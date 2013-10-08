from libsbml import LIBSBML_OPERATION_SUCCESS, UnitDefinition, Parameter, Compartment, SpeciesType, \
    Species, Reaction, SpeciesReference, BQB_IS
from utils.ontology import addMiriamPrefix
from utils.rdf_annotation_helper import addAnnotation
from utils.reaction_filters import getReactionParticipants

DIMENSIONLESS_UNIT = "dimensionless"

SBO_MATERIAL_ENTITY = "SBO:0000240"

__author__ = 'anna'


def copyUnitDefinition(model, prototype, id_=None):
    if prototype:
        id_ = generateUniqueId(model, id_ if id_ else "u_new")
        unit_def = UnitDefinition(prototype)
        unit_def.setId(id_)
        model.addUnitDefinition(unit_def)


def copyCompartment(model, prototype, compartment_id_old2new, id_=None):
    if prototype:
        id_ = generateUniqueId(model, id_ if id_ else "c_new")
        comp = Compartment(prototype)
        comp.setId(id_)
        if prototype.isSetOutside():
            old_outside = prototype.getOutside()
            if old_outside and old_outside in compartment_id_old2new:
                comp.setOutside(compartment_id_old2new[old_outside])
        model.addCompartment(comp)


def copySpecies(model, prototype, compartment_id, type_id=None, id_=None):
    if prototype:
        id_ = generateUniqueId(model, id_ if id_ else "s_new")

        species = Species(prototype)
        species.setId(id_)
        if compartment_id:
            species.setCompartment(compartment_id)
        if type_id:
            species.setSpeciesType(type_id)
            # TODO: improve
        # To avoid errors derived from SBML version differences:
        # In SBML Level 2 prior to Version 4 it is expected to refer to a participant physical type
        # (i.e., terms derived from SBO:0000236, "participant physical type");
        # in Versions 4 and above it is expected to refer to a material entity
        # (i.e., terms derived from SBO:0000240, "material entity").
        # we will just use SBO:0000240 for now
        species.setSBOTerm(SBO_MATERIAL_ENTITY)

        model.addSpecies(species)


def copyParameter(model, prototype, unit_id_old2new, id_=None):
    if prototype:
        id_ = generateUniqueId(model, id_ if id_ else "p_new")
        param = Parameter(prototype)
        param.setId(id_)
        old_unit_id = prototype.getUnits()
        if old_unit_id and old_unit_id in unit_id_old2new:
            param.setUnits(unit_id_old2new[old_unit_id])
        model.addParameter(param)


def copyElements(inputModel, outputModel):
    outputModel.setId(inputModel.getId())
    outputModel.setNamespaces(inputModel.getNamespaces())
    for unit in inputModel.getListOfUnitDefinitions():
        outputModel.addUnitDefinition(unit)
    for parameter in inputModel.getListOfParameters():
        outputModel.addParameter(parameter)
    for compartment in inputModel.getListOfCompartments():
        outputModel.addCompartment(compartment)
    for speciesType in inputModel.getListOfSpeciesTypes():
        outputModel.addSpeciesType(speciesType)
    for species in inputModel.getListOfSpecies():
        outputModel.addSpecies(species)


def removeUnusedElements(outputModel):
    speciesToKeep = []
    for reaction in outputModel.getListOfReactions():
        speciesToKeep.extend(getReactionParticipants(reaction))
    sp_list = list(outputModel.getListOfSpecies())
    for species in sp_list:
        speciesId = species.getId()
        if not (speciesId in speciesToKeep):
            outputModel.removeSpecies(speciesId)
    compartmentsToKeep = set()
    for species in outputModel.getListOfSpecies():
        compartmentId = species.getCompartment()
        compartmentsToKeep.add(compartmentId)
        outer_compartment = outputModel.getCompartment(compartmentId).getOutside()
        while outer_compartment:
            compartmentsToKeep.add(outer_compartment)
            outer_compartment = outputModel.getCompartment(outer_compartment).getOutside()
    c_list = list(outputModel.getListOfCompartments())
    for compartment in c_list:
        compartmentId = compartment.getId()
        if not (compartmentId in compartmentsToKeep):
            outputModel.removeCompartment(compartmentId)


# TODO: improve
def normalize(t):
    if isinstance(t, tuple):
        t = ''.join(flatten(t))
    return t.lower().replace("-", "_").replace(":", "_").replace("(", "_").replace(")", "_").replace("[", "_")\
        .replace("]", "_").replace("'", "_").replace("/", "_").replace(",", "_").replace("\"", "_").replace(" ", "_")\
        .replace(".", "_").replace("%3a", "_").replace("%3A", "_").replace("=", "_").replace("{", "_")\
        .replace("}", "_").replace("+", "_").replace(">", "_")


def flatten(t):
    if not isinstance(t, tuple):
        return t,
    elif not len(t):
        return ()
    else:
        return flatten(t[0]) + flatten(t[1:])


def generateUniqueId(model, id_=None):
    if not id_:
        id_ = "new_id"
    id_ = normalize(id_)
    i = 0
    old_id = id_
    while model.getElementBySId(id_):
        id_ = "{0}_{1}".format(old_id, i)
        i += 1
    return id_


def copySpeciesType(model, id_, prototype):
    if prototype:
        id_ = generateUniqueId(model, id_ if id_ else "t_new")
        sp_type = SpeciesType(prototype)
        sp_type.setId(id_)
        model.addSpeciesType(sp_type)


def createSpeciesType(model, name, term_id=None, id_=None):
    new_type = model.createSpeciesType()
    id_ = generateUniqueId(model, id_ if id_ else "t_new")
    new_type.setId(id_)
    new_type.setName(name)
    if term_id:
        addAnnotation(new_type, BQB_IS, addMiriamPrefix(term_id))
    return new_type


def createSpecies(model, compartment_id, type_id=None, name=None, id_=None, sbo_id=None):
    new_species = model.createSpecies()
    id_ = generateUniqueId(model, id_ if id_ else "s_new")
    if LIBSBML_OPERATION_SUCCESS != new_species.setId(id_):
        print "species  ", id_, " creation error"
    if not name:
        if type_id:
            s_type = model.getSpeciesType(type_id)
            if s_type:
                type_name = s_type.getName()
                if type_name:
                    name = type_name
        if compartment_id:
            compartment = model.getCompartment(compartment_id)
            if compartment:
                compartment_name = compartment.getName()
                if compartment_name:
                    name = "{0} [{1}]".format(name, compartment_name)
    new_species.setName(name)
    new_species.setCompartment(compartment_id)
    if type_id:
        new_species.setSpeciesType(type_id)
    new_species.setSBOTerm(sbo_id if sbo_id else SBO_MATERIAL_ENTITY)
    return new_species


def createReaction(model, reactants, products, name=None, id_=None):
    reaction = model.createReaction()
    id_ = generateUniqueId(model, id_ if id_ else "r_new")
    if LIBSBML_OPERATION_SUCCESS != reaction.setId(id_):
        print "reaction  ", id_, " creation error"
    for sp_id in reactants:
        reactant = model.createReactant()
        reactant.setSpecies(sp_id)
    for sp_id in products:
        product = model.createProduct()
        product.setSpecies(sp_id)
    if name:
        reaction.setName(name)
    return reaction


def _copySpeciesReference(spRef, species_id_replacement_map):
    sp_id = spRef.getSpecies()
    new_spRef = SpeciesReference(spRef)
    new_spRef.setStoichiometry(spRef.getStoichiometry())
    if sp_id in species_id_replacement_map:
        new_spRef.setSpecies(species_id_replacement_map[sp_id])
    return new_spRef


def copyReaction(model, prototype, species_id_old2new, param_id_old2new, unit_id_old2new, name=None,
                 compartment_id=None, id_=None):
    new_reaction = Reaction(prototype)
    id_ = generateUniqueId(model, id_ if id_ else "r_new")
    new_reaction.setId(id_)
    if compartment_id:
        new_reaction.setCompartment(compartment_id)
    if name:
        new_reaction.setName(name)

    if new_reaction.isSetKineticLaw():
        kin_law = new_reaction.getKineticLaw()
        for iterable in kin_law.getListOfParameters(), kin_law.getListOfLocalParameters():
            for param in iterable:
                param_id = param.getId()
                if param_id in param_id_old2new:
                    param.setId(param_id_old2new[param_id])
                if param.isSetUnits():
                    old_unit_id = param.getUnits()
                    if old_unit_id and old_unit_id in unit_id_old2new:
                        param.setUnits(unit_id_old2new[old_unit_id])
    for spRef_iterable in prototype.getListOfReactants(), prototype.getListOfProducts(), prototype.getListOfModifiers():
        for spRef in spRef_iterable:
            new_spRef = _copySpeciesReference(spRef, species_id_old2new)
            new_reaction.addReactant(new_spRef)

    model.addReaction(new_reaction)
    return new_reaction

def remove_is_a_reactions(input_model):
    to_remove = []
    for reaction in input_model.getListOfReactions():
        if 1 == reaction.getNumReactants() == reaction.getNumProducts():  # and reaction.getName().find("isa ") != -1:
            to_remove.append(reaction.getId())
    for r_id in to_remove:
        input_model.removeReaction(r_id)