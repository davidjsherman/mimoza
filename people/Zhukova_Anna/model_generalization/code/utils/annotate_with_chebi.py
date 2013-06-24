from libsbml import BQB_IS
from utils.ontology import removeMiriamPrefix, addMiriamPrefix
from utils.rdf_annotation_helper import addAnnotation, getAllQualifierValues

__author__ = 'anna'


def getIsAnnotations(entity):
    isResources = getAllQualifierValues(entity.getAnnotation(), BQB_IS)
    return [removeMiriamPrefix(it) for it in isResources]


def getTerm(entity, chebi):
    for is_annotation in getIsAnnotations(entity):
        term = chebi.getTerm(is_annotation)
        if term:
            return term
    return None


def normalize(name):
    end = name.find("[")
    if end == -1:
        end = name.find("_")
    if end != -1:
        name = name[:end]
    return name.strip()


def getNames(entity):
    name = normalize(entity.getName())
    name_bis = name
    end = name.find("(")
    if end != -1:
        name_bis = name_bis[0:end].strip()
    return name, name_bis


def getSpecies2chebi_id(model, species_list, chebi):
    species2chebi_id = {}
    usedTerms = set()
    species2entity = {}
    for species in species_list:
        term = getTerm(species, chebi)
        entity = species
        if not term:
            s_type_id = species.getSpeciesType()
            if s_type_id:
                s_type = model.getSpeciesType(s_type_id)
                if s_type:
                    entity = s_type
                    term = getTerm(s_type, chebi)
        if term:
            species2chebi_id[species.getId()] = term.getId()
            usedTerms.add(term)
            continue
        else:
            species2entity[species] = entity
    for species, entity in species2entity.iteritems():
        name, name_bis = getNames(entity)
        possibilities = chebi.getIdsByName(name)
        if not possibilities:
            possibilities = chebi.getIdsByName(name_bis)
        if not possibilities:
            continue
        possibilities = {chebi.getTerm(it) for it in possibilities}
        options = set()
        for it in possibilities:
            options.add(it)
            options |= chebi.getEqualTerms(it)
        intersection = options & usedTerms
        term = intersection.pop() if intersection else possibilities.pop()
        species2chebi_id[species.getId()] = term.getId()
        addAnnotation(entity, BQB_IS, addMiriamPrefix(term.getId()))
        usedTerms.add(term)
    return species2chebi_id
