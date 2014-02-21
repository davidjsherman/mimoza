from sbml_generalization.generalization.mark_ubiquitous import getCofactors
from sbml_generalization.generalization.model_generalizer import map2chebi
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.generalization.sbml_helper import parse_group_sbml, GrPlError
from sbml_generalization.utils.obo_ontology import get_chebi, parse

__author__ = 'anna'


def generalize_entities(input_model, sbml_file, verbose=True):
	chebi = parse(get_chebi())
	r_id2g_id, r_id2ch_id, s_id2gr_id, ub_sps, species_id2chebi_id = {}, {}, {}, set(), {}
	groups_sbml = None
	try:
		r_id2g_id, r_id2ch_id, s_id2gr_id, ub_sps = parse_group_sbml(sbml_file, chebi)
		cofactors = getCofactors(chebi)
		species_id2chebi_id, ubiquitous_chebi_ids = map2chebi(cofactors, input_model, chebi)
	except GrPlError:
		pass
	if not r_id2g_id and not ub_sps:
		dot = sbml_file.find(".sbml")
		if dot == -1:
			dot = sbml_file.find(".xml")
		groups_sbml = "{0}_with_groups.xml".format(sbml_file[0:dot] if dot != -1 else sbml_file)
		out_sbml = "{0}_generalized.xml".format(sbml_file[0:dot] if dot != -1 else sbml_file)
		r_id2g_id, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_sps = generalize_model(groups_sbml, out_sbml,
		                                                                                  sbml_file, chebi,
		                                                                                  cofactors=None,
		                                                                                  sh_chains=False,
		                                                                                  verbose=verbose)

	return r_id2ch_id, r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps, groups_sbml