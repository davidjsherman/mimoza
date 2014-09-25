# !/usr/bin/env python
# encoding: utf-8

from libsbml import SBMLReader, SBMLDocument
import getopt
from reaction_filters import matches_compartment_id
from sbml_helper import copy_elements, remove_unused_elements, save_as_sbml


__author__ = 'anna'
help_message = '''
Generalizes and visualizes an SBML model.
usage: extract_subnetwork.py --model model.xml --outmodel out.xml --compartments=c_14,c_4
'''

import sys


class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg


def process_args(argv):
	try:
		opts, args = getopt.getopt(argv[1:], "m:h:o",
		                           ["help", "model=", "outmodel=", "compartments="])
	except getopt.error, msg:
		raise Usage(msg)
	sbml, out_sbml, c_ids = None, None, None
	# option processing
	for option, value in opts:
		if option in ("-h", "--help"):
			raise Usage(help_message)
		if option in ("-m", "--model"):
			sbml = value
		if option in ("-c", "--compartments"):
			c_ids = value.split(",")
		if option in ("-o", "--outmodel"):
			out_sbml = value
	if not sbml or not out_sbml or not c_ids:
		raise Usage(help_message)
	return sbml, out_sbml, c_ids


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		sbml, out_sbml, c_ids = process_args(argv)
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2

	reader = SBMLReader()
	doc = reader.readSBML(sbml)
	model = doc.getModel()
	out_doc = SBMLDocument(model.getSBMLNamespaces())
	out_model = out_doc.createModel()
	copy_elements(model, out_model)

	for r in model.getListOfReactions():
		if matches_compartment_id(c_ids, r, model):
			out_model.addReaction(r)
	remove_unused_elements(out_model)
	save_as_sbml(out_model, out_sbml)

if __name__ == "__main__":
	sys.exit(main())