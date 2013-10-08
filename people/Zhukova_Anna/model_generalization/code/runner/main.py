#!/usr/bin/env python
# encoding: utf-8

import getopt
import sys
from libsbml import *
from generalization.generalize import generalize_model
from generalization.mark_ubiquitous import getCofactors
from utils.annotate_with_chebi import annotateUbiquitous
from utils.logger import log
from utils.misc import invert
from utils.ontology import parse
from utils.sbml_serializer import update_initial_sbml, save_as_generalized_sbml, save_as_groups_sbml
from utils.usage import Usage

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
        chebi, in_sbml, out_sbml, groups_sbml, verbose = process_args(argv)
        # annotate with ChEBI
        log(verbose, "parsing ChEBI...")
        ontology = parse(chebi)
        cofactor_ids = getCofactors(ontology)
        convert(ontology, cofactor_ids, in_sbml, out_sbml, groups_sbml, verbose)
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
        opts, args = getopt.getopt(argv[1:], "m:c:h:o:v:", ["help", "model=", "chebi=", "outmodel=", "verbose"])
    except getopt.error, msg:
        raise Usage(msg)
    in_sbml, chebi, out_sbml, verbose = None, None, None, False
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
    out_sbml, groups_sbml = generate_out_sbml_name(in_sbml, out_sbml)
    if not chebi:
        chebi = os.getcwd() + "/../data/chebi.obo"
    if not in_sbml or not chebi:
        raise Usage(help_message)
    return chebi, in_sbml, out_sbml, groups_sbml, verbose


def convert(onto, cofactors, in_sbml, out_sbml, groups_sbml, verbose=False):
    # input_model
    reader = SBMLReader()
    input_doc = reader.readSBML(in_sbml)
    input_model = input_doc.getModel()

    input_model, species_id2chebi_id, ubiquitous_chebi_ids, s_id2clu, r2clu = generalize_model(input_model, onto,
                                                                                               cofactors, False,
                                                                                               verbose)

    # print "ubiquitous: ", {ontology.getTerm(it).getName() for it in ubiquitous_chebi_ids}
    annotateUbiquitous(input_model, species_id2chebi_id, ubiquitous_chebi_ids)

    # update input file
    update_initial_sbml(input_model, in_sbml, verbose)

    # save generalized model
    save_as_generalized_sbml(input_model, out_sbml, r2clu, s_id2clu, verbose)

    # save groups model
    clu2rs = invert(r2clu)
    save_as_groups_sbml(clu2rs, groups_sbml, input_model, reader, s_id2clu, verbose)

    log(verbose, "the end\n")


if __name__ == "__main__":
    sys.exit(main())