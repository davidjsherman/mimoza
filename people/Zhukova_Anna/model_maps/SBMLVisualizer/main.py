import logging
from os.path import splitext, basename, dirname, abspath
from generalization.model_generalizer import get_r_compartments
from modules.sbml2tlp import import_sbml
from runner.tulip_helper import visualize_model
from libsbml import *
from tulip import tlp
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.utils.obo_ontology import parse, get_chebi

__author__ = 'anna'
help_message = '''
Generalizes and visualizes the model.
usage: main.py --model model.xml --verbose
'''

MIMOZA_URL = 'http://mimoza.bordeaux.inria.fr'

TILE = '%s/lib/modelmap/white512.jpg' % MIMOZA_URL

FAVIICON = '%s/lib/modelmap/fav.ico' % MIMOZA_URL

JS_SCRIPTS = [('%s/lib/leaflet/leaflet.js' % MIMOZA_URL),
              ('%s/lib/leaflet_label/leaflet.label.js' % MIMOZA_URL),
              'http://code.jquery.com/jquery-2.0.3.min.js', 'http://code.jquery.com/ui/1.10.4/jquery-ui.js',
              ('%s/lib/modelmap/maptools.js' % MIMOZA_URL)]

CSS_SCRIPTS = [('%s/lib/modelmap/modelmap.css' % MIMOZA_URL),
               ('%s/lib/leaflet/leaflet.css' % MIMOZA_URL),
               ('%s/lib/leaflet_label/leaflet.label.css' % MIMOZA_URL),
               'http://code.jquery.com/ui/1.10.4/themes/smoothness/jquery-ui.css']

import sys
import os


def main(argv=None):
	# if argv is None:
	# 	argv = sys.argv
	# try:
	# 	sbml, directory, scripts, css, fav, tile, verbose = process_args(argv, help_message)
	# except Usage, err:
	# 	print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
	# 	print >> sys.stderr, "\t for help use --help"
	# 	return 2
	# sbml = '/Users/anna/Documents/PhD/magnome/model_generalization/code/MODEL1111190000_golgi.xml'
	# sbml = '/Users/anna/Downloads/yeast_7.11/yeast_7.11_recon_with_groups.xml'
	sbml = '/Users/anna/Documents/PhD/yeast_7.00/yeast_7.00_mito.xml'

	logging.basicConfig(level=logging.INFO)

	name, extension = splitext(basename(sbml))
	sbml_directory = dirname(abspath(sbml))
	groups_sbml = "%s/%s_with_groups%s" % (sbml_directory, name, extension)

	out_sbml = "%s/%s_generalized%s" % (sbml_directory, name, extension)
	chebi = parse(get_chebi())
	generalize_model(groups_sbml, out_sbml, sbml, chebi, cofactors=None, verbose=True)

	reader = SBMLReader()
	input_document = reader.readSBML(groups_sbml)
	input_model = input_document.getModel()

	graph = tlp.newGraph()
	graph, onto, name2id_go = import_sbml(graph, input_model, groups_sbml, True)
	url = '%s/mm/comp.html' % MIMOZA_URL
	visualize_model(directory='/Users/anna/Documents/PhD/magnome/', m_dir_id='mm', input_model=input_model, graph=graph,
	                name2id_go=name2id_go, groups_sbml=groups_sbml, url=url, main_url='http://mimoza.bordeaux.inria.fr',
	                scripts=JS_SCRIPTS, css=CSS_SCRIPTS, fav=FAVIICON, verbose=True)

if __name__ == "__main__":
	sys.exit(main())