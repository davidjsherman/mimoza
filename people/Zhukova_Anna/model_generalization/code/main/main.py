#!/usr/bin/env python
# encoding: utf-8

import getopt
import sys
from libsbml import SBMLReader, SBMLDocument, writeSBMLToFile, BQB_IS
from generalization.generalize import generalize
from generalization.mark_ubiquitous import getUbiquitousSpeciesSet
from utils.annotate_with_chebi import getSpecies2chebi_id
from utils.ontology import parse, addMiriamPrefix, subOntology
from utils.rdf_annotation_helper import addAnnotation
from utils.reaction_filters import filterReactionByCompartmentOfAllParticipants, getReactants, getProducts, filterReactionByNotTransport
from utils.sbml_creation_helper import copyElements, createSpecies, createReaction, removeUnusedElements
from utils.usage import Usage
from utils.misc import add2map

__author__ = 'anna'

##
# main module generalizes the model.
# usage: main.py --model model.xml --chebi chebi.obo --outmodel output_model.xml
##

help_message = '''
Generalizes the model.
usage: main.py --model model.xml --chebi chebi.obo --outmodel output_model.xml
'''


def main(argv=None):
    """

    :param argv:
    :return: :raise:
    """
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "m:c:h:o:", ["help", "model=", "chebi=", "outmodel="])
        except getopt.error, msg:
            raise Usage(msg)

        inSBML, chebi, outSBML = None, None, None

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

        inSBML = "/Users/anna/Downloads/MODEL1111190000.xml"
        outSBML = "/Users/anna/Downloads/yali_loira_gen_bis.xml"
        chebi = "/Users/anna/Documents/PhD/gforge/pathtastic/runs/YALI/annotation/chebi.obo"

        if not inSBML or not chebi or not outSBML:
            raise Usage(help_message)

        reader = SBMLReader()
        inputDocument = reader.readSBML(inSBML)
        inputModel = inputDocument.getModel()

        # outputDocument = SBMLDocument(inputModel.getSBMLNamespaces())
        # outputDocument.setModel(inputModel)
        # outputModel = outputDocument.getModel()

        # generalized model
        genDocument = SBMLDocument(inputModel.getSBMLNamespaces())
        genModel = genDocument.createModel()
        copyElements(inputModel, genModel)

        ontology = parse(chebi)
        species = inputModel.getListOfSpecies()
        all_species_id2chebi_id = getSpecies2chebi_id(inputModel, species, ontology)
        ontology = subOntology(ontology, set(all_species_id2chebi_id.values()),
                               relationships={'is_a', 'is_conjugate_base_of', 'is_conjugate_acid_of'}, step=5)
        ubiquitous_chebi_ids = getUbiquitousSpeciesSet(inputModel.getListOfReactions(), all_species_id2chebi_id,
                                                       ontology, threshold=30)
        species_id2chebi_id = dict(
            filter(lambda (s_id, t_id): not (t_id in ubiquitous_chebi_ids), all_species_id2chebi_id.iteritems()))

        print [ontology.getTerm(u_id).getName() for u_id in ubiquitous_chebi_ids]
        reactions = filter(lambda r: filterReactionByNotTransport(r, inputModel), inputModel.getListOfReactions())

        species_id2chebi_term = {s_id: ontology.getTerm(t_id) for (s_id, t_id) in species_id2chebi_id.iteritems()}

        clu2s_ids, clu2rs, s_id2clu, r2clu = generalize(reactions, species_id2chebi_term, ontology)
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

        generalize_species = lambda s_id: s_id2clu[s_id] if s_id in s_id2clu else s_id
        for clu, r_set in clu2rs.iteritems():
            comp2rs = {}
            for r in r_set:
                c_id = getCompartment(r, inputModel)
                add2map(comp2rs, c_id, r)
            for c_id, rs in comp2rs.iteritems():
                representative = rs.pop()
                reactants = [generalize_species(it) for it in getReactants(representative)]
                products = [generalize_species(it) for it in getProducts(representative)]
                print "+1"
                createReaction(genModel, reactants, products,
                               "{0}{1}".format("generalized " if len(rs) > 1 else "", representative.getName()))

        # outputDocument.setModel(outputModel)
        # writeSBMLToFile(outputDocument, outSBML)
        print "removing rubbish"
        removeUnusedElements(genModel)

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


if __name__ == "__main__":
    sys.exit(main())