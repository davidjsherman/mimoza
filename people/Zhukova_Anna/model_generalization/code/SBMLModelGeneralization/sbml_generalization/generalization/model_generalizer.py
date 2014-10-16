from collections import defaultdict, Counter
from math import sqrt
from sbml_generalization.generalization.MaximizingThread import MaximizingThread
from sbml_generalization.generalization.StoichiometryFixingThread import StoichiometryFixingThread
from sbml_generalization.generalization.reaction_filters import get_reactions_by_species, get_reactants, get_products, \
	get_reactions_by_term
from sbml_generalization.generalization.vertical_key import get_vertical_key, is_reactant
from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi
from sbml_generalization.utils.logger import log_clusters, log
from sbml_generalization.utils.misc import invert_map
from sbml_generalization.utils.obo_ontology import Term, filter_ontology
from sbml_generalization.generalization.mark_ubiquitous import get_ubiquitous_species_set


__author__ = 'anna'

EQUIVALENT_TERM_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of', 'is_tautomer_of'}


def get_r_compartments(model, r):
	s_ids = get_reactants(r) | get_products(r)
	return tuple({model.getSpecies(s_id).getCompartment() for s_id in s_ids})


def get_reaction_ids_to_factor(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
	vk2r = defaultdict(set)
	for r in model.getListOfReactions():
		vk2r[(get_vertical_key(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids), get_r_compartments(model, r))].add(
			r.getId())
	return vk2r


def generalize_reactions(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
	r_id2clu, i = {}, 0
	for r_ids in get_reaction_ids_to_factor(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids).itervalues():
		for r_id in r_ids:
			r_id2clu[r_id] = i
		i += 1
	return r_id2clu


def compute_s_id2clu(model, species_id2term_id, term_id2clu):
	s_id2clu = {}
	term_id2s_ids = defaultdict(set)
	for s_id, t_id in species_id2term_id.iteritems():
		term_id2s_ids[t_id].add(s_id)
		if t_id in term_id2clu:
			s_id2clu[s_id] = (term_id2clu[t_id], model.getSpecies(s_id).getCompartment())
	return s_id2clu, term_id2s_ids


def maximize(model, term_id2clu, species_id2term_id, ubiquitous_chebi_ids):
	clu2term_ids = invert_map(term_id2clu)
	s_id2clu, term_id2s_ids = compute_s_id2clu(model, species_id2term_id, term_id2clu)

	r_id2clu = generalize_reactions(model, s_id2clu, species_id2term_id, ubiquitous_chebi_ids)

	thrds = []
	for (clu, term_ids) in clu2term_ids.iteritems():
		if len(term_ids) <= 1:
			continue

		thread = MaximizingThread(model, term_ids, term_id2s_ids, species_id2term_id, clu, term_id2clu,
		                          s_id2clu,
		                          ubiquitous_chebi_ids, r_id2clu)
		thrds.append(thread)
		thread.start()  # This actually causes the thread to run
	for th in thrds:
		th.join()  # This waits until the thread has completed
	return term_id2clu


def update_binary_vectors(model, term_id2clu, species_id2term_id, ubiquitous_chebi_ids):
	clu2term_ids = invert_map(term_id2clu)
	s_id2clu, term_id2s_ids = compute_s_id2clu(model, species_id2term_id, term_id2clu)

	r_id2clu = generalize_reactions(model, s_id2clu, species_id2term_id, ubiquitous_chebi_ids)
	rs = [r for r in model.getListOfReactions() if r.getNumReactants() > 1 or r.getNumProducts() > 1]

	for clu, t_ids in clu2term_ids.iteritems():
		# print "\n--------------------------"
		r2t_ids = defaultdict(set)
		for t_id in t_ids:
			for r in get_reactions_by_term(t_id, rs, term_id2s_ids):
				r2t_ids[r.getId()].add(t_id)

		t_id2r_clus = {}
		all_clus = set()
		for t_id in t_ids:
			clus = {(r_id2clu[r.getId()],
			         "in" if is_reactant(t_id, r, s_id2clu, species_id2term_id, ubiquitous_chebi_ids) else "out")
			        for r in get_reactions_by_term(t_id, rs, term_id2s_ids)}
			t_id2r_clus[t_id] = clus
			all_clus |= {clu[0] for clu in clus}
		clu2index = dict(zip(all_clus, xrange(0, len(all_clus))))
		vector2t_ids = defaultdict(list)
		for t_id in t_id2r_clus.iterkeys():
			cls = []
			for r_clu in t_id2r_clus[t_id]:
				cls.append((clu2index[r_clu[0]], r_clu[1]))
			vector = tuple(
				[1 if (it, "in") in cls else (-1 if (it, "out") in cls else 0) for it in xrange(0, len(all_clus))])
			vector2t_ids[vector].append(t_id)

		vectors = vector2t_ids.keys()
		conflicts = [i for i in xrange(0, len(all_clus)) if
		             next((t for t in vectors if 1 == t[i]), None) and next((t for t in vectors if -1 == t[i]), None)]
		if not conflicts:
			continue

		# for vector, t_s in vector2t_ids.iteritems():
		# 	print vector, [[model.getSpecies(s_id).getName() for s_id in term_id2s_ids[t_id]] for t_id in t_s]

		in_conflict = lambda v1, v2: next((True for j in conflicts if v1[j] * v2[j] == -1), False)
		median_vector = lambda vector_list: [median(vector_list, j, vector2t_ids) for j in xrange(0, len(all_clus))]
		i = max(conflicts, key=lambda i: len([t for t in vectors if 0 != t[i]]))
		current_vectors = []
		for vector in sorted((vector for vector in vectors if vector[i] != 0),
		                     key=lambda vector: -len(vector2t_ids[vector])):
			good_vectors = sorted(
				((c_vectors, tot) for (c_vectors, tot) in current_vectors if not in_conflict(vector, tot)),
				key=lambda (c_vectors, tot): distance(vector, median_vector(c_vectors)))
			if good_vectors:
				c_vectors, tot = good_vectors[0]
				c_vectors.append(vector)
				for j in xrange(0, len(all_clus)):
					if vector[j] != 0:
						tot[j] = vector[j]
			else:
				current_vectors.append(([vector], list(vector)))

		# print "CV: ", current_vectors

		neutral_vectors = [vector for vector in vectors if vector[i] == 0]
		# print "NV: ", neutral_vectors

		intersect = lambda v1, v2: next((True for j in xrange(0, len(all_clus)) if v1[j] == v2[j] != 0), False)
		compatible_clusters = lambda vector, vectors: [(vs, tot) for (vs, tot) in vectors if
		                                               not in_conflict(vector, tot) and intersect(vector, tot)]

		while neutral_vectors:
			bad_vectors = [vector for vector in neutral_vectors if
			               not next(((c_vectors, tot) for (c_vectors, tot) in current_vectors if
			                         not in_conflict(vector, tot)), None)]
			if not bad_vectors:
				vector = min(neutral_vectors, key=lambda vector: min(distance(vector, median_vector(c_vectors))
				                                                     for (c_vectors, tot) in current_vectors if
				                                                     not in_conflict(vector, tot)))

				# print "? ", vector, [[model.getSpecies(s_id).getName() for s_id in term_id2s_ids[t_id]] for t_id in
				#                      vector2t_ids[vector]]

				comp_clus = compatible_clusters(vector, current_vectors)
				if comp_clus:
					c_vectors, tot = max(((c_vs, tot) for (c_vs, tot) in comp_clus), key=lambda (c_vs, tot):
						sum((1 if vector[j] == tot[j] != 0 else 0 for j in xrange(0, len(all_clus)))))
					# print "attached to ", c_vectors
					c_vectors.append(vector)
					for j in xrange(0, len(all_clus)):
						if vector[j] != 0:
							tot[j] = vector[j]
				else:
					# print "new"
					current_vectors.append(([vector], list(vector)))
			else:
				vector = max(bad_vectors, key=lambda vector: len(vector2t_ids[vector]))
				current_vectors.append(([vector], list(vector)))
				# print "bad ", vector, [[model.getSpecies(s_id).getName() for s_id in term_id2s_ids[t_id]] for t_id in
				#                        vector2t_ids[vector]]
			neutral_vectors.remove(vector)

		i = 0
		for (c_vectors, _) in current_vectors:
			n_clu = clu + (i,)
			i += 1
			for vector in c_vectors:
				for t in vector2t_ids[vector]:
					term_id2clu[t] = n_clu


def median(arrays, j, array2num):
	total, length = 0, 0
	for array in arrays:
		l = len(array2num[array])
		total += array[j] * l
		length += l

	return int(round(float(total) / length))


def distance(a, b):
	return sqrt(sum(pow(a[i] - b[i], 2) for i in xrange(0, len(a))))


def compute_eq0(interesting_term_ids, onto):
	term_id2clu = {}
	roots = set()
	for t in interesting_term_ids:
		term = onto.get_term(t)
		# then it's a fake term
		if not term:
			continue
		roots |= onto.get_generalized_ancestors_of_level(term, set(), None, 3)
	psi = [tuple(t.get_id() for t in onto.get_sub_tree(root)) for root in roots]
	i = 0
	for t_set in greedy(interesting_term_ids, psi, {it: 1 for it in psi}):
		term_id2clu.update({t_id: (i, ) for t_id in t_set})
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
		thread.start()  # This actually causes the thread to run
	for th in thrds:
		th.join()  # This waits until the thread has completed
	return term_id2clu


def greedy(terms, psi, set2score):
	terms = set(terms)
	while terms and psi:
		s = max(psi, key=lambda candidate_terms: (len(set(candidate_terms) & terms), set2score[candidate_terms]))
		result = set(s)
		# yield result
		yield result & terms
		terms -= result
		psi.remove(s)


def update(term_id2clu, onto):
	clu2term_ids = invert_map(term_id2clu)
	used = set()
	i = 0
	for clu, term_ids in clu2term_ids.iteritems():
		terms = {onto.get_term(t) for t in term_ids}
		common_ancestors = {t for t in onto.common_points(terms)}
		options = common_ancestors - used
		if options:
			common_ancestor_term = options.pop()
		else:
			name = common_ancestors.pop().get_name() + " (another)" if common_ancestors else ' or '.join(
				[t.get_name() for t in terms])
			common_ancestor_term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
			onto.add_term(common_ancestor_term)
			i += 1
		used.add(common_ancestor_term)
		for t in term_ids:
			term_id2clu[t] = common_ancestor_term.get_id()
	return term_id2clu


def update_clu(s_id2clu, onto, s_id2term_id, model):
	clu2s_ids = invert_map(s_id2clu)
	used = set()
	i = 0
	for clu, s_ids in clu2s_ids.iteritems():
		c_id = model.getSpecies(list(s_ids)[0]).getCompartment()
		terms = {onto.get_term(s_id2term_id[s_id]) for s_id in s_ids if s_id in s_id2term_id}
		if terms:
			common_ancestors = {(t, c_id) for t in onto.common_points(terms)}
			options = common_ancestors - used
			if options:
				common_ancestor_term = options.pop()[0]
			else:
				name = common_ancestors.pop()[0].get_name() + " (another)" if common_ancestors else ' or '.join(
					[t.get_name() for t in terms])
				common_ancestor_term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
				onto.add_term(common_ancestor_term)
				i += 1
		else:
			name = ' or '.join([model.getSpecies(s_id).getName() for s_id in s_ids])
			common_ancestor_term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
			onto.add_term(common_ancestor_term)
			i += 1
		used.add((common_ancestor_term, c_id,))
		for s_id in s_ids:
			s_id2clu[s_id] = (c_id, common_ancestor_term)
	return s_id2clu


def filter_clu_to_terms(term2clu):
	clu2term = invert_map(term2clu)
	for clu, terms in clu2term.iteritems():
		if len(terms) <= 1:
			del term2clu[terms.pop()]


def fix_incompatibilities(model, onto, species_id2chebi_id, ubiquitous_chebi_ids, verbose):
	interesting_term_ids = set(species_id2chebi_id.itervalues()) - ubiquitous_chebi_ids
	log(verbose, "  computing eq 0...")
	term_id2clu = compute_eq0(interesting_term_ids, onto)
	# log_clusters(term_id2clu, onto, verbose, True)
	log(verbose, "  maximizing...")
	term_id2clu = maximize(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	filter_clu_to_terms(term_id2clu)
	# log_clusters(term_id2clu, onto, verbose, True)
	log(verbose, "  preserving stoichiometry...")
	update_binary_vectors(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	term_id2clu = fix_stoichiometry(model, term_id2clu, species_id2chebi_id, onto)
	filter_clu_to_terms(term_id2clu)
	# log_clusters(term_id2clu, onto, verbose, True)
	log(verbose, "  maximizing...")
	term_id2clu = maximize(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	filter_clu_to_terms(term_id2clu)
	# log_clusters(term_id2clu, onto, verbose, True)
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
		if t in term_id2clu:
			s_id2clu[s_id] = (c_id, onto.get_term(term_id2clu[t]))
		else:
			t_c_id2species[(t, c_id)].add(s_id)
	# If there were several species in the same compartment
	# with the same ChEBI id, let's cluster them, too.
	for ((t, c_id), s_set) in t_c_id2species.iteritems():
		if len(s_set) > 1:
			term = onto.get_term(t)
			for s_id in s_set:
				s_id2clu[s_id] = (c_id, term)
	# log(verbose, "  generalizing by simplified key...")
	# vk2r_ids = get_reaction_ids_to_factor(model, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	# simplified_key_generalization(model, s_id2clu, ubiquitous_chebi_ids, vk2r_ids, onto)
	# s_id2clu = update_clu(s_id2clu, onto, species_id2chebi_id, model)
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


def update_clusters(c_id2sps, i, reactions, s_id2clu, onto):
	for c_id, sps in c_id2sps.iteritems():
		if len(sps) > 1:
			res = get_compatible_species(sps, reactions, c_id, s_id2clu, onto)
			if res:
				term, sps = res
				if not term:
					term = (None, i)
					i += 1
				for s_id in sps:
					s_id2clu[s_id] = c_id, term


def get_compatible_species(s_ids, reactions, c_id, s_id2clu, onto):
	term = None
	rs = set()
	sps = []
	for s_id in s_ids:
		if isinstance(s_id, Term):
			if term and term != s_id:
				common_ancestor_terms = {(c_id, tt) for tt in onto.common_points({term, s_id}, 2)}
				if common_ancestor_terms:
					term = common_ancestor_terms.pop()[1]
				else:
					return None
			else:
				term = s_id
			for s_id in (s_id for (s_id, clu) in s_id2clu.iteritems() if clu == (c_id, term)):
				its_rs = set(get_reactions_by_species(s_id, reactions))
				if rs & its_rs:
					return None
				rs |= its_rs
				sps.append(s_id)
		else:
			its_rs = set(get_reactions_by_species(s_id, reactions))
			if rs & its_rs:
				return None
			rs |= its_rs
			sps.append(s_id)
	return term, sps


# TODO: should check if it breaks compatibility after (i.e., stoichiometry)
def simplified_key_generalization(input_model, s_id2clu, ub_sps, keys, onto):
	simple_key2vks = defaultdict(set)
	for ((ub_rs, ub_ps, rs, ps), comps) in keys.keys():
		if ub_rs or ub_ps:
			simple_key = ((ub_rs, ub_ps, len(rs), len(ps)), comps)
			simple_key2vks[simple_key].add(((ub_rs, ub_ps, rs, ps), comps))
	reactions = list(input_model.getListOfReactions())
	i = 0
	for ((ub_rs, ub_ps, _, _), _), vks in simple_key2vks.iteritems():
		if len(vks) > 1:  # and (ub_ps or ub_rs):
			r_counter, p_counter = Counter(), Counter()
			for ((_, _, rs, ps), _) in vks:
				r_counter.update(rs)
				p_counter.update(ps)
			r_max, p_max = r_counter.most_common(1), p_counter.most_common(1)
			r_max, p_max = r_max[0] if r_max else None, p_max[0] if p_max else None
			rp_max_count = max(r_max[1] if r_max else 0, p_max[1] if p_max else 0)
			if rp_max_count > 1:
				if r_max and rp_max_count == r_max[1]:
					to_merge = [vk for vk in vks if r_max[0] in vk[0][2]]
				else:
					to_merge = [vk for vk in vks if p_max[0] in vk[0][3]]
				r_sps, p_sps = set(), set()
				common_rs = set(to_merge[0][0][2]) & set(to_merge[1][0][2])
				common_ps = set(to_merge[0][0][3]) & set(to_merge[1][0][3])
				# if there are less that 1 common elements, it's not enough evidence
				if len(ub_rs) + len(ub_sps) + len(common_rs) & len(common_ps) < 1:
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


def map2chebi(cofactors, input_model, onto):
	# species_id2chebi_id, fake_terms = get_species_to_chebi(input_model, onto)
	species_id2chebi_id = get_species_to_chebi(input_model, onto)
	terms = (onto.get_term(t_id) for t_id in
	         species_id2chebi_id.itervalues())  # if not onto.getTerm(t_id) in fake_terms)
	filter_ontology(onto, terms, relationships=EQUIVALENT_TERM_RELATIONSHIPS, min_deepness=11)
	cofactor_ids = {cofactor_id for cofactor_id in cofactors if onto.get_term(cofactor_id)}
	ubiquitous_chebi_ids = cofactor_ids | get_ubiquitous_species_set(input_model, species_id2chebi_id, onto)
	return species_id2chebi_id, ubiquitous_chebi_ids
