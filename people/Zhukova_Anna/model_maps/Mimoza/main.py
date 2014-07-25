# !/usr/bin/env python
# encoding: utf-8


from _libsbml import writeSBMLToFile
import getopt
import logging
import os
from os.path import dirname, abspath
from shutil import copytree

from libsbml import SBMLReader

from mimoza.mimoza import JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON, MIMOZA_URL
from sbml_vis.converter.sbml2tlp import import_sbml
from sbml_vis.file.md5_checker import check_md5
from sbml_vis.file.serializer import serialize
from sbml_vis.converter.tulip_graph2geojson import graph2geojson
import mimoza.mimoza
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.utils.obo_ontology import parse, get_chebi
from sbml_helper import check_for_groups, SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS


__author__ = 'anna'
help_message = '''
Generalizes and visualizes an SBML model.
usage: main.py --model model.xml --verbose
'''

import sys


class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg


def process_args(argv):
	try:
		opts, args = getopt.getopt(argv[1:], "m:h:v",
		                           ["help", "model=", "verbose"])
	except getopt.error, msg:
		raise Usage(msg)
	sbml, verbose = None, False
	# option processing
	for option, value in opts:
		if option in ("-h", "--help"):
			raise Usage(help_message)
		if option in ("-m", "--model"):
			sbml = value
		if option in ("-v", "--verbose"):
			verbose = True
	if not sbml:
		raise Usage(help_message)
	return sbml, verbose


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		sbml, verbose = process_args(argv)
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2

	reader = SBMLReader()
	doc = reader.readSBML(sbml)
	model = doc.getModel()
	if not model:
		raise Exception("The model should be in SBML format")
	model_id = model.getId()
	if not model_id:
		sbml_name = os.path.splitext(os.path.basename(sbml))[0]
		model.setId(sbml_name)
		model_id = sbml_name

	m_id = check_md5(sbml)
	sbml_dir = dirname(abspath(sbml))
	directory = '%s/%s/' % (sbml_dir, m_id)
	if not os.path.exists(directory):
		os.makedirs(directory)
	if not os.path.exists('%s/lib' % directory):
		copytree(get_lib(), '%s/lib' % directory)

	if verbose:
		# log_file = None
		# try:
		# 	log_file = '%s/log.log' % directory
		# 	with open(log_file, "w+"):
		# 		pass
		# except:
		# 	pass
		logging.basicConfig(level=logging.INFO) #, filename=log_file)

	groups_sbml = '%s%s_with_groups.xml' % (directory, model_id)
	if check_for_groups(sbml, SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS):
		if sbml != groups_sbml:
			if not writeSBMLToFile(doc, groups_sbml):
				raise Exception("Could not write your model to %s" % groups_sbml)
	else:
		chebi = parse(get_chebi())
		generalize_model(groups_sbml, None, sbml, chebi, cofactors=None, verbose=True)

	reader = SBMLReader()
	input_document = reader.readSBML(groups_sbml)
	input_model = input_document.getModel()

	root, c_id2info = import_sbml(input_model, groups_sbml, True)

	fc, max_zoom = graph2geojson(c_id2info, root, True)
	serialize(directory=directory, m_dir_id=m_id, input_model=input_model, level2features=fc, groups_sbml=groups_sbml,
	          main_url=MIMOZA_URL, scripts=JS_SCRIPTS, css=CSS_SCRIPTS, fav=MIMOZA_FAVICON, verbose=verbose,
	          max_zoom=max_zoom)


def get_lib():
	return "%s/../lib" % os.path.dirname(os.path.abspath(mimoza.mimoza.__file__))


if __name__ == "__main__":
	sys.exit(main())