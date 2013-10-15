from misc import add_to_map
from obo_ontology import removeMiriamPrefix, Term, addMiriamPrefix
from generalization.rdf_annotation_helper import getAllQualifierValues, addAnnotation
from generalization.sbml_helper import get_is_qualifier

__author__ = 'anna'


def getIsAnnotations(entity):
    isResources = getAllQualifierValues(entity.getAnnotation(), get_is_qualifier())
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
    end = name_bis.find("(")
    if end != -1 and end != 0:
        name_bis = name_bis[0:end].strip()
    return name, name_bis

# This annotation is to be used in Tulip
def annotateUbiquitous(model, species_id2chebi_id, ubiquitous_chebi_ids):
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


def getSpeciesTerm(species, chebi, model):
    term = getTerm(species, chebi)
    if not term:
        s_type_id = species.getSpeciesType()
        if s_type_id:
            s_type = model.getSpeciesType(s_type_id)
            if s_type:
                term = getTerm(s_type, chebi)
    return term


def getSpecies2chebi(model, chebi):
    species2chebi = {}
    usedTerms = set()
    entity2species = {}

    # process annotated ones
    # and find those that need to be annotated
    for species in model.getListOfSpecies():
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
            species2chebi[species.getId()] = term.getId()
            usedTerms.add(term)
            continue
        else:
            add_to_map(entity2species, entity, species)
    i = 0
    # annotate unannotated
    fake_terms = set()
    for entity, species_set in entity2species.iteritems():
        name, name_bis = getNames(entity)
        possibilities = chebi.getIdsByName(name)
        if not possibilities:
            possibilities = chebi.getIdsByName(name_bis)
        if not possibilities:
            while chebi.getTerm("chebi:unknown_{0}".format(i)):
                i += 1
            term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
            term.addSynonym(name_bis)
            chebi.addTerm(term)
            fake_terms.add(term)
            usedTerms.add(term)
            for species in species_set:
                species2chebi[species.getId()] = term.getId()
            continue
        possibilities = {chebi.getTerm(it) for it in possibilities}
        options = set()
        for it in possibilities:
            options.add(it)
        intersection = options & usedTerms
        term = intersection.pop() if intersection else possibilities.pop()
        for species in species_set:
            species2chebi[species.getId()] = term.getId()
        addAnnotation(entity, get_is_qualifier(), addMiriamPrefix(term.getId()))
        usedTerms.add(term)
    return species2chebi, fake_terms
