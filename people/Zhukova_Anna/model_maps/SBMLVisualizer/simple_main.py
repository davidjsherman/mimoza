from libsbml import SBMLReader
import sys
from modules.html_generator import generate_simple_html
from runner.mod_gen_helper import generalize_entities
from runner.runner import prepare_dir, process_args, Usage, log

__author__ = 'anna'
help_message = '''
Generalizes the model.
usage: simple_main.py --model model.xml --verbose
'''


def generalize_model(directory, sbml, scripts, css, fav, verbose):
	reader = SBMLReader()
	input_document = reader.readSBML(sbml)
	input_model = input_document.getModel()
	model_id = input_model.getId()
	m_dir, sbml = prepare_dir(directory, sbml, model_id)
	r_id2ch_id, r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps, groups_sbml = generalize_entities(input_model,
	                                                                                                           sbml, verbose)
	log('generating html')
	generate_simple_html(input_model, '{0}/index.html'.format(m_dir), groups_sbml, scripts, css, fav)


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		sbml, directory, scripts, css, fav, tile, verbose = process_args(argv, help_message)
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2
	generalize_model(directory, sbml, scripts, css, fav, verbose)


if __name__ == "__main__":
	sys.exit(main())