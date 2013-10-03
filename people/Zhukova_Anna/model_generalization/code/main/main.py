#!/usr/bin/env python
# encoding: utf-8
from genericpath import exists, isfile

import getopt
from os import makedirs, listdir
import sys
from libsbml import *
from generalization.generalize import generalize
from generalization.mark_ubiquitous import getUbiquitousSpeciesSet, getCofactors
from utils.annotate_with_chebi import getSpecies2chebi, annotateUbiquitous, EQUIVALENT_TERM_RELATIONSHIPS
from utils.logger import log
from utils.ontology import parse, subOntology
from utils.reaction_filters import getReactants, getProducts, filterReactionByNotTransport
from utils.sbml_creation_helper import remove_is_a_reactions
from utils.sbml_serializer import update_initial_sbml, save_as_generalized_sbml
from utils.usage import Usage

__author__ = 'anna'

##
# main module generalizes the model.
# usage: main.py --model model.xml --chebi chebi.obo --outmodel output_model.xml --verbose
##

help_message = '''
Generalizes the model.
usage: main.py --model model.xml --chebi chebi.obo --outmodel output_model.xml --verbose
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
    log(verbose, "filtering reactions and species...")
    remove_is_a_reactions(input_model)
    # go only for reactions inside organelles
    reactions = filter(lambda reaction: filterReactionByNotTransport(reaction, input_model),
                       input_model.getListOfReactions())
    s_ids = set()
    for r in reactions:
        s_ids |= getProducts(r) | getReactants(r)
    species = {input_model.getSpecies(s_id) for s_id in s_ids}

    log(verbose, "mapping species to ChEBI...")
    species_id2chebi_id, fake_terms = getSpecies2chebi(input_model, species, onto)
    terms = [onto.getTerm(t_id) for t_id in set(species_id2chebi_id.values())]
    ontology = subOntology(onto, terms, relationships={'is_a'} | EQUIVALENT_TERM_RELATIONSHIPS, step=None,
                           min_deepness=11)
    for t in fake_terms:
        onto.removeTerm(t)
    cofactor_ids = set(filter(lambda cofactor_id: ontology.getTerm(cofactor_id), cofactors))
    ubiquitous_chebi_ids = cofactor_ids | getUbiquitousSpeciesSet(input_model, species_id2chebi_id, ontology)

    # print "ubiquitous: ", {ontology.getTerm(it).getName() for it in ubiquitous_chebi_ids}
    annotateUbiquitous(input_model, species_id2chebi_id, ubiquitous_chebi_ids)

    # shorten chains
    # log(verbose, "chain shortening...")
    # chains = shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
    # if chains:
    #     # save
    #     input_model = saveToChainShortenedSBML(chains, input_model, verbose)
    #     # update species_id2chebi_id
    #     for s_id in species_id2chebi_id.keys():
    #         if not input_model.getSpecies(s_id):
    #             del species_id2chebi_id[s_id]
    #     # update reactions, go only for reactions inside organelles
    #     reactions = filter(lambda r: filterReactionByNotTransport(r, input_model), input_model.getListOfReactions())

    # generalize
    log(verbose, "generalizing...")
    s_id2clu, r2clu = generalize(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
    s_id2clu = {s_id: ontology.getTerm(clu) for (s_id, clu) in s_id2clu.iteritems()}

    # update input file
    update_initial_sbml(input_model, in_sbml, verbose)

    # save generalized model
    save_as_generalized_sbml(input_model, out_sbml, r2clu, s_id2clu, verbose)

    # save groups model
    # saveAsGroupsSBML(clu2rs, groups_sbml, input_model, reader, s_id2clu, verbose)

    log(verbose, "the end\n")


def generalize_many(chebi, verbose):
    # annotate with ChEBI
    log(verbose, "parsing ChEBI...")
    ontology = parse(chebi)
    cofactor_ids = getCofactors(ontology)
    in_path = "/Users/anna/Documents/PhD/magnome/MCCMB13/models/paper/sbml/biomodels/"
    out_path = "/Users/anna/Documents/PhD/magnome/MCCMB13/models/paper/sbml/gen_biomodels/"
    if not exists(out_path):
        makedirs(out_path)
    gr_path = "/Users/anna/Documents/PhD/magnome/MCCMB13/models/paper/sbml/gr_biomodels/"
    if not exists(gr_path):
        makedirs(gr_path)
        for f in listdir(in_path):
            in_sbml = in_path + f
            out_sbml = out_path + f
            groups_sbml = gr_path + f
            if not isfile(in_sbml) or in_sbml.find(".xml") == -1:
                continue
            log(verbose, "Processing " + in_sbml)
            convert(ontology, cofactor_ids, in_sbml, out_sbml, groups_sbml, verbose)


if __name__ == "__main__":
    sys.exit(main())