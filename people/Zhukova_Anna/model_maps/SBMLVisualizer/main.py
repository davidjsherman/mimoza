import logging
from os.path import splitext, basename, dirname, abspath
from mimoza.mimoza import JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON
from modules.sbml2tlp import import_sbml
from runner.mod_gen_helper import check_if_already_generalized
from runner.serializer import serialize
from libsbml import SBMLReader
from tulip import tlp
from runner.tulip_helper import graph2geojson
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.utils.obo_ontology import parse, get_chebi

__author__ = 'anna'
help_message = '''
Generalizes and visualizes the model.
usage: main.py --model model.xml --verbose
'''

import sys


def main(argv=None):
	# if argv is None:
	# 	argv = sys.argv
	# try:
	# 	sbml, directory, scripts, css, fav, tile, verbose = process_args(argv, help_message)
	# except Usage, err:
	# 	print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
	# 	print >> sys.stderr, "\t for help use --help"
	# 	return 2
	sbml = '/Users/anna/Documents/PhD/magnome/model_generalization/code/MODEL1111190000_pero_with_groups.xml'
	# sbml = '/Users/anna/Downloads/MODEL1209060000.xml'
	# sbml = '/Users/anna/Documents/PhD/yeast_7.00/yeast_7.00_mito.xml'

	# reader = SBMLReader()
	# input_document = reader.readSBML(sbml)
	# input_model = input_document.getModel()
	#
	# print comp2level(input_model)

	logging.basicConfig(level=logging.INFO)

	name, extension = splitext(basename(sbml))
	sbml_directory = dirname(abspath(sbml))
	if check_if_already_generalized(sbml):
		groups_sbml = sbml
	else:
		groups_sbml = "%s/%s_with_groups%s" % (sbml_directory, name, extension)
		chebi = parse(get_chebi())
		generalize_model(groups_sbml, None, sbml, chebi, cofactors=None, verbose=True)

	reader = SBMLReader()
	input_document = reader.readSBML(groups_sbml)
	input_model = input_document.getModel()

	graph = tlp.newGraph()
	# graph, onto, name2id_go = import_sbml(graph, input_model, groups_sbml, True)
	graph, onto, c_id2info = import_sbml(graph, input_model, groups_sbml, True)
	url = 'comp.html'

	fc, max_zoom = graph2geojson(c_id2info, graph, input_model, True)
	serialize(directory='/Users/anna/Documents/PhD/magnome/model_maps/mimoza/html/mm/', m_dir_id='mm',
	          input_model=input_model, features=fc, groups_sbml=groups_sbml, url=url,
	          main_url='http://mimoza.bordeaux.inria.fr', scripts=JS_SCRIPTS, css=CSS_SCRIPTS, fav=MIMOZA_FAVICON,
	          verbose=True, max_zoom=max_zoom)

if __name__ == "__main__":
	sys.exit(main())