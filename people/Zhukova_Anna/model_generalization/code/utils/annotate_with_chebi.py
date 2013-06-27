from libsbml import BQB_IS
from utils.misc import add2map
from utils.ontology import removeMiriamPrefix, addMiriamPrefix, Term
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


def getSpecies2chebi(model, species_list, chebi):
    # a fake term to annotate species
    # for which we'll not find any term in ChEBI
    unknown = Term(t_id="chebi:unknown", name="unknown")

    species2chebi = {}
    usedTerms = set()
    entity2species = {}

    # process annotated ones
    # and find those that need to be annotated
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
            species2chebi[species.getId()] = term
            usedTerms.add(term)
            continue
        else:
            add2map(entity2species, entity, species)
    i = 0
    # annotate unannotated
    for entity, species_set in entity2species.iteritems():
        name, name_bis = getNames(entity)
        possibilities = chebi.getIdsByName(name)
        if not possibilities:
            possibilities = chebi.getIdsByName(name_bis)
        if not possibilities:
            term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
            i += 1
            term.addSynonym(name_bis)
            chebi.addTerm(term)
            usedTerms.add(term)
            for species in species_set:
                species2chebi[species.getId()] = term
            continue
        possibilities = {chebi.getTerm(it) for it in possibilities}
        options = set()
        for it in possibilities:
            options.add(it)
        intersection = options & usedTerms
        term = intersection.pop() if intersection else possibilities.pop()
        for species in species_set:
            species2chebi[species.getId()] = term
            print species.getName(), term.getName()
        addAnnotation(entity, BQB_IS, addMiriamPrefix(term.getId()))
        usedTerms.add(term)

    return species2chebi
