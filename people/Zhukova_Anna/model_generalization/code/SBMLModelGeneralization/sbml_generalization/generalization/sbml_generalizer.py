import logging

import libsbml

from sbml_generalization.generalization.mark_ubiquitous import UBIQUITOUS_THRESHOLD, get_cofactors, COMMON_UB_IDS
from sbml_generalization.generalization.sbml_helper import save_as_comp_generalized_sbml, remove_is_a_reactions, \
    remove_unused_elements, set_consistency_level
from sbml_generalization.generalization.model_generalizer import generalize_species, generalize_reactions, \
    EQUIVALENT_TERM_RELATIONSHIPS
from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi
from sbml_generalization.utils.obo_ontology import filter_ontology, parse, get_go
from sbml_generalization.utils.misc import invert_map
from sbml_generalization.utils.compartment_positioner import get_comp2go


CYTOPLASM = 'GO:0005737'

CYTOSOL = 'GO:0005829'

__author__ = 'anna'


def add_equivalent_ub_chebi_ids(onto, ub_chebi_ids):
    return reduce(lambda s1, s2: s1 | s2,
                  (reduce(lambda s1, s2: s1 | s2,
                          (it.get_all_ids() for it in onto.get_equivalents(t, relationships=EQUIVALENT_TERM_RELATIONSHIPS)),
                          t.get_all_ids())
                   for t in (onto.get_term(ub_id) for ub_id in ub_chebi_ids)), ub_chebi_ids)


def get_ub_elements(input_model, onto, s_id2chebi_id, ub_chebi_ids, ub_s_ids):
    if ub_s_ids:
        if not ub_chebi_ids:
            ub_chebi_ids = set()
        ub_chebi_ids |= {s_id2chebi_id[s_id] for s_id in ub_s_ids if s_id in s_id2chebi_id}
    if not ub_chebi_ids:
        ub_chebi_ids = get_cofactors(onto) | COMMON_UB_IDS
        ub_chebi_ids = add_equivalent_ub_chebi_ids(onto, ub_chebi_ids)
    else:
        ub_chebi_ids = add_equivalent_ub_chebi_ids(onto, ub_chebi_ids)
        if not ub_s_ids:
            ub_s_ids = {s.getId() for s in input_model.getListOfSpecies() if
                        s.getId() in s_id2chebi_id and s_id2chebi_id[s.getId()] in ub_chebi_ids}
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
    filter_ontology(onto, terms, relationships=EQUIVALENT_TERM_RELATIONSHIPS, min_deepness=5)

    threshold = min(max(3, int(0.1 * input_model.getNumReactions())), UBIQUITOUS_THRESHOLD)
    s_id2clu, ub_s_ids = generalize_species(input_model, s_id2chebi_id, ub_s_ids, onto, ub_chebi_ids, threshold)
    logging.info("generalized species")
    r_id2clu = generalize_reactions(input_model, s_id2clu, s_id2chebi_id, ub_chebi_ids)
    logging.info("generalized reactions")

    clu2s_ids = invert_map(s_id2clu)
    r_id2g_eq, s_id2gr_id = save_as_comp_generalized_sbml(input_model, out_sbml, groups_sbml, r_id2clu, clu2s_ids,
                                                          ub_s_ids, onto)
    return r_id2g_eq, s_id2gr_id, s_id2chebi_id, ub_s_ids


def update_model_element_ids(m_id, model, go2c_id, go):
    id2id = {}
    comp2go_term = get_comp2go(model, go)
    for c in model.getListOfCompartments():
        c_id = c.getId()
        go_id = comp2go_term[c_id]
        if not go_id:
            c_name = c.getName()
            if c_name:
                go_id = c_name.lower()
        elif go_id == CYTOSOL and CYTOSOL not in go2c_id and CYTOPLASM in go2c_id:
            go_id = CYTOPLASM
        elif go_id == CYTOPLASM and CYTOSOL in go2c_id and CYTOPLASM not in go2c_id:
            go_id = CYTOSOL
        if go_id:
            if go_id not in go2c_id:
                go2c_id[go_id] = "%s__%s" % (m_id, c_id)
            new_c_id = go2c_id[go_id]
            c.setId(new_c_id)
        else:
            new_c_id = "%s__%s" % (m_id, c_id)
            c.setId(new_c_id)
        id2id[c_id] = new_c_id

    for c in model.getListOfCompartments():
        if c.getOutside():
            c.setOutside(id2id[c.getOutside()])

    for s_t in model.getListOfSpeciesTypes():
        old_id = s_t.getId()
        new_id = "%s__%s" % (m_id, old_id)
        s_t.setId(new_id)
        id2id[old_id] = new_id

    for s in model.getListOfSpecies():
        old_id = s.getId()
        new_id = "%s__%s" % (m_id, old_id)
        s.setId(new_id)
        id2id[old_id] = new_id
        if s.getSpeciesType():
            s.setSpeciesType(id2id[s.getSpeciesType()])
        if s.getCompartment():
            s.setCompartment(id2id[s.getCompartment()])

    for r in model.getListOfReactions():
        old_id = r.getId()
        new_id = "%s__%s" % (m_id, old_id)
        r.setId(new_id)
        id2id[old_id] = new_id
        if r.getCompartment():
            r.setCompartment(id2id[r.getCompartment()])
        for s_ref in r.getListOfReactants():
            s_ref.setSpecies(id2id[s_ref.getSpecies()])
        for s_ref in r.getListOfProducts():
            s_ref.setSpecies(id2id[s_ref.getSpecies()])
        for s_ref in r.getListOfModifiers():
            s_ref.setSpecies(id2id[s_ref.getSpecies()])


def get_model_id(i, m_ids, model):
    m_id = model.getId()
    if not m_id:
        while "m_%d" % i in m_ids:
            i += 1
        m_id = "m_%d" % i
        model.setId(m_id)
    m_ids.add(m_id)
    return m_id


def merge_models(in_sbml_list, out_sbml):
    if not in_sbml_list:
        raise ValueError('Provide SBML models to be merged')
    go = parse(get_go())
    i = 0
    m_ids = set()
    go2c_id = {}

    doc = libsbml.SBMLDocument(2, 4)
    model = doc.createModel()
    model.setId('m_merged')
    m_c_ids = set()

    for o_sbml in in_sbml_list:
        o_doc = libsbml.SBMLReader().readSBML(o_sbml)
        set_consistency_level(o_doc)
        o_doc.checkL2v4Compatibility()
        o_doc.setLevelAndVersion(2, 4, False)
        o_model = o_doc.getModel()
        logging.info("Processing %s" % o_sbml)
        m_id = get_model_id(i, m_ids, o_model)
        update_model_element_ids(m_id, o_model, go2c_id, go)
        for c in o_model.getListOfCompartments():
            c_id = c.getId()
            if c_id not in m_c_ids:
                model.addCompartment(c)
                m_c_ids.add(c_id)
        for s_t in o_model.getListOfSpeciesTypes():
            model.addSpeciesType(s_t)
        for s in o_model.getListOfSpecies():
            model.addSpecies(s)
        for r in o_model.getListOfReactions():
            model.addReaction(r)

    libsbml.writeSBMLToFile(doc, out_sbml)


def ubiquitize_model(groups_sbml, in_sbml, onto, ub_s_ids=None, ub_chebi_ids=None):
    # input_model
    input_doc = libsbml.SBMLReader().readSBML(in_sbml)
    input_model = input_doc.getModel()

    logging.info("mapping species to ChEBI")
    s_id2chebi_id = get_species_to_chebi(input_model, onto)
    ub_s_ids, _ = get_ub_elements(input_model, onto, s_id2chebi_id, ub_chebi_ids, ub_s_ids)

    save_as_comp_generalized_sbml(input_model, None, groups_sbml, {}, {}, ub_s_ids, onto)
    return s_id2chebi_id, ub_s_ids
