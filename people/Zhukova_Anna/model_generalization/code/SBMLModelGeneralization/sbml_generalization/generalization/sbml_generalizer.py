import logging

import libsbml

from mod_sbml.sbml.ubiquitous_manager import UBIQUITOUS_THRESHOLD, select_metabolite_ids_by_term_ids, get_ubiquitous_chebi_ids
from sbml_generalization.sbml.sbml_helper import save_as_comp_generalized_sbml, remove_is_a_reactions, \
    remove_unused_elements
from sbml_generalization.generalization.model_generalizer import generalize_species, generalize_reactions
from mod_sbml.annotation.chebi.chebi_annotator import get_species_to_chebi, EQUIVALENT_RELATIONSHIPS, \
    add_equivalent_chebi_ids
from mod_sbml.onto.obo_ontology import filter_ontology
from mod_sbml.utils.misc import invert_map


__author__ = 'anna'


def get_ub_elements(input_model, onto, s_id2chebi_id, ub_chebi_ids, ub_s_ids):
    if ub_s_ids:
        if not ub_chebi_ids:
            ub_chebi_ids = set()
        ub_chebi_ids |= {s_id2chebi_id[s_id] for s_id in ub_s_ids if s_id in s_id2chebi_id}
    else:
        if not ub_chebi_ids:
            ub_chebi_ids = get_ubiquitous_chebi_ids(add_common=True, add_cofactors=True, add_frequent=False, onto=onto)
        else:
            ub_chebi_ids = add_equivalent_chebi_ids(onto, ub_chebi_ids)
        ub_s_ids = select_metabolite_ids_by_term_ids(input_model, ub_chebi_ids, s_id2chebi_id)
    return ub_s_ids, ub_chebi_ids


def generalize_model(groups_sbml, out_sbml, in_sbml, onto, ub_s_ids=None, ub_chebi_ids=None):
    # input_model
    input_doc = libsbml.SBMLReader().readSBML(in_sbml)
    input_model = input_doc.getModel()

    remove_is_a_reactions(input_model)
    remove_unused_elements(input_model)

    logging.info("mapping species to ChEBI")
    s_id2chebi_id = get_species_to_chebi(input_model, onto)
    ub_s_ids, ub_chebi_ids = get_ub_elements(input_model, onto, s_id2chebi_id, ub_chebi_ids, ub_s_ids)

    terms = (onto.get_term(t_id) for t_id in s_id2chebi_id.itervalues())
    filter_ontology(onto, terms, relationships=EQUIVALENT_RELATIONSHIPS, min_deepness=5)

    threshold = min(max(3, int(0.1 * input_model.getNumReactions())), UBIQUITOUS_THRESHOLD)
    s_id2clu, ub_s_ids = generalize_species(input_model, s_id2chebi_id, ub_s_ids, onto, ub_chebi_ids, threshold)
    logging.info("generalized species")
    r_id2clu = generalize_reactions(input_model, s_id2clu, s_id2chebi_id, ub_chebi_ids)
    logging.info("generalized reactions")

    clu2s_ids = invert_map(s_id2clu)
    r_id2g_eq, s_id2gr_id = save_as_comp_generalized_sbml(input_model, out_sbml, groups_sbml, r_id2clu, clu2s_ids,
                                                          ub_s_ids, onto)
    return r_id2g_eq, s_id2gr_id, s_id2chebi_id, ub_s_ids


def ubiquitize_model(groups_sbml, in_sbml, onto, ub_s_ids=None, ub_chebi_ids=None):
    input_doc = libsbml.SBMLReader().readSBML(in_sbml)
    input_model = input_doc.getModel()

    logging.info("mapping species to ChEBI")
    s_id2chebi_id = get_species_to_chebi(input_model, onto)
    ub_s_ids, _ = get_ub_elements(input_model, onto, s_id2chebi_id, ub_chebi_ids, ub_s_ids)

    save_as_comp_generalized_sbml(input_model, None, groups_sbml, {}, {}, ub_s_ids, onto)
    return s_id2chebi_id, ub_s_ids
