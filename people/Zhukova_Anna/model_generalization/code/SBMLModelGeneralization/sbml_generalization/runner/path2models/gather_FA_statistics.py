from collections import defaultdict
from genericpath import isfile, exists
from os import listdir, makedirs
import os
from shutil import copyfile

from libsbml import SBMLReader
from sbml_generalization.utils.annotate_with_chebi import get_species_term
from sbml_generalization.generalization.reaction_filters import get_reactants, get_products
from sbml_generalization.generalization.model_generalizer import EQUIVALENT_TERM_RELATIONSHIPS
from sbml_generalization.utils.obo_ontology import parse
from main import ROOT_DIR


__author__ = 'anna'


def count_fa_coa_oxidation(model, the_terms, chebi):
    the_species = defaultdict(set)
    for species in model.getListOfSpecies():
        i = 0
        s_term = get_species_term(species, chebi, model)
        for terms in the_terms:
            if s_term in terms:
                the_species[i].add(species.getId())
                break
            i += 1

    the_r_ids = [(0, 1), (1, 2), (2, 3), (3, 0)]
    the_s_ids = []
    for r_ids in the_r_ids:
        id1, id2 = r_ids
        if id1 in the_species and id2 in the_species:
            the_s_ids.append((the_species[id1], the_species[id2],))
        else:
            the_s_ids.append(tuple())
    the_reactions = defaultdict(set)
    for reaction in model.getListOfReactions():
        i = 0
        for r_ids in the_s_ids:
            if r_ids:
                s_id1, s_id2 = r_ids
                rs, ps = get_reactants(reaction), get_products(reaction)
                if rs & s_id1 and ps & s_id2 or rs & s_id2 and ps & s_id1:
                # if filterReactionByBetweenSpecies(reaction, s_id1, s_id2):
                    the_reactions[i].add(reaction.getId())
                    break
            i += 1
    return tuple(the_species.keys()), tuple(the_reactions.keys()), tuple(
        [the_reactions[k] for k in the_reactions.keys()])


def test_acyl_coa_number(model, acyl_coa_terms, chebi):
    acyls_coa = set()
    for species in model.getListOfSpecies():
        s_term = get_species_term(species, chebi, model)
        if s_term in acyl_coa_terms:
            acyls_coa.add(species.getId())

    acyl_coa_reactions = 0
    for reaction in model.getListOfReactions():
        if acyls_coa & (get_reactants(reaction) | get_products(reaction)):
            acyl_coa_reactions += 1

    return len(acyls_coa), acyl_coa_reactions


def get_statistics():
    chebi = os.getcwd() + "/../../data/chebi.obo"
    ontology = parse(chebi)
    # FA-CoA, trans A-CoA, hydroxy FA-CoA, oxo A-CoA
    the_ids = ['chebi:37554', 'chebi:51006', 'chebi:61902', 'chebi:15489']
    the_terms = [{term} | ontology.getEquivalentTerms(term, relationships=EQUIVALENT_TERM_RELATIONSHIPS)
                 | ontology.getAnyChildren(term, False, set(), relationships=EQUIVALENT_TERM_RELATIONSHIPS)
                 for term in [ontology.getTerm(t_id) for t_id in the_ids]]
    # hydroxy A-CoA
    h_term = ontology.getTerm('chebi:62618')
    the_terms[2] |= {h_term} | ontology.getEquivalentTerms(h_term, relationships=EQUIVALENT_TERM_RELATIONSHIPS) \
                    | ontology.getAnyChildren(h_term, False, set(), relationships=EQUIVALENT_TERM_RELATIONSHIPS)
    the_terms[0] -= (the_terms[3] | the_terms[1] | the_terms[2])
    #result = {}
    #model2key = {}
    in_path = ROOT_DIR + "bacteria/"
    out_path = ROOT_DIR + "sorted_bacteria/"
    for f in listdir(in_path):
        in_sbml = in_path + f
        if not isfile(in_sbml) or in_sbml.find(".xml") == -1:
            continue
        reader = SBMLReader()
        input_doc = reader.readSBML(in_sbml)
        input_model = input_doc.getModel()
        res = count_fa_coa_oxidation(input_model, the_terms, ontology)
        sps, rs, nums = res
        #k = tuple(sorted(zip(rs, [len(t) for t in nums]), key=lambda it: it[0])) #, "-".join([str(it) for it in sps])])
        #d = dict(k)
        dist = "{0}{1}__{2}/".format(out_path, "-".join([str(it) for it in rs]), "-".join([str(len(it)) for it in nums]))
        if not exists(dist):
            makedirs(dist)
        copyfile(in_sbml, dist + f)
        #model2key["\multicolumn{3}{c}{" + in_sbml[in_sbml.find("BMID"):in_sbml.find(".xml")] + "}"] = \
        # " & ".join(["-" if not i in rs else '+'*d[i] for i in [0,1,2,3]])
        # print f, " : ", res
        #result[k] = 1 if not k in result else result[k] + 1
        #print_list = []
        #for k in sorted(sorted(result.keys()), key=lambda it: len(it)):
        #    rs2num = dict(k)
        #    l = []
        #    for i in [0, 1, 2, 3]:
        #        l.append(0 if not i in rs2num else rs2num[i])
        #    l.append(result[k])
        #    print_list.append(l)
        #for it in reversed(sorted(print_list, key = lambda it: sorted(it))):
        #    s = ['-' if i == 0 else '+'*i for i in it[:4]]
        #    print " & ".join(s), str(it[4]), " \\\\"
        #for m in sorted(model2key.keys()):
        #     print m, " & ", model2key[m], " \\\\"
