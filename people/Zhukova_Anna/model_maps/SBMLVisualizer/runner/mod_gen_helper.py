from os.path import abspath, dirname, basename, splitext
from libsbml import SBMLReader
from sbml_generalization.generalization.mark_ubiquitous import getCofactors
from sbml_generalization.generalization.model_generalizer import map2chebi
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.generalization.sbml_helper import parse_group_sbml, GrPlError
from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi
from sbml_generalization.utils.obo_ontology import get_chebi, parse
from modules.html_generator import generate_simple_html
from runner.os_helper import copy_sbml_file

__author__ = 'anna'


def generalize_entities(chebi, input_model, sbml_file, verbose=True):
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
		                                                                                  sh_chains=False,
		                                                                                  verbose=verbose)

	return r_id2ch_id, r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps, groups_sbml


def html_model(directory, sbml, scripts, css, fav, verbose):
	reader = SBMLReader()
	input_document = reader.readSBML(sbml)
	input_model = input_document.getModel()
	model_id = input_model.getId()
	m_dir, sbml = copy_sbml_file(directory, sbml, model_id)
	chebi = parse(get_chebi())
	r_id2ch_id, r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps, groups_sbml = generalize_entities(chebi, input_model,
	                                                                                                           sbml, verbose)
	generate_simple_html(input_model, '{0}/index.html'.format(m_dir), groups_sbml, scripts, css, fav)