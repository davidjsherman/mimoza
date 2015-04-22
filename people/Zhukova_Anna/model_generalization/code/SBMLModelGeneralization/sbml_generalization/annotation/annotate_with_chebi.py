from collections import defaultdict
from itertools import chain

from sbml_generalization.annotation.kegg_manager import get_kegg_m_id
from sbml_generalization.sbml.reaction_filters import get_formula
from sbml_generalization.onto.obo_ontology import to_identifiers_org_format
from sbml_generalization.annotation.rdf_annotation_helper import add_annotation, \
    get_is_qualifier, get_is_annotations, get_is_vo_annotations


__author__ = 'anna'


def get_term(entity, chebi):
    for is_annotation in chain(get_is_annotations(entity), get_is_vo_annotations(entity)):
        term = chebi.get_term(is_annotation)
        if term:
            return term
    return None


def normalize(name):
    return name.strip()


def get_species_term(species, chebi, model):
    term = get_term(species, chebi)
    if not term:
        s_type_id = species.getSpeciesType()
        if s_type_id:
            s_type = model.getSpeciesType(s_type_id)
            if s_type:
                term = get_term(s_type, chebi)
    return term


def find_term_id(entity, chebi):
    term = get_term(entity, chebi)
    if term:
        return term.get_id()

    for formula in get_formula(entity):
        if formula and formula != '.':
            term = chebi.get_term(formula)
            if term:
                return term.get_id()

    kegg = get_kegg_m_id(entity)
    if kegg:
        t_id = chebi.get_t_id_by_kegg(kegg)
        if t_id:
            return t_id

    return None


def get_species_to_chebi(model, chebi, guess=True):
    species2chebi = {}
    s_type_id2chebi = {}
    unannotated = []

    # process species types
    for s_type in model.getListOfSpeciesTypes():
        has_chebi = next((annotation for annotation in get_is_annotations(s_type) if annotation.find('chebi') != -1),
                         None)
        t_id = find_term_id(s_type, chebi)
        if t_id:
            if not has_chebi:
                add_annotation(s_type, get_is_qualifier(), to_identifiers_org_format(t_id, "obo.chebi"))
            s_type_id2chebi[s_type.getId()] = t_id

    # process species
    for species in model.getListOfSpecies():
        has_chebi = next((annotation for annotation in get_is_annotations(species) if annotation.find('chebi') != -1),
                         None)
        s_type_id = species.getSpeciesType()
        if s_type_id and s_type_id in s_type_id2chebi:
            t_id = s_type_id2chebi[s_type_id]
        else:
            t_id = find_term_id(species, chebi)
        if t_id:
            species2chebi[species.getId()] = t_id
            if not has_chebi:
                add_annotation(species, get_is_qualifier(), to_identifiers_org_format(t_id, "obo.chebi"))
            if s_type_id and s_type_id not in s_type_id2chebi:
                s_type_id2chebi[s_type_id] = t_id
                add_annotation(model.getSpeciesType(s_type_id), get_is_qualifier(),
                               to_identifiers_org_format(t_id, "obo.chebi"))
        else:
            unannotated.append(species)
    s_t_id2unannotated = defaultdict(list)
    for species in unannotated:
        s_type_id = species.getSpeciesType()
        if s_type_id and s_type_id in s_type_id2chebi:
            t_id = s_type_id2chebi[s_type_id]
            species2chebi[species.getId()] = t_id
            add_annotation(species, get_is_qualifier(), to_identifiers_org_format(t_id, "obo.chebi"))
        else:
            if s_type_id:
                s_t_id2unannotated[s_type_id].append(species)
            else:
                s_t_id2unannotated[species.getId()].append(species)

    # annotate unannotated
    if guess:
        for s_t_id, species_list in s_t_id2unannotated.iteritems():
            s_type = model.getSpeciesType(s_t_id)
            name = ''
            if s_type:
                name = normalize(s_type.getName())
            if not name:
                species = species_list[0]
                c_name = normalize("[{0}]".format(model.getCompartment(species.getCompartment()).getName()))
                name = normalize(species.getName()).replace(c_name, '').strip()
            if not name:
                continue
            t_ids = chebi.get_ids_by_name(name)
            if not t_ids:
                continue
            t_id = t_ids.pop()
            for species in species_list:
                species2chebi[species.getId()] = t_id
                add_annotation(species, get_is_qualifier(), to_identifiers_org_format(t_id, "obo.chebi"))
            if s_type:
                add_annotation(s_type, get_is_qualifier(), to_identifiers_org_format(t_id, "obo.chebi"))
    return species2chebi
