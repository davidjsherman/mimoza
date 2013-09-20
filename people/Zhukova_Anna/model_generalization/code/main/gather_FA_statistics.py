from genericpath import isfile, exists
from os import listdir, makedirs
from shutil import copyfile
from libsbml import SBMLReader, os
from utils.annotate_with_chebi import getSpeciesTerm, EQUIVALENT_TERM_RELATIONSHIPS
from utils.logger import log
from utils.ontology import parse
from utils.reaction_filters import filterReactionByBetweenSpecies, getReactants, getProducts

__author__ = 'anna'


def testFACoAOxidation(model, the_terms, chebi):
    the_species = dict()
    for species in model.getListOfSpecies():
        i = 0
        s_term = getSpeciesTerm(species, chebi, model)
        for terms in the_terms:
            if s_term in terms:
                the_species[i] = species.getId()
                break
            i += 1
        if 4 == len(the_species.keys()):
            break

    the_r_ids = [(0, 3), (0, 2), (1, 2), (1, 3)]
    the_s_ids = []
    for r_ids in the_r_ids:
        id1, id2 = r_ids
        if id1 in the_species and id2 in the_species:
            the_s_ids.append((the_species[id1], the_species[id2],))
        else:
            the_s_ids.append(tuple())
    the_reactions = dict()
    for reaction in model.getListOfReactions():
        i = 0
        for r_ids in the_s_ids:
            if r_ids:
                s_id1, s_id2 = r_ids
                if filterReactionByBetweenSpecies(reaction, s_id1, s_id2):
                    the_reactions[i] = True
                    break
            i += 1
    return tuple(the_species.keys()), tuple(the_reactions.keys())


def testAcylCoANum(model, aCoA_terms, chebi):
    aCoAs = set()
    for species in model.getListOfSpecies():
        s_term = getSpeciesTerm(species, chebi, model)
        if s_term in aCoA_terms:
            aCoAs.add(species.getId())

    aCoARs = 0
    for reaction in model.getListOfReactions():
        if aCoAs & (getReactants(reaction) | getProducts(reaction)):
            aCoARs += 1

    return len(aCoAs), aCoARs


def testFACoAOxidation_main(verbose=False):
    chebi = os.getcwd() + "/../data/chebi.obo"
    log(verbose, "parsing ChEBI...")
    ontology = parse(chebi)
    # oxo A-CoA, trans A-CoA, FA-CoA, hydroxy FA-CoA
    the_ids = ['chebi:15489', 'chebi:51006', 'chebi:37554', 'chebi:61902']
    the_terms = [{term} | ontology.getEquivalentTerms(term, relationships=EQUIVALENT_TERM_RELATIONSHIPS)
                 for term in [ontology.getTerm(t_id) for t_id in the_ids]]
    # hydroxy A-CoA
    h_term = ontology.getTerm('chebi:62618')
    the_terms[3] |= {h_term} | ontology.getEquivalentTerms(h_term, relationships=EQUIVALENT_TERM_RELATIONSHIPS)
    result = {}
    in_path = "/Users/anna/Desktop/gen_biomodels/"
    out_path = "/Users/anna/Desktop/sorted_gen_biomodels/"
    for f in listdir(in_path):
        inSBML = in_path + f
        if not isfile(inSBML) or inSBML.find(".xml") == -1:
            continue
        reader = SBMLReader()
        inputDocument = reader.readSBML(inSBML)
        inputModel = inputDocument.getModel()
        res = testFACoAOxidation(inputModel, the_terms, ontology)
        sps, rs = res
        key = "__".join(["-".join([str(it) for it in sps]), "-".join([str(it) for it in rs])])
        dist = out_path + key + "/"
        if not exists(dist):
            makedirs(dist)
        copyfile(inSBML, dist + f)
        # print f, " : ", res
        result[key] = 1 if not key in result else result[key] + 1
    print "RESULT: ", result


def testACoANum_main(verbose=False):
    chebi = os.getcwd() + "/../data/chebi.obo"
    log(verbose, "parsing ChEBI...")
    ontology = parse(chebi)
    aCoA = ontology.getTerm('chebi:17984')
    aCoAs = ontology.getEquivalentsAndChildren(aCoA, relationships=EQUIVALENT_TERM_RELATIONSHIPS)
    in_path = "/Users/anna/Desktop/sorted_gen_biomodels/"
    out_path = "/Users/anna/Desktop/sorted_gen_biomodels2/"
    for d in listdir(in_path):
        result = {}
        for f in listdir(in_path + d):
            inSBML = in_path + d + "/" + f
            if not isfile(inSBML) or inSBML.find(".xml") == -1:
                continue
            reader = SBMLReader()
            inputDocument = reader.readSBML(inSBML)
            inputModel = inputDocument.getModel()
            res = testAcylCoANum(inputModel, aCoAs, ontology)
            aCoA_num, aCoARs_num = res
            key = "__".join([str(aCoA_num), str(aCoARs_num)])
            dist = out_path + d + "/" + key + "/"
            if not exists(dist):
                makedirs(dist)
            copyfile(inSBML, dist + f)
            # print f, " : ", res
            result[key] = 1 if not key in result else result[key] + 1
            print d, " : ", result