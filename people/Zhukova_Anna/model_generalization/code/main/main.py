#!/usr/bin/env python
# encoding: utf-8
from genericpath import isfile, exists

import getopt
from os import listdir, makedirs
import sys
from libsbml import *
from generalization.generalize import generalize, shorten_chains
from generalization.mark_ubiquitous import getUbiquitousSpeciesSet, getCofactors
from gather_FA_statistics import testFACoAOxidation_main, testACoANum_main
from utils.annotate_with_chebi import getSpecies2chebi, annotateUbiquitous, EQUIVALENT_TERM_RELATIONSHIPS
from utils.logger import log
from utils.ontology import parse, addMiriamPrefix, subOntology
from utils.rdf_annotation_helper import addAnnotation, getTaxonomy
from utils.reaction_filters import getReactants, getProducts, filterReactionByNotTransport
from utils.sbml_creation_helper import copyElements, createSpecies, createReaction, removeUnusedElements, generateUniqueId
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
    if not inSBML:
        raise Usage(help_message)
    extension = inSBML.find(".xml")
    if extension == -1:
        extension = inSBML.find(".sbml")
    if extension == -1:
        extension = len(inSBML)
    if not outSBML: outSBML = "{0}_generalized.xml".format(inSBML[:extension])
    grSBML = "{0}_with_groups.xml".format(inSBML[:extension])
    return outSBML, grSBML


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
    outSBML, grSBML = generateOutSBMLName(inSBML, outSBML)
    if not chebi:
        chebi = os.getcwd() + "/../data/chebi.obo"
    if not inSBML or not chebi:
        raise Usage(help_message)
    return chebi, inSBML, outSBML, grSBML, verbose


def saveToChainShortenedModel(csModel, inputModel, chains):
    processed_rs = set()
    for chain in chains:
        species_chain, k, reaction_chain = chain
        processed_rs |= set(reaction_chain)
        r = inputModel.getReaction(reaction_chain[0])
        # replace the second species in the chain with the last one
        id_replacer = lambda s_id: species_chain[-1] if s_id == species_chain[1] else s_id
        reactants = {id_replacer(it) for it in getReactants(r)}
        products = {id_replacer(it) for it in getProducts(r)}
        createReaction(csModel, reactants, products, "{0}{1}".format("shortened chain: ", r.getName()))
    for r in inputModel.getListOfReactions():
        if not r.getId() in processed_rs:
            csModel.addReaction(r)
    removeUnusedElements(csModel)


def saveToGeneralizedModel(genModel, inputModel, sp_id2clu, clu2rs):
    s_id2clu = {s_id: clu for (s_id, clu) in sp_id2clu.iteritems()}
    clu2s_ids = invert(s_id2clu)
    for clu, species_ids in clu2s_ids.iteritems():
        comp2s_ids = {}
        for s_id in species_ids:
            species = inputModel.getSpecies(s_id)
            c_id = species.getCompartment()
            add2map(comp2s_ids, c_id, s_id)
        for c_id, s_ids in comp2s_ids.iteritems():
            if len(s_ids) > 1:
                new_species = createSpecies(genModel, c_id, type_id=None,
                                            name="{0} ({1})".format(clu.getName(), len(s_ids)))
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
                r_name = representative.getName()
                if len(rs) > 1:
                    r_name = "{0} ({1})".format(r_name, len(rs))
                createReaction(genModel, reactants, products, r_name)
    removeUnusedElements(genModel)


def convertTo31(inputModel):
    outputDocument = SBMLDocument(inputModel.getSBMLNamespaces())
    outputDocument.setModel(inputModel)
    outputDocument.setConsistencyChecksForConversion(LIBSBML_CAT_GENERAL_CONSISTENCY, False)
    outputDocument.setConsistencyChecksForConversion(LIBSBML_CAT_IDENTIFIER_CONSISTENCY, False)
    outputDocument.setConsistencyChecksForConversion(LIBSBML_CAT_UNITS_CONSISTENCY, False)
    outputDocument.setConsistencyChecksForConversion(LIBSBML_CAT_MATHML_CONSISTENCY, False)
    outputDocument.setConsistencyChecksForConversion(LIBSBML_CAT_SBO_CONSISTENCY, False)
    outputDocument.setConsistencyChecksForConversion(LIBSBML_CAT_OVERDETERMINED_MODEL, False)
    outputDocument.setConsistencyChecksForConversion(LIBSBML_CAT_MODELING_PRACTICE, False)
    outputDocument.checkL3v1Compatibility()
    outputDocument.setLevelAndVersion(3, 1, False)
    outputDocument.getSBMLNamespaces().addPackageNamespace("groups", 1)
    return outputDocument


def saveWithGroups(doc, s_id2clu, clu2rs):
    model = doc.getModel()
    mplugin = model.getPlugin("groups")
    clu2s_ids = invert(s_id2clu)
    i = 0
    for clu, species_ids in clu2s_ids.iteritems():
        comp2s_ids = {}
        for s_id in species_ids:
            species = model.getSpecies(s_id)
            c_id = species.getCompartment()
            add2map(comp2s_ids, c_id, s_id)
        for c_id, s_ids in comp2s_ids.iteritems():
            if len(s_ids) > 1:
                s_group = mplugin.createGroup()
                s_group.setId("g_s_{0}".format(i))
                s_group.setKind(GROUP_KIND_CLASSIFICATION)
                s_group.setSBOTerm("SBO:0000252")
                s_group.setName(clu.getName())
                addAnnotation(s_group, BQB_IS, addMiriamPrefix(clu.getId()))
                for s_id in s_ids:
                    member = s_group.createMember()
                    member.setSymbol(s_id)
    i = 0
    for clu, r_set in clu2rs.iteritems():
        comp2rs = {}
        for r in r_set:
            c_id = getCompartment(r, model)
            add2map(comp2rs, c_id, r)
        for c_id, rs in comp2rs.iteritems():
            if len(rs) > 1:
                representative = list(rs)[0]
                r_group = mplugin.createGroup()
                r_group.setId("g_r_{0}".format(i))
                r_group.setKind(GROUP_KIND_COLLECTION)
                r_group.setSBOTerm("SBO:0000176")
                r_group.setName("generalized {0}".format(representative.getName()))
                for r in rs:
                    member = r_group.createMember()
                    member.setSymbol(r.getId())
    return doc


def removeIsAReactions(inputModel):
    to_remove = []
    for reaction in inputModel.getListOfReactions():
        if 1 == reaction.getNumReactants() == reaction.getNumProducts(): # and reaction.getName().find("isa ") != -1:
            to_remove.append(reaction.getId())
    for r_id in to_remove:
        inputModel.removeReaction(r_id)


def saveAsGroupsSBML(clu2rs, grSBML, inputModel, reader, s_id2clu, verbose):
    log(verbose, "saving to {0}...".format(grSBML))
    grDocument = convertTo31(Model(inputModel))
    writeSBMLToFile(grDocument, grSBML)
    grDocument = reader.readSBMLFromFile(grSBML)
    grDocument = saveWithGroups(grDocument, s_id2clu, clu2rs)
    writeSBMLToFile(grDocument, grSBML)


def saveAsGeneralizedSBML(inputModel, outSBML, r2clu, s_id2clu, verbose):
    log(verbose, "saving to {0}...".format(outSBML))
    # generalized model
    genDocument = SBMLDocument(inputModel.getSBMLNamespaces())
    clu2rs = invert(r2clu)
    if not s_id2clu:
        genModel = inputModel
    else:
        genModel = genDocument.createModel()
        copyElements(inputModel, genModel)
        saveToGeneralizedModel(genModel, inputModel, s_id2clu, clu2rs)
    outDocument = SBMLDocument(inputModel.getSBMLNamespaces())
    outDocument.setModel(genModel)
    writeSBMLToFile(outDocument, outSBML)


def saveToChainShortenedSBML(chains, inputModel, verbose):
    log(verbose, "serializing chain shortening...")
    # chain shortened model
    csDocument = SBMLDocument(inputModel.getSBMLNamespaces())
    csModel = csDocument.createModel()
    copyElements(inputModel, csModel)
    saveToChainShortenedModel(csModel, inputModel, chains)
    return csModel


def convert(onto, cofactors, inSBML, outSBML, grSBML, verbose=False):
    # inputModel
    reader = SBMLReader()
    inputDocument = reader.readSBML(inSBML)
    inputModel = inputDocument.getModel()
    log(verbose, "filtering reactions and species...")
    removeIsAReactions(inputModel)
    # go only for reactions inside organelles
    reactions = filter(lambda r: filterReactionByNotTransport(r, inputModel), inputModel.getListOfReactions())
    s_ids = set()
    for r in reactions:
        s_ids |= getProducts(r) | getReactants(r)
    species = {inputModel.getSpecies(s_id) for s_id in s_ids}

    log(verbose, "mapping species to ChEBI...")
    species_id2chebi_id, fake_terms = getSpecies2chebi(inputModel, species, onto)
    terms = [onto.getTerm(t_id) for t_id in set(species_id2chebi_id.values())]
    ontology = subOntology(onto, terms, relationships={'is_a'} | EQUIVALENT_TERM_RELATIONSHIPS, step=None,
                           min_deepness=11)
    for t in fake_terms:
        onto.removeTerm(t)
    cofactor_ids = set(filter(lambda t_id: ontology.getTerm(t_id), cofactors))
    ubiquitous_chebi_ids = cofactor_ids | getUbiquitousSpeciesSet(inputModel, species_id2chebi_id, ontology)

    # print "ubiquitous: ", {ontology.getTerm(it).getName() for it in ubiquitous_chebi_ids}
    annotateUbiquitous(inputModel, species_id2chebi_id, ubiquitous_chebi_ids)

    # shorten chains
    # log(verbose, "chain shortening...")
    # chains = shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
    # if chains:
    #     # save
    #     inputModel = saveToChainShortenedSBML(chains, inputModel, verbose)
    #     # update species_id2chebi_id
    #     for s_id in species_id2chebi_id.keys():
    #         if not inputModel.getSpecies(s_id):
    #             del species_id2chebi_id[s_id]
    #     # update reactions, go only for reactions inside organelles
    #     reactions = filter(lambda r: filterReactionByNotTransport(r, inputModel), inputModel.getListOfReactions())

    # generalize
    log(verbose, "generalizing...")
    s_id2clu, r2clu = generalize(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
    s_id2clu = {s_id: ontology.getTerm(clu) for (s_id, clu) in s_id2clu.iteritems()}

    # save
    saveAsGeneralizedSBML(inputModel, outSBML, r2clu, s_id2clu, verbose)

    # groups model
    # saveAsGroupsSBML(clu2rs, grSBML, inputModel, reader, s_id2clu, verbose)

    log(verbose, "the end\n")


def generalize_main(chebi, inSBML, outSBML, grSBML, verbose):
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
    o, r = len(ontology.getAllTerms()), len(ontology.rel_map.values())
    print o, r
    for f in listdir(in_path):
        inSBML = in_path + f
        outSBML = out_path + f
        grSBML = gr_path + f
        if not isfile(inSBML) or inSBML.find(".xml") == -1:
            continue
        log(verbose, "Processing " + inSBML)
        convert(ontology, cofactor_ids, inSBML, outSBML, grSBML, verbose)
        if o != len(ontology.getAllTerms()) or r != len(ontology.rel_map.values()):
            print len(ontology.getAllTerms()), " ", len(ontology.rel_map.values())
    # convert(ontology, cofactor_ids, inSBML, outSBML, grSBML, verbose)


def get_taxonomies_main():
    in_path = "/Users/anna/Documents/PhD/magnome/MCCMB13/models/paper/sbml/biomodels/"
    out_file = "/Users/anna/Documents/PhD/magnome/MCCMB13/models/paper/sbml/taxo.txt"
    with open(out_file, 'w') as out_f:
        for f in listdir(in_path):
            inSBML = in_path + f
            if not isfile(inSBML) or inSBML.find(".xml") == -1:
                continue
            reader = SBMLReader()
            document = reader.readSBML(inSBML)
            model = document.getModel()
            taxonomy = getTaxonomy(model)
            out_f.write(taxonomy + "\n")


def main(argv=None):
    # get_taxonomies_main()
    if argv is None:
        argv = sys.argv
    try:
        chebi, inSBML, outSBML, grSBML, verbose = processArgs(argv)
        verbose = False
        generalize_main(chebi, inSBML, outSBML, grSBML, verbose)
        testFACoAOxidation_main(verbose)
        # testACoANum_main(verbose)
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