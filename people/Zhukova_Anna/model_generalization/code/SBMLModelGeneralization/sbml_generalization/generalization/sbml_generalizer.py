from collections import defaultdict
from libsbml import SBMLReader
from sbml_generalization.generalization.reaction_filters import get_reactions_by_species
from sbml_generalization.generalization.vertical_key import get_vertical_key
from sbml_generalization.utils.logger import log, log_r_clusters
from sbml_helper import save_as_comp_generalized_sbml, remove_is_a_reactions, model_to_l3v1, annotate_ubiquitous, remove_unused_elements
from mark_ubiquitous import getCofactors
from model_generalizer import map2chebi, generalize_species, generalize_reactions, get_reaction_ids_to_factor


__author__ = 'anna'


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
		rns = vks[(ub_rs, ub_ps, rs, ps)]
		if len(rns) > 1 and (ub_rs or ub_ps):
			simple_key = (ub_rs, ub_ps, len(rs), len(ps))
			sk2vks[simple_key].add((ub_rs, ub_ps, rs, ps))

	reactions = {r for r in input_model.getListOfReactions()}
	for species in input_model.getListOfSpecies():
		s_id = species.getId()
		if s_id in species_id2chebi_id:
			continue
		rs = get_reactions_by_species(s_id, reactions)
		for r in rs:
			(ub_rs, ub_ps, rs, ps) = get_vertical_key(r, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
			s_k = (ub_rs, ub_ps, len(rs), len(ps))
			if s_k in sk2vks:
				print '----------'
				print 'SK: ', s_k
				print rs, ps
				for (ub_rs, ub_ps, rs, ps) in sk2vks[s_k]:
					print ' ', rs, ps



	r_id2clu = generalize_reactions(input_model, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	log_r_clusters(r_id2clu, input_model, verbose)
	r_id2g_eq, s_id2gr_id = save_as_comp_generalized_sbml(input_model, out_sbml, groups_sbml, r_id2clu, s_id2clu,
	                                                      verbose)
	return r_id2g_eq, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_sps