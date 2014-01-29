from collections import defaultdict, Counter

from libsbml import SBMLReader

from sbml_generalization.generalization.reaction_filters import get_reactions_by_species
from sbml_generalization.utils.logger import log
from sbml_generalization.utils.misc import invert_map
from sbml_generalization.utils.obo_ontology import Term
from sbml_helper import save_as_comp_generalized_sbml, remove_is_a_reactions, model_to_l3v1, annotate_ubiquitous, remove_unused_elements
from mark_ubiquitous import getCofactors
from model_generalizer import map2chebi, generalize_species, generalize_reactions, get_reaction_ids_to_factor


__author__ = 'anna'


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


def generalize_model(groups_sbml, out_sbml, in_sbml, onto, cofactors=None, sh_chains=True, verbose=False):
	# input_model
	input_doc = SBMLReader().readSBML(in_sbml)
	input_model = input_doc.getModel()

	remove_is_a_reactions(input_model)
	remove_unused_elements(input_model)
	## go only for reactions inside organelles
	#reactions = [reaction for reaction in input_model.getListOfReactions() if
	#             filterReactionByNotTransport(reaction, input_model)]

	log(verbose, "mapping species to ChEBI...")
	if not cofactors:
		cofactors = getCofactors(onto)
	species_id2chebi_id, ubiquitous_chebi_ids = map2chebi(cofactors, input_model, onto)

	model_to_l3v1(groups_sbml, input_model)
	r_id2g_eq, r_id2ch_id, s_id2gr_id = {}, {}, {}

	ub_sps = {s.getId() for s in input_model.getListOfSpecies() if
	          s.getId() in species_id2chebi_id and species_id2chebi_id[s.getId()] in ubiquitous_chebi_ids}
	annotate_ubiquitous(groups_sbml, ub_sps, verbose)
	#if sh_chains:
	#    # shorten chains
	#    log(verbose, "chain shortening...")
	#    chains = shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
	#    if chains:
	#        # save
	#        r_id2ch_id = save_as_chain_shortened_sbml(chains, input_model, out_sbml, groups_sbml, verbose)
	#        doc = SBMLReader().readSBML(out_sbml)
	#        input_model = doc.getModel()
	#
	#        # update species_id2chebi_id
	#        s_ids = set(species_id2chebi_id.keys())
	#        for s_id in s_ids:
	#            if not input_model.getSpecies(s_id):
	#                del species_id2chebi_id[s_id]
	#                # update reactions, go only for reactions inside organelles
	#                #reactions = [rn for rn in input_model.getListOfReactions() \
	# if filterReactionByNotTransport(rn, input_model)]

	# generalize
	s_id2clu = generalize_species(input_model, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose)

	vks = get_reaction_ids_to_factor(input_model, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	sk2vks = defaultdict(set)
	for (ub_rs, ub_ps, rs, ps) in vks.keys():
		if ub_rs or ub_ps:
			simple_key = (ub_rs, ub_ps, len(rs), len(ps))
			sk2vks[simple_key].add((ub_rs, ub_ps, rs, ps))

	reactions = list(input_model.getListOfReactions())
	i = 0
	for (ub_rs, ub_ps, _, _), vks in sk2vks.iteritems():
		if len(vks) > 1 and (ub_ps or ub_rs):
			# print ub_ps, ' ', ub_rs
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
				# if there are less that 3 common elements, it's not enough evidence
				if len(ub_rs) + len(ub_sps) + len(common_rs) & len(common_ps) < 3:
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

	clu2s_ids = invert_map(s_id2clu)
	print 'final quotient species set:'
	print '\t', sorted([len(s_ids) for s_ids in clu2s_ids.itervalues()])



	# reactions = {r for r in input_model.getListOfReactions()}
	# for species in input_model.getListOfSpecies():
	# 	s_id = species.getId()
	# 	if s_id in species_id2chebi_id:
	# 		continue
	# 	rs = get_reactions_by_species(s_id, reactions)
	# 	for r in rs:
	# 		(ub_rs, ub_ps, rs, ps) = get_vertical_key(r, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	# 		s_k = (ub_rs, ub_ps, len(rs), len(ps))
	# 		if s_k in sk2vks:
	# 			values = set(sk2vks[s_k]) - {(ub_rs, ub_ps, rs, ps)}
	# 			print '----------'
	# 			print 'SK: ', s_k
	# 			print rs, ps
	# 			for (ub_rs, ub_ps, rs, ps) in sk2vks[s_k]:
	# 				print ' ', rs, ps


	r_id2clu = generalize_reactions(input_model, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	# log_r_clusters(r_id2clu, input_model, verbose)
	r_id2g_eq, s_id2gr_id = save_as_comp_generalized_sbml(input_model, out_sbml, groups_sbml, r_id2clu, s_id2clu,
	                                                      verbose)
	return r_id2g_eq, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_sps


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