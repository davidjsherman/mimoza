from libsbml import _libsbml
import logging
import libsbml
from annotation.rdf_annotation_helper import get_qualifier_values, add_annotation
from sbml_generalization.annotation.compartment_positioner import get_comp2go, get_go_term
from sbml_generalization.onto.obo_ontology import parse
from sbml_generalization.onto.onto_getter import get_go
from sbml_generalization.sbml.sbml_helper import set_consistency_level

__author__ = 'anna'



CYTOPLASM = 'GO:0005737'

CYTOSOL = 'GO:0005829'


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
    m_id = model.getId() if model.getId() else "m"
    if m_id in m_ids:
        while "%s_%d" % (m_id, i) in m_ids:
            i += 1
        m_id = "%s_%d" % (m_id, i)
        model.setId(m_id)
    m_ids.add(m_id)
    return m_id


def copy_reaction(e, model):
    new_e = model.createReaction()
    new_e.setId(e.getId())
    new_e.setName(e.getName())
    new_e.setCompartment(e.getCompartment())
    new_e.setReversible(e.getReversible())
    new_e.setKineticLaw(e.getKineticLaw())
    for qualifier in [libsbml.BQB_IS, libsbml.BQB_IS_VERSION_OF]:
        for annotation in get_qualifier_values(e, qualifier):
            add_annotation(new_e, qualifier, annotation)
    for s in e.getListOfReactants():
        sr = new_e.createReactant()
        sr.setSpecies(s.getSpecies())
        sr.setStoichiometry(s.getStoichiometry())
    for s in e.getListOfProducts():
        sr = new_e.createProduct()
        sr.setSpecies(s.getSpecies())
        sr.setStoichiometry(s.getStoichiometry())
    for s in e.getListOfModifiers():
        sr = new_e.createModifier()
        sr.setSpecies(s.getSpecies())
        sr.setStoichiometry(s.getStoichiometry())
    new_e.setNotes(e.getNotes())
    return new_e


def copy_species(e, model):
    new_e = model.createSpecies()
    new_e.setId(e.getId())
    new_e.setName(e.getName())
    new_e.setSpeciesType(e.getSpeciesType())
    new_e.setCompartment(e.getCompartment())
    new_e.setBoundaryCondition(e.getBoundaryCondition())
    for qualifier in [libsbml.BQB_IS, libsbml.BQB_IS_VERSION_OF]:
        for annotation in get_qualifier_values(e, qualifier):
            add_annotation(new_e, qualifier, annotation)
    new_e.setNotes(e.getNotes())
    return new_e


def copy_species_type(e, model):
    new_e = model.createSpeciesType()
    new_e.setId(e.getId())
    new_e.setName(e.getName())
    for qualifier in [libsbml.BQB_IS, libsbml.BQB_IS_VERSION_OF]:
        for annotation in get_qualifier_values(e, qualifier):
            add_annotation(new_e, qualifier, annotation)
    new_e.setNotes(e.getNotes())
    return new_e


def copy_compartment(e, model):
    new_e = model.createCompartment()
    new_e.setId(e.getId())
    new_e.setName(e.getName())
    new_e.setOutside(e.getOutside())
    for qualifier in [libsbml.BQB_IS, libsbml.BQB_IS_VERSION_OF]:
        for annotation in get_qualifier_values(e, qualifier):
            add_annotation(new_e, qualifier, annotation)
    new_e.setNotes(e.getNotes())
    return new_e


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
        o_doc.setLevelAndVersion(2, 4, False, True)
        o_model = o_doc.getModel()
        logging.info("Processing %s" % o_sbml)
        m_id = get_model_id(i, m_ids, o_model)
        update_model_element_ids(m_id, o_model, go2c_id, go)
        for e in o_model.getListOfCompartments():
            c_id = e.getId()
            if c_id not in m_c_ids:
                if model.addCompartment(e):
                    copy_compartment(e, model)
                m_c_ids.add(c_id)
        for e in o_model.getListOfSpeciesTypes():
            if model.addSpeciesType(e):
                copy_species_type(e, model)
        for e in o_model.getListOfSpecies():
            if model.addSpecies(e):
                copy_species(e, model)
        for e in o_model.getListOfReactions():
            if model.addReaction(e):
                copy_reaction(e, model)

    libsbml.writeSBMLToFile(doc, out_sbml)