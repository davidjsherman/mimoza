#!/usr/bin/env python
# encoding: utf-8

import getopt
import sys
from libsbml import SBMLReader, SBMLDocument, writeSBMLToFile, BQB_IS, os
from generalization.generalize import generalize
from generalization.mark_ubiquitous import getUbiquitousSpeciesSet, getCofactors
from utils.annotate_with_chebi import getSpecies2chebi, annotateUbiquitous
from utils.ontology import parse, addMiriamPrefix, subOntology
from utils.rdf_annotation_helper import addAnnotation
from utils.reaction_filters import getReactants, getProducts, filterReactionByNotTransport
from utils.sbml_creation_helper import copyElements, createSpecies, createReaction, removeUnusedElements
from utils.usage import Usage
from utils.misc import add2map, invert

__author__ = 'anna'

##
# main module generalizes the model.
# usage: main.py --model model.xml --chebi chebi.obo --outmodel output_model.xml --verbose
##

help_message = '''
Generalizes the model.
usage: main.py --model model.xml --chebi chebi.obo --outmodel output_model.xml --verbose
'''


def generateOutSBMLName(inSBML, outSBML):
    if not outSBML and inSBML:
        extension = inSBML.find(".xml")
        if extension == -1:
            extension = inSBML.find(".sbml")
        if extension == -1:
            extension = len(inSBML)
        outSBML = "{0}_generalized.xml".format(inSBML[:extension])
    return outSBML


def processArgs(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "m:c:h:o:v:", ["help", "model=", "chebi=", "outmodel=", "verbose"])
    except getopt.error, msg:
        raise Usage(msg)
    inSBML, chebi, outSBML, verbose = None, None, None, False
    # option processing
    for option, value in opts:
        if option in ("-h", "--help"):
            raise Usage(help_message)
        if option in ("-m", "--model"):
            inSBML = value
        if option in ("-c", "--chebi"):
            chebi = value
        if option in ("-o", "--outmodel"):
            outSBML = value
        if option in ("-v", "--verbose"):
            verbose = True
    outSBML = generateOutSBMLName(inSBML, outSBML)
    if not chebi:
        chebi = os.getcwd() + "/../data/chebi.obo"
        print chebi
    if not inSBML or not chebi:
        raise Usage(help_message)
    return chebi, inSBML, outSBML, verbose


def saveToGeneralizedModel(genModel, inputModel, s_id2clu, clu2rs):
    clu2s_ids = invert(s_id2clu)
    for clu, species_ids in clu2s_ids.iteritems():
        comp2s_ids = {}
        for s_id in species_ids:
            species = inputModel.getSpecies(s_id)
            c_id = species.getCompartment()
            add2map(comp2s_ids, c_id, s_id)
        for c_id, s_ids in comp2s_ids.iteritems():
            if len(s_ids) > 1:
                new_species = createSpecies(genModel, c_id, type_id=None, name=clu.getName())
                addAnnotation(new_species, BQB_IS, addMiriamPrefix(clu.getId()))
                for s_id in s_ids:
                    s_id2clu[s_id] = new_species.getId()
            else:
                del s_id2clu[s_ids.pop()]

    generalize_species = lambda s_id: s_id2clu[s_id] if (s_id in s_id2clu) else s_id
    s_id_to_generalize = set(s_id2clu.keys())
    for clu, r_set in clu2rs.iteritems():
        comp2rs = {}
        for r in r_set:
            c_id = getCompartment(r, inputModel)
            add2map(comp2rs, c_id, r)
        for c_id, rs in comp2rs.iteritems():
            representative = list(rs)[0]
            reactants = getReactants(representative)
            products = getProducts(representative)
            if (len(rs) == 1) and not ((reactants | products) & s_id_to_generalize):
                genModel.addReaction(representative)
            else:
                reactants = {generalize_species(it) for it in reactants}
                products = {generalize_species(it) for it in products}
                createReaction(genModel, reactants, products,
                               "{0}{1}".format("generalized " if len(rs) > 1 else "", representative.getName()))
    removeUnusedElements(genModel)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        chebi, inSBML, outSBML, verbose = processArgs(argv)

        # inputModel
        reader = SBMLReader()
        inputDocument = reader.readSBML(inSBML)
        inputModel = inputDocument.getModel()

        # go only for reactions inside organelles
        reactions = filter(lambda r: filterReactionByNotTransport(r, inputModel), inputModel.getListOfReactions())
        species = filter(
            lambda s: filter(lambda r: s.getId() in getProducts(r) | getReactants(r), reactions),
            inputModel.getListOfSpecies())

        # annotate with ChEBI
        print "parsing ChEBI..."
        ontology = parse(chebi)
        species_id2chebi_id = getSpecies2chebi(inputModel, species, ontology)
        terms = [ontology.getTerm(t_id) for t_id in set(species_id2chebi_id.values())]
        cofactor_ids = getCofactors(ontology)
        ontology = subOntology(ontology, terms,
                               relationships={'is_a', 'is_conjugate_base_of', 'is_conjugate_acid_of'}, step=None,
                               min_deepness=11)
        cofactor_ids = set(filter(lambda t_id: ontology.getTerm(t_id), cofactor_ids))
        ubiquitous_chebi_ids = cofactor_ids | getUbiquitousSpeciesSet(inputModel, species_id2chebi_id, ontology)

        # print "ubiquitous: ", {ontology.getTerm(it).getName() for it in ubiquitous_chebi_ids}
        annotateUbiquitous(inputModel, species_id2chebi_id, ubiquitous_chebi_ids)

        # generalize
        print "generalizing..."
        s_id2clu, r2clu = generalize(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
        s_id2clu = {s_id: ontology.getTerm(clu) for (s_id, clu) in s_id2clu.iteritems()}

        # save
        print "saving to {0}...".format(outSBML)
        # generalized model
        genDocument = SBMLDocument(inputModel.getSBMLNamespaces())
        genModel = genDocument.createModel()
        copyElements(inputModel, genModel)
        saveToGeneralizedModel(genModel, inputModel, s_id2clu, invert(r2clu))

        outDocument = SBMLDocument(inputModel.getSBMLNamespaces())
        outDocument.setModel(genModel)
        writeSBMLToFile(outDocument, outSBML)

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


def getCompartment(reaction, model):
    s_id = (getReactants(reaction) | getProducts(reaction)).pop()
    return model.getSpecies(s_id).getCompartment()


def filterReactionByNotTransport(reaction, model):
    c_id = None
    for speciesId in getReactants(reaction) | getProducts(reaction):
        species = model.getSpecies(speciesId)
        compartment_id = species.getCompartment()
        if not compartment_id:
            return False
        if not c_id:
            c_id = compartment_id
        if compartment_id != c_id:
            return False
    return True


if __name__ == "__main__":
    sys.exit(main())