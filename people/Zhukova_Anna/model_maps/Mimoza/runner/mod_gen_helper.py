from sbml_generalization.generalization.sbml_helper import parse_group_sbml, GrPlError, check_for_groups, \
	SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS
from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi

__author__ = 'anna'


def process_generalized_model(chebi, input_model, sbml_file):
	try:
		r_id2g_id, s_id2gr_id, ub_sps = parse_group_sbml(sbml_file, chebi)
		species_id2chebi_id = get_species_to_chebi(input_model, chebi) if (r_id2g_id or ub_sps) else {}
		return r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps
	except GrPlError:
		return None, None, None, None, None


def check_if_already_generalized(sbml_file):
	return check_for_groups(sbml_file, SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS)