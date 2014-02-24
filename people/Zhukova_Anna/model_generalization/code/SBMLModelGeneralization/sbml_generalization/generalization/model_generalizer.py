from collections import defaultdict, Counter
from sbml_generalization.generalization.MaximizingThread import MaximizingThread
from sbml_generalization.generalization.StoichiometryFixingThread import StoichiometryFixingThread
from sbml_generalization.generalization.reaction_filters import get_reactions_by_species, getReactants, getProducts
from sbml_generalization.generalization.vertical_key import get_vertical_key
from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi
from sbml_generalization.utils.logger import log_clusters, log
from sbml_generalization.utils.misc import invert_map
from sbml_generalization.utils.obo_ontology import Term, filter_ontology
from sbml_generalization.generalization.mark_ubiquitous import getUbiquitousSpeciesSet


__author__ = 'anna'

EQUIVALENT_TERM_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of', 'is_tautomer_of'}

def get_r_compartments(model, r):
	s_ids = getReactants(r) | getProducts(r)
	return tuple({model.getSpecies(s_id).getCompartment() for s_id in s_ids})


def get_reaction_ids_to_factor(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
	vk2r = defaultdict(set)
	for r in model.getListOfReactions():
		vk2r[(get_vertical_key(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids), get_r_compartments(model, r))].add(r.getId())
	return vk2r


def generalize_reactions(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
	r_id2clu, i = {}, 0
	for r_ids in get_reaction_ids_to_factor(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids).itervalues():
		for r_id in r_ids:
			r_id2clu[r_id] = i
		i += 1
	return r_id2clu


def maximize(model, term_id2clu, species_id2term_id, ubiquitous_chebi_ids):
	clu2term_ids = invert_map(term_id2clu)
	term_id2s_ids = defaultdict(set)
	s_id2clu = {}
	for s_id, t_id in species_id2term_id.iteritems():
		c_id = model.getSpecies(s_id).getCompartment()
		term_id2s_ids[t_id, c_id].add(s_id)
		if (t_id, c_id) in term_id2clu:
			s_id2clu[s_id] = term_id2clu[t_id, c_id]

	r_id2clu = generalize_reactions(model, s_id2clu, species_id2term_id, ubiquitous_chebi_ids)

	thrds = []
	for (clu, term_ids) in clu2term_ids.iteritems():
		if len(term_ids) <= 1:
			continue

		thread = MaximizingThread(model, term_ids, term_id2s_ids, species_id2term_id, clu, term_id2clu, s_id2clu,
	             ubiquitous_chebi_ids, r_id2clu)
		thrds.append(thread)
		thread.start() # This actually causes the thread to run
	for th in thrds:
		th.join()  # This waits until the thread has completed
	return term_id2clu


def compute_eq0(interesting_term_ids, comp_ids, onto):
	term_id2clu = {}
	i = 0
	roots = set()
	for t in interesting_term_ids:
		term = onto.getTerm(t)
		# then it's a fake term
		if not term:
			continue
		roots |= onto.getAnyParentsOfLevel(term, set(), None, 3)
	psi = [tuple(t.getId() for t in onto.get_sub_tree(root)) for root in roots]
	for t_set in greedy(interesting_term_ids, psi, {it: 1 for it in psi}):
		for c_id in comp_ids:
			clu = (c_id, i)
			term_id2clu.update({(t_id, c_id): clu for t_id in t_set})
		i += 1
	return term_id2clu


def fix_stoichiometry(model, term_id2clu, species_id2term_id, onto):
	clu2term_ids = invert_map(term_id2clu)
	thrds = []
	for clu, term_ids in clu2term_ids.iteritems():
		if len(term_ids) <= 1:
			continue
		thread = StoichiometryFixingThread(model, term_ids, species_id2term_id, onto, clu, term_id2clu)
		thrds.append(thread)
		thread.start() # This actually causes the thread to run
	for th in thrds:
		th.join()  # This waits until the thread has completed
	return term_id2clu


def greedy(terms, psi, set2score):
	terms = set(terms)
	while terms and psi:
		s = max(psi, key=lambda candidate_terms: (len(set(candidate_terms) & terms), set2score[candidate_terms]))
		result = set(s)
		#yield result
		yield result & terms
		terms -= result
		psi.remove(s)


def update(term_id2clu, onto):
	clu2term_ids = invert_map(term_id2clu)
	used = set()
	i = 0
	for clu, term_ids in clu2term_ids.iteritems():
		c_id = list(term_ids)[0][1]
		terms = {onto.getTerm(t) for (t, _) in term_ids}
		common_ancestors = {(t, c_id) for t in onto.commonPts(terms)}
		options = common_ancestors - used
		if options:
			common_ancestor_term = options.pop()[0]
		else:
			name = common_ancestors.pop()[0].getName() + " (another)" if common_ancestors else ' or '.join(
				[t.getName() for t in terms])
			common_ancestor_term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
			onto.addTerm(common_ancestor_term)
			i += 1
		used.add((common_ancestor_term, c_id,))
		for t in term_ids:
			term_id2clu[t] = (c_id, common_ancestor_term.getId())
	return term_id2clu


def filter_clu_to_terms(term2clu):
	clu2term = invert_map(term2clu)
	for clu, terms in clu2term.iteritems():
		if len(terms) <= 1:
			del term2clu[terms.pop()]


def fix_incompatibilities(model, onto, species_id2chebi_id, ubiquitous_chebi_ids, verbose):
	interesting_term_ids = set(species_id2chebi_id.itervalues()) - ubiquitous_chebi_ids
	log(verbose, "  computing eq 0...")
	term_id2clu = compute_eq0(interesting_term_ids, {c.getId() for c in model.getListOfCompartments()}, onto)
	log_clusters(term_id2clu, onto, verbose, True)
	log(verbose, "  maximizing...")
	term_id2clu = maximize(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	filter_clu_to_terms(term_id2clu)
	log_clusters(term_id2clu, onto, verbose, True)
	log(verbose, "  preserving stoichiometry...")
	term_id2clu = fix_stoichiometry(model, term_id2clu, species_id2chebi_id, onto)
	filter_clu_to_terms(term_id2clu)
	log_clusters(term_id2clu, onto, verbose, True)
	log(verbose, "  maximizing...")
	term_id2clu = maximize(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	filter_clu_to_terms(term_id2clu)
	log_clusters(term_id2clu, onto, verbose, True)
	return term_id2clu


def generalize_species(model, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose=False):
	term_id2clu = fix_incompatibilities(model, onto, species_id2chebi_id, ubiquitous_chebi_ids, verbose)
	if not term_id2clu:
		return {}
	term_id2clu = update(term_id2clu, onto)
	# log_clusters(term_id2clu, onto, verbose)
	s_id2clu = {}
	t_c_id2species = defaultdict(set)
	for (s_id, t) in species_id2chebi_id.iteritems():
		c_id = model.getSpecies(s_id).getCompartment()
		if (t, c_id) in term_id2clu:
			s_id2clu[s_id] = (c_id, onto.getTerm(term_id2clu[t, c_id][1]))
		else:
			t_c_id2species[(t, c_id)].add(s_id)
	# If there were several species in the same compartment
	# with the same ChEBI id, let's cluster them, too.
	for ((t, c_id), s_set) in t_c_id2species.iteritems():
		if len(s_set) > 1:
			term = onto.getTerm(t)
			for s_id in s_set:
				s_id2clu[s_id] = (c_id, term)
	log(verbose, "  generalizing by simplified key...")
	vks = get_reaction_ids_to_factor(model, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	simplified_key_generalization(model, s_id2clu, ubiquitous_chebi_ids, vks, onto)
	log_clusters(s_id2clu, onto, verbose, True)

	return s_id2clu


def sort_by_compartment(input_model, r_sps):
	comp2r_sps = defaultdict(list)
	for it in r_sps:
		if isinstance(it, tuple):
			c_id, term = it
			comp2r_sps[c_id].append(term)
		else:
			comp2r_sps[input_model.getSpecies(it).getCompartment()].append(it)
	return comp2r_sps


def update_clusters(comp2r_sps, i, reactions, s_id2clu, onto):
	for c_id, sps in comp2r_sps.iteritems():
		if len(sps) > 1:
			res = no_conflicts(sps, reactions, c_id, s_id2clu, onto)
			if res:
				term, sps = res
				if not term:
					term = (None, i)
					i += 1
				for s_id in sps:
					s_id2clu[s_id] = c_id, term


def no_conflicts(elements, reactions, c_id, s_id2clu, onto):
	clus = set(s_id2clu.values())
	term = None
	rs = set()
	sps = []
	for it in elements:
		if isinstance(it, Term):
			if term and term != it:
				cmmn_pts = {(c_id, tt) for tt in onto.commonPts({term, it}, 2)} - clus
				if cmmn_pts:
					term = cmmn_pts.pop()[1]
				else:
					return None
			else:
				term = it
			for s_id in (s_id for (s_id, clu) in s_id2clu.iteritems() if clu == (c_id, term)):
				its_rs = set(get_reactions_by_species(s_id, reactions))
				if rs & its_rs:
					return None
				rs |= its_rs
				sps.append(s_id)
		else:
			its_rs = set(get_reactions_by_species(it, reactions))
			if rs & its_rs:
				return None
			rs |= its_rs
			sps.append(it)
	return term, sps


def simplified_key_generalization(input_model, s_id2clu, ub_sps, vks, onto):
	sk2vks = defaultdict(set)
	for ((ub_rs, ub_ps, rs, ps), comps) in vks.keys():
		if ub_rs or ub_ps:
			simple_key = ((ub_rs, ub_ps, len(rs), len(ps)), comps)
			sk2vks[simple_key].add(((ub_rs, ub_ps, rs, ps), comps))
	reactions = list(input_model.getListOfReactions())
	i = 0
	for ((ub_rs, ub_ps, _, _), _), vks in sk2vks.iteritems():
		if len(vks) > 1 and (ub_ps or ub_rs):
			r_counter, p_counter = Counter(), Counter()
			for ((_, _, rs, ps), _) in vks:
				r_counter.update(rs)
				p_counter.update(ps)
			r_max, p_max = r_counter.most_common(1), p_counter.most_common(1)
			r_max, p_max = r_max[0] if r_max else None, p_max[0] if p_max else None
			rp_max = max(r_max[1] if r_max else 0, p_max[1] if p_max else 0)
			if rp_max > 1:
				if r_max and rp_max == r_max[1]:
					to_merge = [vk for vk in vks if r_max[0] in vk[0][2]]
				else:
					to_merge = [vk for vk in vks if p_max[0] in vk[0][3]]
				r_sps, p_sps = set(), set()
				common_rs = set(to_merge[0][0][2]) & set(to_merge[1][0][2])
				common_ps = set(to_merge[0][0][3]) & set(to_merge[1][0][3])
				# if there are less that 2 common elements, it's not enough evidence
				if len(ub_rs) + len(ub_sps) + len(common_rs) & len(common_ps) < 2:
					continue
				stop = False
				for vk in to_merge:
					r_s, p_s = set(vk[0][2]) - common_rs, set(vk[0][3]) - common_ps
					if len(r_s) > 1 or len(p_s) > 1:
						stop = True
						break
					r_sps |= r_s
					p_sps |= p_s
				if not stop:
					comp2r_sps = sort_by_compartment(input_model, r_sps)
					update_clusters(comp2r_sps, i, reactions, s_id2clu, onto)
					comp2p_sps = sort_by_compartment(input_model, p_sps)
					update_clusters(comp2p_sps, i, reactions, s_id2clu, onto)


# def simplified_need_to_reverse(r, ubiquitous_ids):
# 	if not r.getReversible():
# 		return False
# 	return getReactants(r) & ubiquitous_ids > getProducts(r) & ubiquitous_ids
#
#
# def get_simplified_key(r, ubiquitous_ids):
# 	get_vertical_key(r, s_id2clu, s_id2term_id)
# 	reactants, products = getReactants(r), getProducts(r)
# 	ubiquitous_reactants, ubiquitous_products = reactants & ubiquitous_ids, products & ubiquitous_ids
# 	srs_len, sps_len = len(reactants - ubiquitous_reactants), len(products - ubiquitous_products)
# 	if r.getReversible() and simplified_need_to_reverse(r, ubiquitous_ids):
# 		return ubiquitous_products, ubiquitous_reactants, sps_len, srs_len
# 	return ubiquitous_reactants, ubiquitous_products, srs_len, sps_len,


# def shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose=False):
# 	ubiquitous_ids = {s_id for s_id in species_id2chebi_id.iterkeys() if
# 	                  species_id2chebi_id[s_id] in ubiquitous_chebi_ids}
#
# 	def get_in_out_reactions(s_id):
# 		ins, outs = get_p_reactions_by_species(s_id, reactions), get_r_reactions_by_species(s_id, reactions)
# 		r_ins = [r for r in ins if not simplified_need_to_reverse(r, ubiquitous_ids)] \
# 		        + [r for r in outs if simplified_need_to_reverse(r, ubiquitous_ids)]
# 		r_outs = [r for r in ins if not r in r_ins] + [r for r in outs if not r in r_ins]
# 		return r_ins, r_outs
#
# 	def get_aligned_reactants_products(r):
# 		rs, ps = getReactants(r, True), getProducts(r, True)
# 		if simplified_need_to_reverse(r, ubiquitous_ids):
# 			return ps, rs
# 		return rs, ps
#
# 	def check(s_id, already_checked):
# 		if s_id in already_checked:
# 			return [], None, []
#
# 		rs = get_reactions_by_species(s_id, reactions)
# 		if len(rs) != 2:
# 			return [s_id], None, []
# 		ins, outs = get_in_out_reactions(s_id)
# 		if 1 == len(ins) == len(outs):
# 			r_in, r_out = ins[0], outs[0]
# 			in_k, out_k = get_simplified_key(r_in, ubiquitous_ids), get_simplified_key(r_out, ubiquitous_ids)
# 			# same simplified keys that include at least one ubiquitous species
# 			if in_k == out_k and (in_k[0] or in_k[1]):
# 				already_checked.add(s_id)
# 				in_rs, in_ps = get_aligned_reactants_products(r_in)
# 				out_rs, out_ps = get_aligned_reactants_products(r_out)
#
# 				left_s_ids = in_rs - out_rs
# 				if len(left_s_ids) != 1:
# 					return [s_id], (in_k, r_in.getName()), []
# 				left_id = left_s_ids.pop()
#
# 				right_s_ids = out_ps - in_ps
# 				if len(right_s_ids) != 1:
# 					return [s_id], (in_k, r_in.getName()), []
# 				right_id = right_s_ids.pop()
# 				left_ts, l_key, left_rs = check(left_id, already_checked)
# 				if not r_in.getId() in left_rs:
# 					left_rs += [r_in.getId()]
# 				right_ts, r_key, right_rs = check(right_id, already_checked)
# 				if not r_out.getId() in right_rs:
# 					right_rs = [r_out.getId()] + right_rs
# 				return left_ts + [s_id] + right_ts, (in_k, r_in.getName()), left_rs + right_rs
# 		return [s_id], None, []
#
# 	result = []
# 	checked = set()
# 	specific_ids = (s_id for s_id in species_id2chebi_id.iterkeys() if \
# 	                not species_id2chebi_id[s_id] in ubiquitous_chebi_ids)
# 	for s_id in specific_ids:
# 		lst = check(s_id, checked)
# 		if len(lst[0]) > 1 and onto.commonPts((onto.getTerm(species_id2chebi_id[s_id]) for s_id in lst[0])):
# 			result.append(lst)
#
# 	log_chains(result, verbose)
#
# 	return result


def map2chebi(cofactors, input_model, onto):
	# species_id2chebi_id, fake_terms = get_species_to_chebi(input_model, onto)
	species_id2chebi_id = get_species_to_chebi(input_model, onto)
	terms = (onto.getTerm(t_id) for t_id in species_id2chebi_id.itervalues()) # if not onto.getTerm(t_id) in fake_terms)
	filter_ontology(onto, terms, relationships=EQUIVALENT_TERM_RELATIONSHIPS, min_deepness=11)
	cofactor_ids = {cofactor_id for cofactor_id in cofactors if onto.getTerm(cofactor_id)}
	ubiquitous_chebi_ids = cofactor_ids | getUbiquitousSpeciesSet(input_model, species_id2chebi_id, onto)
	return species_id2chebi_id, ubiquitous_chebi_ids
