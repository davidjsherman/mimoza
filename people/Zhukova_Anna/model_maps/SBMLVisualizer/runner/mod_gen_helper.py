from os.path import abspath, dirname, basename, splitext
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.generalization.sbml_helper import parse_group_sbml, GrPlError
from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi

__author__ = 'anna'


def generalize_entities(chebi, input_model, sbml_file, verbose=True, log_file=None):
	r_id2g_id, r_id2ch_id, s_id2gr_id, ub_sps, species_id2chebi_id = {}, {}, {}, set(), {}
	groups_sbml = None
	try:
		r_id2g_id, r_id2ch_id, s_id2gr_id, ub_sps = parse_group_sbml(sbml_file, chebi)
		if r_id2g_id or ub_sps:
			groups_sbml = sbml_file
			species_id2chebi_id = get_species_to_chebi(input_model, chebi)
	except GrPlError:
		pass
	if not r_id2g_id and not ub_sps:
		name, extension = splitext(basename(sbml_file))
		sbml_directory = dirname(abspath(sbml_file))
		groups_sbml = "%s/%s_with_groups%s" % (sbml_directory, name, extension)
		out_sbml = "%s/%s_generalized%s" % (sbml_directory, name, extension)
		r_id2g_id, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_sps = generalize_model(groups_sbml, out_sbml,
		                                                                                  sbml_file, chebi,
		                                                                                  cofactors=None,
		                                                                                  verbose=verbose, log_file=log_file)

	return r_id2ch_id, r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps, groups_sbml
