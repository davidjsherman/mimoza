from libsbml import SBMLReader
from sbml_generalization.generalization.sbml_helper import save_as_comp_generalized_sbml, remove_is_a_reactions, \
	remove_unused_elements
from sbml_generalization.utils.logger import log
from mark_ubiquitous import get_cofactors
from model_generalizer import map2chebi, generalize_species, generalize_reactions


__author__ = 'anna'


def generalize_model(groups_sbml, out_sbml, in_sbml, onto, cofactors=None, verbose=False, log_file=None):
	# input_model
	input_doc = SBMLReader().readSBML(in_sbml)
	input_model = input_doc.getModel()

	remove_is_a_reactions(input_model)
	remove_unused_elements(input_model)

	log(verbose, "mapping species to ChEBI...")
	if not cofactors:
		cofactors = get_cofactors(onto)
	species_id2chebi_id, ubiquitous_chebi_ids = map2chebi(cofactors, input_model, onto)

	r_id2g_eq, r_id2ch_id, s_id2gr_id = {}, {}, {}

	ub_sps = {s.getId() for s in input_model.getListOfSpecies() if
	          s.getId() in species_id2chebi_id and species_id2chebi_id[s.getId()] in ubiquitous_chebi_ids}

	# generalize
	s_id2clu = generalize_species(input_model, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose)
	r_id2clu = generalize_reactions(input_model, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
	r_id2g_eq, s_id2gr_id = save_as_comp_generalized_sbml(input_model, out_sbml, groups_sbml, r_id2clu, s_id2clu, ub_sps,
	                                                      verbose)
	log(verbose, "generalization done...")
	return r_id2g_eq, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_sps
