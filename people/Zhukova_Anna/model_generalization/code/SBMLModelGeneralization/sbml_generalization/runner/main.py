#!/usr/bin/env python
# encoding: utf-8

import getopt
import logging
from os import listdir
import sys

import libsbml
from merge.model_merger import merge_models

from sbml_generalization.generalization.model_generalizer import EQUIVALENT_TERM_RELATIONSHIPS
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.onto.onto_getter import get_chebi
from sbml_generalization.onto.obo_ontology import parse
from sbml_generalization.utils.misc import invert_map


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
        chebi, in_sbml, in_path, out_sbml, groups_sbml, merged_sbml, verbose, log_file = process_args(argv)
        # log(verbose, "parsing ChEBI...")
        if verbose:
            logging.basicConfig(level=logging.INFO)
        ontology = parse(chebi, EQUIVALENT_TERM_RELATIONSHIPS | {'has_role'})
        if not in_sbml and in_path:
            in_sbml_list = ['%s/%s' % (in_path, f) for f in listdir(in_path)
                            if f.find(".xml") != -1 or f.find(".sbml") != -1]
            merge_models(in_sbml_list, merged_sbml)
            in_sbml = merged_sbml
        r_id2clu, s_id2clu, _, _ = generalize_model(groups_sbml, out_sbml, in_sbml, ontology)
        doc = libsbml.SBMLReader().readSBML(groups_sbml)
        model = doc.getModel()
        clu2r_ids = invert_map(r_id2clu)
        clu2s_ids = invert_map(s_id2clu)
        for s_ids in clu2s_ids.itervalues():
            print(len(s_ids), [(s_id, model.getSpecies(s_id).getName()) for s_id in s_ids])
        print('---------------------')
        for r_ids in clu2r_ids.itervalues():
            print(len(r_ids), [(r_id, model.getReaction(r_id).getName()) for r_id in r_ids])
    except Usage, err:
        logging.error(sys.argv[0].split("/")[-1] + ": " + str(err.msg))
        logging.error(sys.stderr, "\t for help use --help")
        return 2


def generate_out_sbml_name(in_sbml, in_path, out_sbml, groups_sbml, merged_sbml):
    if not in_sbml and not in_path:
        raise Usage(help_message)
    if in_sbml:
        extension = in_sbml.find(".xml")
        if extension == -1:
            extension = in_sbml.find(".sbml")
        if extension == -1:
            extension = len(in_sbml)
        prefix = in_sbml[:extension]
    else:
        prefix = '{0}/merged'.format(in_path)
        if not merged_sbml:
            merged_sbml = "{0}.xml".format(prefix)
    if not out_sbml:
        out_sbml = "{0}_generalized.xml".format(prefix)
    if not groups_sbml:
        groups_sbml = "{0}_with_groups.xml".format(prefix)
    return out_sbml, groups_sbml, merged_sbml


def process_args(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "m:c:h:o:v:l:p:g:b",
                                   ["help", "model=", "chebi=", "outmodel=", "verbose", "log=", "inpath=", "groupsmodel=",
                                    "mergedmodel="])
    except getopt.error, msg:
        raise Usage(msg)
    in_path, in_sbml, groups_sbml, merged_sbml, chebi, out_sbml, verbose, log_file = \
        None, None, None, None, None, None, False, None
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
        if option in ("-g", "--groupsmodel"):
            groups_sbml = value
        if option in ("-b", "--mergedmodel"):
            merged_sbml = value
        if option in ("-v", "--verbose"):
            verbose = True
        if option in ("-l", "--log"):
            log_file = value
        if option in ("-p", "--inpath"):
            in_path = value
    out_sbml, groups_sbml, merged_sbml = generate_out_sbml_name(in_sbml, in_path, out_sbml, groups_sbml, merged_sbml)
    if not chebi:
        chebi = get_chebi()
    if not in_sbml and not in_path:
        raise Usage(help_message)
    return chebi, in_sbml, in_path, out_sbml, groups_sbml, merged_sbml, verbose, log_file


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

if __name__ == "__main__":
    sys.exit(main())