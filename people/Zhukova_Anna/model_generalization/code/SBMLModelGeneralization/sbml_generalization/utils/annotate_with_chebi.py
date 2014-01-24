from libsbml import SBMLReader, Species
from misc import add_to_map
from obo_ontology import miriam_to_term_id, Term, to_identifiers_org_format
from sbml_generalization.generalization.rdf_annotation_helper import getAllQualifierValues, addAnnotation, \
    get_is_qualifier, get_is_vo_qualifier

__author__ = 'anna'


def get_is_annotations(entity):
    return (miriam_to_term_id(it) for it in getAllQualifierValues(entity.getAnnotation(), get_is_qualifier()))


def get_is_vo_annotations(entity):
    return (miriam_to_term_id(it) for it in getAllQualifierValues(entity.getAnnotation(), get_is_vo_qualifier()))


def get_term(entity, chebi):
    for is_annotation in get_is_annotations(entity):
        term = chebi.getTerm(is_annotation)
        if term:
            return term
    for is_vo_annotation in get_is_vo_annotations(entity):
        term = chebi.getTerm(is_vo_annotation)
        if term:
            return term
    return None


def normalize(name):
    return name.strip()


def get_names(entity):
    name = normalize(entity.getName())
    name_bis = name
    end = name_bis.find("(")
    if end != -1 and end != 0:
        name_bis = name_bis[0:end].strip()
    return name, name_bis


# This annotation is to be used in Tulip
def annotate_ubiquitous(model, species_id2chebi_id, ubiquitous_chebi_ids):
    for species in model.getListOfSpecies():
        s_id = species.getId()
        if (s_id in species_id2chebi_id) and (species_id2chebi_id[s_id] in ubiquitous_chebi_ids):
            st_id = species.getSpeciesType()
            if st_id:
                # species = model.getSpeciesType(st_id)
                st = model.getSpeciesType(st_id)
                st.setName(st.getName() + " ubiquitous")
                # species.appendNotes("<html:body><html:p>SUBSYSTEM: {0}</html:p></html:body>".format("ubiquitous"))
            # addAnnotation(species, BQB_IS_DESCRIBED_BY, "ubiquitous")
            species.setName(species.getName() + " ubiquitous")


def get_species_term(species, chebi, model):
    term = get_term(species, chebi)
    if not term:
        s_type_id = species.getSpeciesType()
        if s_type_id:
            s_type = model.getSpeciesType(s_type_id)
            if s_type:
                term = get_term(s_type, chebi)
    return term


def get_species_to_chebi(model, chebi):

    species2chebi = {}
    used_terms = set()
    entity2species = {}

    # process annotated ones
    # and find those that need to be annotated
    for species in model.getListOfSpecies():
        term = get_term(species, chebi)
        entity = species
        if not term:
            s_type_id = species.getSpeciesType()
            if s_type_id:
                s_type = model.getSpeciesType(s_type_id)
                if s_type:
                    entity = s_type
                    term = get_term(s_type, chebi)
        if term:
            species2chebi[species.getId()] = term.getId()
            used_terms.add(term)
            continue
        else:
            add_to_map(entity2species, entity, species)
    i = 0
    # annotate unannotated
    fake_terms = set()
    for entity, species_set in entity2species.iteritems():
        name, name_bis = get_names(entity)
        if isinstance(entity, Species):
            index = name.find("[{0}]".format(model.getCompartment(entity.getCompartment()).getName()))
            if -1 != index:
                name = name[:index].strip()
        possibilities = chebi.getIdsByName(name)
        if not possibilities:
            possibilities = chebi.getIdsByName(name_bis)
        if not possibilities:
            # #if entity.getName().find("protein") == -1: print entity.getName(), entity.getId()
            # while chebi.getTerm("chebi:unknown_{0}".format(i)):
            #     i += 1
            # term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
            # term.addSynonym(name_bis)
            # chebi.addTerm(term)
            # fake_terms.add(term)
            # used_terms.add(term)
            # for species in species_set:
            #     species2chebi[species.getId()] = term.getId()
            continue
        possibilities = {chebi.getTerm(it) for it in possibilities}
        intersection = possibilities & used_terms
        term = intersection.pop() if intersection else possibilities.pop()
        for species in species_set:
            species2chebi[species.getId()] = term.getId()
        addAnnotation(entity, get_is_qualifier(), to_identifiers_org_format(term.getId()))
        used_terms.add(term)
    return species2chebi, fake_terms
