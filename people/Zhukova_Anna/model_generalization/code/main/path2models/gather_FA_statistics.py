from genericpath import isfile, exists
from os import listdir, makedirs
from shutil import copyfile
from libsbml import SBMLReader, os
import sys
from utils.annotate_with_chebi import getSpeciesTerm, EQUIVALENT_TERM_RELATIONSHIPS
from utils.misc import add2map
from utils.ontology import parse
from utils.reaction_filters import getReactants, getProducts

__author__ = 'anna'


def count_fa_coa_oxidation(model, the_terms, chebi):
    the_species = dict()
    for species in model.getListOfSpecies():
        i = 0
        s_term = getSpeciesTerm(species, chebi, model)
        for terms in the_terms:
            if s_term in terms:
                add2map(the_species, i, species.getId())
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
    the_reactions = dict()
    for reaction in model.getListOfReactions():
        i = 0
        for r_ids in the_s_ids:
            if r_ids:
                s_id1, s_id2 = r_ids
                rs, ps = getReactants(reaction), getProducts(reaction)
                if rs & s_id1 and ps & s_id2 or rs & s_id2 and ps & s_id1:
                # if filterReactionByBetweenSpecies(reaction, s_id1, s_id2):
                    add2map(the_reactions, i, reaction.getId())
                    break
            i += 1
    return tuple(the_species.keys()), tuple(the_reactions.keys()), tuple(
        [the_reactions[k] for k in the_reactions.keys()])


def test_acyl_coa_number(model, acyl_coa_terms, chebi):
    acyls_coa = set()
    for species in model.getListOfSpecies():
        s_term = getSpeciesTerm(species, chebi, model)
        if s_term in acyl_coa_terms:
            acyls_coa.add(species.getId())

    acyl_coa_reactions = 0
    for reaction in model.getListOfReactions():
        if acyls_coa & (getReactants(reaction) | getProducts(reaction)):
            acyl_coa_reactions += 1

    return len(acyls_coa), acyl_coa_reactions


def main(argv=None):
    chebi = os.getcwd() + "/../data/chebi.obo"
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
    in_path = "/Users/anna/Documents/PhD/magnome/MCCMB13/models/paper/sbml/bacteria/"
    out_path = "/Users/anna/Documents/PhD/magnome/MCCMB13/models/paper/sbml/sorted_bacteria/"
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
        dist = out_path + "-".join([str(it) for it in rs]) + "__" + "-".join([str(len(it)) for it in nums]) + "/"
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


if __name__ == "__main__":
    sys.exit(main())