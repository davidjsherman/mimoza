from libsbml import SBMLReader, SBMLDocument, writeSBMLToFile
from model_generalizer import map2chebi, shorten_chains, generalize
from utils.logger import log
from generalization.reaction_filters import filterReactionByNotTransport, getProducts, getReactants
from generalization.sbml_helper import save_as_generalized_sbml, \
    remove_is_a_reactions, save_as_chain_shortened_sbml, model_to_l3v1, annotate_ubiquitous

__author__ = 'anna'


def generalize_model(groups_sbml, out_sbml, cofactors, input_model, onto, sh_chains=True, verbose=False):
    remove_is_a_reactions(input_model)
    log(verbose, "filtering reactions and species...")
    ## go only for reactions inside organelles
    reactions = filter(lambda reaction: filterReactionByNotTransport(reaction, input_model),
                       input_model.getListOfReactions())

    log(verbose, "mapping species to ChEBI...")
    ontology, species_id2chebi_id, ubiquitous_chebi_ids = map2chebi(cofactors, input_model, onto)

    model_to_l3v1(groups_sbml, input_model)
    annotate_ubiquitous(groups_sbml, species_id2chebi_id, ubiquitous_chebi_ids, verbose)

    if sh_chains:
        # shorten chains
        log(verbose, "chain shortening...")
        chains = shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
        if chains:
            # save
            save_as_chain_shortened_sbml(chains, input_model, out_sbml, groups_sbml, verbose)
            doc = SBMLReader().readSBML(out_sbml)
            input_model = doc.getModel()

            # update species_id2chebi_id
            s_ids = set(species_id2chebi_id.keys())
            for s_id in s_ids:
                if not input_model.getSpecies(s_id):
                    del species_id2chebi_id[s_id]
                    # update reactions, go only for reactions inside organelles
            reactions = filter(lambda rn: filterReactionByNotTransport(rn, input_model),
                               input_model.getListOfReactions())

    # generalize
    log(verbose, "generalizing...")
    s_id2clu, r2clu = generalize(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
    s_id2clu = {s_id: ontology.getTerm(clu) for (s_id, clu) in s_id2clu.iteritems()}
    save_as_generalized_sbml(input_model, out_sbml, groups_sbml, r2clu, s_id2clu, verbose)
    return r2clu, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids


def convert(onto, cofactors, in_sbml, out_sbml, groups_sbml, sh_chains=True, verbose=False):
    # input_model
    input_doc = SBMLReader().readSBML(in_sbml)
    input_model = input_doc.getModel()

    generalize_model(groups_sbml, out_sbml, cofactors, input_model, onto, sh_chains, verbose)

    # print "ubiquitous: ", {ontology.getTerm(it).getName() for it in ubiquitous_chebi_ids}
    # annotateUbiquitous(input_model, species_id2chebi_id, ubiquitous_chebi_ids, verbose)

    log(verbose, "the end\n")