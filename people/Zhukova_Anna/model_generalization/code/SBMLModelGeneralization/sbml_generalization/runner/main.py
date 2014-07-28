#!/usr/bin/env python
# encoding: utf-8

import getopt
import logging
import sys
from sbml_generalization.generalization.model_generalizer import EQUIVALENT_TERM_RELATIONSHIPS
from sbml_generalization.generalization.sbml_generalizer import generalize_model

from sbml_generalization.utils.obo_ontology import get_chebi, parse
from sbml_generalization.utils.usage import Usage


__author__ = 'anna'

##
# runner module generalizes the model.
# usage: main.py --model model.xml --chebi chebi.obo --verbose
##

help_message = '''
Generalizes the model.
usage: main.py --model model.xml --chebi chebi.obo --verbose
'''


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		chebi, in_sbml, out_sbml, groups_sbml, sh_chains, verbose, log_file = process_args(argv)
		# log(verbose, "parsing ChEBI...")
		if verbose:
			logging.basicConfig(level=logging.INFO)
		ontology = parse(chebi, EQUIVALENT_TERM_RELATIONSHIPS | {'has_role'})
		generalize_model(groups_sbml, None, in_sbml, ontology, None, verbose, log_file)
	except Usage, err:
		logging.error(sys.argv[0].split("/")[-1] + ": " + str(err.msg))
		logging.error(sys.stderr, "\t for help use --help")
		return 2


def generate_out_sbml_name(in_sbml, out_sbml):
	if not in_sbml:
		raise Usage(help_message)
	extension = in_sbml.find(".xml")
	if extension == -1:
		extension = in_sbml.find(".sbml")
	if extension == -1:
		extension = len(in_sbml)
	if not out_sbml:
		out_sbml = "{0}_generalized.xml".format(in_sbml[:extension])
	groups_sbml = "{0}_with_groups.xml".format(in_sbml[:extension])
	return out_sbml, groups_sbml


def process_args(argv):
	try:
		opts, args = getopt.getopt(argv[1:], "m:c:h:o:v:s:l",
		                           ["help", "model=", "chebi=", "outmodel=", "verbose", "shorten", "log="])
	except getopt.error, msg:
		raise Usage(msg)
	in_sbml, chebi, out_sbml, shorten, verbose, log_file = None, None, None, False, False, None
	# option processing
	for option, value in opts:
		if option in ("-h", "--help"):
			raise Usage(help_message)
		if option in ("-m", "--model"):
			in_sbml = value
		if option in ("-c", "--chebi"):
			chebi = value
		if option in ("-o", "--outmodel"):
			out_sbml = value
		if option in ("-v", "--verbose"):
			verbose = True
		if option in ("-s", "--shorten"):
			shorten = True
		if option in ("-l", "--log"):
			log_file = value
	out_sbml, groups_sbml = generate_out_sbml_name(in_sbml, out_sbml)
	if not chebi:
		chebi = get_chebi()
	if not in_sbml or not chebi:
		raise Usage(help_message)
	return chebi, in_sbml, out_sbml, groups_sbml, shorten, verbose, log_file


if __name__ == "__main__":
	sys.exit(main())