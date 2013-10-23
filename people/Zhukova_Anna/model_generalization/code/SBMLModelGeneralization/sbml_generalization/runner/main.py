#!/usr/bin/env python
# encoding: utf-8

import getopt
import sys

from sbml_generalization.generalization.sbml_helper import parse_group_sbml, convert_to_l2v4_with_species_types
from sbml_generalization.utils.logger import log
from sbml_generalization.utils.obo_ontology import parse, get_chebi
from sbml_generalization.utils.usage import Usage
from sbml_generalization.generalization.sbml_generalizer import convert


__author__ = 'anna'

##
# runner module generalizes the model.
# usage: runner.py --model model.xml --chebi chebi.obo --outmodel output_model.xml --verbose
##

help_message = '''
Generalizes the model.
usage: runner.py --model model.xml --chebi chebi.obo --outmodel output_model.xml --verbose
'''


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        chebi, in_sbml, out_sbml, groups_sbml, sh_chains, verbose = process_args(argv)
        log(verbose, "parsing ChEBI...")
        ontology = parse(chebi)
        #convert_to_l2v4_with_species_types(groups_sbml)
        #print parse_group_sbml(groups_sbml, ontology)
        convert(in_sbml, out_sbml, groups_sbml, ontology, None, sh_chains, verbose)
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
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
        opts, args = getopt.getopt(argv[1:], "m:c:h:o:v:s",
                                   ["help", "model=", "chebi=", "outmodel=", "verbose", "shorten"])
    except getopt.error, msg:
        raise Usage(msg)
    in_sbml, chebi, out_sbml, shorten, verbose = None, None, None, False, False
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
    out_sbml, groups_sbml = generate_out_sbml_name(in_sbml, out_sbml)
    if not chebi:
        chebi = get_chebi()
    if not in_sbml or not chebi:
        raise Usage(help_message)
    return chebi, in_sbml, out_sbml, groups_sbml, shorten, verbose


if __name__ == "__main__":
    sys.exit(main())