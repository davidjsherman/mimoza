from collections import defaultdict, Counter
from sbml_generalization.generalization.MaximizingThread import MaximizingThread
from sbml_generalization.generalization.StoichiometryFixingThread import StoichiometryFixingThread
from sbml_generalization.generalization.reaction_filters import get_reactions_by_species
from sbml_generalization.generalization.vertical_key import get_vertical_key
from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi
from sbml_generalization.utils.logger import log_clusters, log
from sbml_generalization.utils.misc import invert_map
from sbml_generalization.utils.obo_ontology import Term, filter_ontology
from sbml_generalization.generalization.mark_ubiquitous import getUbiquitousSpeciesSet


__author__ = 'anna'

EQUIVALENT_TERM_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of', 'is_tautomer_of'}


def get_reaction_ids_to_factor(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
	vk2r = defaultdict(set)
	for r in model.getListOfReactions():
		vk2r[get_vertical_key(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids)].add(r.getId())
	return vk2r


# def aligned_to_v_key(r, term_id2clu, s_id2term_id, ubiquitous_chebi_ids):
# 	if not r.getReversible():
# 		return True
# 	return not need_to_reverse(get_key_elements(r, term_id2clu, s_id2term_id, ubiquitous_chebi_ids))


def generalize_reactions(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
	r_id2clu, i = {}, 0
	for r_ids in get_reaction_ids_to_factor(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids).itervalues():
		for r_id in r_ids:
			r_id2clu[r_id] = i
		i += 1
	return r_id2clu


# def merge_based_on_neighbours(lst):
# 	new_lst = []
# 	for neighbours, terms in lst:
# 		neighbours = set(neighbours)
# 		to_remove = []
# 		for (new_neighbours, new_terms) in new_lst:
# 			if neighbours & new_neighbours:
# 				neighbours |= new_neighbours
# 				terms |= new_terms
# 				to_remove.append((new_neighbours, new_terms))
# 		new_lst = [it for it in new_lst if not it in to_remove] + [(neighbours, terms)]
# 	return new_lst


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
		#print [onto.getTerm(it).getName() for it in term_ids]
		if len(term_ids) <= 1:
			continue
		# neighbours2term_ids = {}
		# neighbourless_terms = set()
		# for t_id in term_ids:
		# 	neighbours = {
		# 		("in" if t_id in get_vertical_key(r, s_id2clu, species_id2term_id, ubiquitous_chebi_ids)[3] else "out",
		# 		 r_id2clu[r.getId()]) for r
		# 		in get_reactions_by_term(t_id, model, term_id2s_ids)}
		# 	if neighbours:
		# 		key = tuple(neighbours)
		# 		add_to_map(neighbours2term_ids, key, t_id)
		# 	else:
		# 		neighbourless_terms.add(t_id)
		# 	#print onto.getTerm(t_id).getName(), neighbours
		# new_lst = merge_based_on_neighbours(neighbours2term_ids.iteritems())
		# i = 0
		# if len(new_lst) > 1:
		# 	for neighbours, term_ids in new_lst:
		# 		n_clu = clu + (i,)
		# 		i += 1
		# 		for t in term_ids:
		# 			term_id2clu[t] = n_clu
		# for t in neighbourless_terms:
		# 	term_id2clu[t] = clu + (i,)
		# 	i += 1

		thread = MaximizingThread(model, term_ids, term_id2s_ids, species_id2term_id, clu, term_id2clu, s_id2clu,
	             ubiquitous_chebi_ids, r_id2clu)
		thrds.append(thread)
		thread.start() # This actually causes the thread to run
	for th in thrds:
		th.join()  # This waits until the thread has completed
	return term_id2clu


def compute_eq0(interesting_term_ids, comp_ids, onto):
	#clu = (0,)
	term_id2clu = {}
	i = 0
	# psi = [tuple(t.getId() for t in onto.get_sub_tree(root)) for root in onto.getRoots()]
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


# def get_conflicts(model, term_ids, species_id2term_id):
# 	term_id2s_ids = defaultdict(set)
# 	for s_id, t_id in species_id2term_id.iteritems():
# 		c_id = model.getSpecies(s_id).getCompartment()
# 		if (t_id, c_id) in term_ids:
# 			term_id2s_ids[t_id, c_id].add(s_id)
# 	r2term_ids = defaultdict(set)
# 	for t_id in term_ids:
# 		for r in get_reactions_by_term(t_id, model, term_id2s_ids):
# 			r2term_ids[r.getId()].add(t_id)
# 	return [{t_id for (t_id, _) in terms} for terms in r2term_ids.itervalues() if len(terms) > 1]




def fix_stoichiometry(model, term_id2clu, species_id2term_id, onto):
	clu2term_ids = invert_map(term_id2clu)
	thrds = []
	for clu, term_ids in clu2term_ids.iteritems():
		if len(term_ids) <= 1:
			continue
		# conflicts = get_conflicts(model, term_ids, species_id2term_id)
		# if not conflicts:
		# 	continue
		# #print [[onto.getTerm(it).getName() for it in trms] for trms in conflicts]
		# term_ids = {t_id for (t_id, _) in term_ids}
		# psi, set2score = get_psi_set(onto, term_ids, conflicts)
		# i = 0
		# for ts in greedy(term_ids, psi, set2score):
		# 	i += 1
		# 	n_clu = clu + (i,)
		# 	for t in ts:
		# 		# clu[0] is a compartment_id
		# 		term_id2clu[(t, clu[0])] = n_clu
		thread = StoichiometryFixingThread(model, term_ids, species_id2term_id, onto, clu, term_id2clu)
		thrds.append(thread)
		thread.start() # This actually causes the thread to run
	for th in thrds:
		th.join()  # This waits until the thread has completed
		# At this point, the thread has completed
		# term_id2clu.update(th.term_id2clu)
	return term_id2clu


# def get_psi_set(onto, term_ids, conflicts):
# 	def good(t_set):
# 		if not t_set:
# 			return False
# 		if len(t_set) == 1:
# 			return True
# 		for c_ts in conflicts:
# 			if len(t_set & c_ts) > 1:
# 				return False
# 		return True
#
# 	def get_conflict_num(t_set):
# 		if not t_set or len(t_set) == 1:
# 			return 0
# 		res = 0
# 		for c_ts in conflicts:
# 			res += len(t_set & c_ts) / 2
# 		return res
#
# 	get_covered_term_ids = lambda term: {sub_t.getId() for sub_t in onto.get_sub_tree(term) if
# 	                                     sub_t.getId() in term_ids}
#
# 	# the least common ancestors, or roots if there are none
# 	common_ancestor_terms = onto.commonPts({onto.getTerm(t) for t in term_ids}, 3)
# 	if not common_ancestor_terms:
# 		common_ancestor_terms = set()
# 		for t in term_ids:
# 			term = onto.getTerm(t)
# 			# then it's a fake term
# 			if not term:
# 				continue
# 			common_ancestor_terms |= onto.getAnyParentsOfLevel(term, set(), None, 3)
#
# 	psi, basics, set2score = set(), [], {}
#
# 	def process(element, score):
# 		el = tuple(element)
# 		if el in psi:
# 			return False
# 		if get_conflict_num(element) > 40:
# 			return True
# 		basics.append(element)
# 		psi.add(el)
# 		set2score[el] = score
# 		return True
#
# 	# sets defined by the least common ancestors
# 	# print "ANCESTORS: ", [t.getName() for t in common_ancestor_terms]
# 	processed = set()
# 	for T in common_ancestor_terms:
# 		T_element = get_covered_term_ids(T)
# 		T_level = onto.getLevel(T)
# 		T_l = sum(T_level) / len(T_level)
# 		process(T_element, (3, T_l))
# 		for t in onto.getAnyChildren(T, False, set()):
# 			if t in processed:
# 				continue
# 			processed.add(t)
#
# 			element = get_covered_term_ids(t)
# 			if not element:
# 				continue
# 			level = onto.getLevel(t)
# 			if process(element, (3, sum(level) / len(level))):
# 				# complement set
# 				complement = T_element - element
# 				if complement:
# 					process(complement, (2, T_l))
#
# 	def avg_tup(s0, s1):
# 		i0, j0 = set2score[tuple(s0)]
# 		i1, j1 = set2score[tuple(s1)]
# 		return min(i0, i1) - 1, min(j0, j1)
#
# 	# the differences between sets already in Psi
# 	for _ in xrange(2):
# 		to_add = []
# 		i = 0
# 		for basic in basics:
# 			i += 1
# 			for element in basics[i:]:
# 				for complement_set in (basic - element, element - basic):
# 					if len(complement_set) > 0:
# 						c_element = tuple(complement_set)
# 						if c_element in psi:
# 							continue
# 						psi.add(c_element)
# 						to_add.append(complement_set)
# 						set2score[c_element] = avg_tup(element, basic)
# 		basics += to_add
#
# 	result = [term_set for term_set in psi if good(set(term_set))]
# 	return result, set2score


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
	simplified_key_generalization(model, s_id2clu, ubiquitous_chebi_ids, vks)
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


def update_clusters(comp2r_sps, i, reactions, s_id2clu):
	for c_id, sps in comp2r_sps.iteritems():
		if len(sps) > 1:
			res = no_conflicts(sps, reactions, c_id, s_id2clu)
			if res:
				term, sps = res
				if not term:
					term = (None, i)
					i += 1
				for s_id in sps:
					s_id2clu[s_id] = c_id, term


def no_conflicts(elements, reactions, c_id, s_id2clu):
	term = None
	rs = set()
	sps = []
	for it in elements:
		if isinstance(it, Term):
			if term and term != it:
				return None
			term = it
			for s_id in (s_id for (s_id, clu) in s_id2clu.iteritems() if clu == (c_id, term)):
				its_rs = set(get_reactions_by_species(s_id, reactions))
				if rs & its_rs:
					return None
				rs |= its_rs
		else:
			its_rs = set(get_reactions_by_species(it, reactions))
			if rs & its_rs:
				return None
			rs |= its_rs
			sps.append(it)
	return term, sps


def simplified_key_generalization(input_model, s_id2clu, ub_sps, vks):
	sk2vks = defaultdict(set)
	for (ub_rs, ub_ps, rs, ps) in vks.keys():
		if ub_rs or ub_ps:
			simple_key = (ub_rs, ub_ps, len(rs), len(ps))
			sk2vks[simple_key].add((ub_rs, ub_ps, rs, ps))
	reactions = list(input_model.getListOfReactions())
	i = 0
	for (ub_rs, ub_ps, _, _), vks in sk2vks.iteritems():
		if len(vks) > 1 and (ub_ps or ub_rs):
			r_counter, p_counter = Counter(), Counter()
			for (_, _, rs, ps) in vks:
				r_counter.update(rs)
				p_counter.update(ps)
			r_max, p_max = r_counter.most_common(1), p_counter.most_common(1)
			r_max, p_max = r_max[0] if r_max else None, p_max[0] if p_max else None
			rp_max = max(r_max[1] if r_max else 0, p_max[1] if p_max else 0)
			if rp_max > 1:
				if r_max and rp_max == r_max[1]:
					to_merge = [vk for vk in vks if r_max[0] in vk[2]]
				else:
					to_merge = [vk for vk in vks if p_max[0] in vk[3]]
				r_sps, p_sps = set(), set()
				common_rs = set(to_merge[0][2]) & set(to_merge[1][2])
				common_ps = set(to_merge[0][3]) & set(to_merge[1][3])
				# if there are less that 2 common elements, it's not enough evidence
				if len(ub_rs) + len(ub_sps) + len(common_rs) & len(common_ps) < 2:
					continue
				stop = False
				for vk in to_merge:
					r_s, p_s = set(vk[2]) - common_rs, set(vk[3]) - common_ps
					if len(r_s) > 1 or len(p_s) > 1:
						stop = True
						break
					r_sps |= r_s
					p_sps |= p_s
				if not stop:
					comp2r_sps = sort_by_compartment(input_model, r_sps)
					update_clusters(comp2r_sps, i, reactions, s_id2clu)
					comp2p_sps = sort_by_compartment(input_model, p_sps)
					update_clusters(comp2p_sps, i, reactions, s_id2clu)


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
