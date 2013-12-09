from libsbml import SBMLReader
from sbml_generalization.utils.logger import log, log_r_clusters
from reaction_filters import filterReactionByNotTransport, filterReactionByCompartmentOfAllParticipants
from sbml_helper import save_as_generalized_sbml, save_as_comp_generalized_sbml, save_as_chain_shortened_sbml, \
    remove_is_a_reactions, model_to_l3v1, annotate_ubiquitous, remove_unused_elements
from mark_ubiquitous import getCofactors
from model_generalizer import map2chebi, shorten_chains, generalize_species, generalize_reactions


__author__ = 'anna'


def generalize_model(groups_sbml, out_sbml, in_sbml, onto, cofactors=None, sh_chains=True, verbose=False,
                     using_compartments=True):
    # input_model
    input_doc = SBMLReader().readSBML(in_sbml)
    input_model = input_doc.getModel()

    remove_is_a_reactions(input_model)
    remove_unused_elements(input_model)
    ## go only for reactions inside organelles
    reactions = [reaction for reaction in input_model.getListOfReactions() if
                 filterReactionByNotTransport(reaction, input_model)]

    log(verbose, "mapping species to ChEBI...")
    if not cofactors:
        cofactors = getCofactors(onto)
    ontology, species_id2chebi_id, ubiquitous_chebi_ids = map2chebi(cofactors, input_model, onto)

    model_to_l3v1(groups_sbml, input_model)
    r_id2g_eq, r_id2ch_id, s_id2gr_id = {}, {}, {}

    ub_sps = {s.getId() for s in input_model.getListOfSpecies() if
              s.getId() in species_id2chebi_id and species_id2chebi_id[s.getId()] in ubiquitous_chebi_ids}
    annotate_ubiquitous(groups_sbml, ub_sps, verbose)
    if sh_chains:
        # shorten chains
        log(verbose, "chain shortening...")
        chains = shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
        if chains:
            # save
            r_id2ch_id = save_as_chain_shortened_sbml(chains, input_model, out_sbml, groups_sbml, verbose)
            doc = SBMLReader().readSBML(out_sbml)
            input_model = doc.getModel()

            # update species_id2chebi_id
            s_ids = set(species_id2chebi_id.keys())
            for s_id in s_ids:
                if not input_model.getSpecies(s_id):
                    del species_id2chebi_id[s_id]
                    # update reactions, go only for reactions inside organelles
                    #reactions = [rn for rn in input_model.getListOfReactions() if filterReactionByNotTransport(rn, input_model)]
    if using_compartments:
        result_r2clu, comp2_species_id2clu = {}, []
        total_s_id2clu = {}
        for comp in input_model.getListOfCompartments():
            log(verbose, "generalizing {0}...".format(comp.getName()))
            c_id = comp.getId()
            # generalize
            reactions = [rn for rn in input_model.getListOfReactions() if
                         filterReactionByCompartmentOfAllParticipants(c_id, rn, input_model)]
            comp_species_id2chebi_id = {s_id: ch_id for (s_id, ch_id) in species_id2chebi_id.iteritems() if
                                        c_id == input_model.getSpecies(s_id).getCompartment()}
            s_id2clu = generalize_species(reactions, comp_species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
            if s_id2clu:
                comp2_species_id2clu.append((comp, s_id2clu))
                r2clu = generalize_reactions(reactions, s_id2clu, comp_species_id2chebi_id)
                log_r_clusters(r2clu, verbose)
                result_r2clu.update(r2clu)
                for (s_id, clu) in s_id2clu.iteritems():
                    total_s_id2clu[s_id] = (clu, c_id)
        # generalize transport
        log(verbose, "generalizing transport...")
        if total_s_id2clu:
            tr_reactions = [rn for rn in input_model.getListOfReactions() if
                            not filterReactionByNotTransport(rn, input_model)]
            r2clu = generalize_reactions(tr_reactions, total_s_id2clu, species_id2chebi_id)
            log_r_clusters(r2clu, verbose)
            result_r2clu.update(r2clu)
        r_id2g_eq, s_id2gr_id = save_as_comp_generalized_sbml(input_model, out_sbml, groups_sbml, result_r2clu,
                                                              comp2_species_id2clu, verbose)
    else:
        log(verbose, "generalizing...")
        # generalize
        reactions = [rn for rn in input_model.getListOfReactions() if filterReactionByNotTransport(rn, input_model)]
        s_id2clu = generalize_species(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
        r2clu = generalize_reactions(input_model.getListOfReactions(), s_id2clu, species_id2chebi_id)
        log_r_clusters(r2clu, verbose)
        r_id2g_eq, s_id2gr_id = save_as_generalized_sbml(input_model, out_sbml, groups_sbml, r2clu, s_id2clu, verbose)
    return r_id2g_eq, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_sps