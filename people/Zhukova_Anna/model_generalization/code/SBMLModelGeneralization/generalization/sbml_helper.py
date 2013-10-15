from libsbml import *
from utils.annotate_with_chebi import get_term
from utils.logger import log
from utils.misc import add_to_map, invert_map
from utils.obo_ontology import addMiriamPrefix, removeMiriamPrefix
from generalization.rdf_annotation_helper import addAnnotation, getAllQualifierValues
from generalization.reaction_filters import getProducts, getReactants, get_compartment, getReactionParticipants

GROUP_TYPE_EQUIV = "equivalent"

GROUP_TYPE_CHAIN = "chain"

GROUP_TYPE_UBIQUITOUS = "ubiquitous"

SBO_CHEMICAL_MACROMOLECULE = "SBO:0000248"

SBO_BIOCHEMICAL_REACTION = "SBO:0000176"

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
    return t.lower().replace("-", "_").replace(":", "_").replace("(", "_").replace(")", "_").replace("[", "_") \
        .replace("]", "_").replace("'", "_").replace("/", "_").replace(",", "_").replace("\"", "_").replace(" ", "_") \
        .replace(".", "_").replace("%3a", "_").replace("%3A", "_").replace("=", "_").replace("{", "_") \
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


# serialization


def convert_to_lev3_v1(model):
    doc = SBMLDocument(model.getSBMLNamespaces())
    doc.setModel(model)
    doc.setConsistencyChecksForConversion(LIBSBML_CAT_GENERAL_CONSISTENCY, False)
    doc.setConsistencyChecksForConversion(LIBSBML_CAT_IDENTIFIER_CONSISTENCY, False)
    doc.setConsistencyChecksForConversion(LIBSBML_CAT_UNITS_CONSISTENCY, False)
    doc.setConsistencyChecksForConversion(LIBSBML_CAT_MATHML_CONSISTENCY, False)
    doc.setConsistencyChecksForConversion(LIBSBML_CAT_SBO_CONSISTENCY, False)
    doc.setConsistencyChecksForConversion(LIBSBML_CAT_OVERDETERMINED_MODEL, False)
    doc.setConsistencyChecksForConversion(LIBSBML_CAT_MODELING_PRACTICE, False)
    doc.checkL3v1Compatibility()
    doc.setLevelAndVersion(3, 1, False)
    doc.getSBMLNamespaces().addPackageNamespace("groups", 1)
    return doc


def model_to_l3v1(sbml, model):
    doc = convert_to_lev3_v1(Model(model))
    writeSBMLToFile(doc, sbml)


def annotate_ubiquitous(groups_sbml, species_id2chebi_id, ubiquitous_chebi_ids, verbose=False):
    if groups_sbml:
        log(verbose, "saving ubiquitous species annotations...")
        doc = SBMLReader().readSBMLFromFile(groups_sbml)
        groups_model = doc.getModel()
        groups_plugin = groups_model.getPlugin("groups")
        s_group = groups_plugin.createGroup()
        s_group.setId("g_ubiquitous_sps")
        s_group.setKind(GROUP_KIND_COLLECTION)
        s_group.setSBOTerm(SBO_CHEMICAL_MACROMOLECULE)
        s_group.setName("ubiquitous species")
        for s in groups_model.getListOfSpecies():
            s_id = s.getId()
            if s_id in species_id2chebi_id and species_id2chebi_id[s_id] in ubiquitous_chebi_ids:
                member = s_group.createMember()
                member.setSymbol(s_id)
        addAnnotation(s_group, BQB_IS_DESCRIBED_BY, GROUP_TYPE_UBIQUITOUS)
        save_as_sbml(groups_model, groups_sbml, verbose)


def save_as_generalized_sbml(input_model, out_sbml, groups_sbml, r2clu, s_id2clu, verbose):
    log(verbose, "serializing generalization...")
    # generalized model
    generalized_doc = SBMLDocument(input_model.getSBMLNamespaces())
    clu2rs = invert_map(r2clu)
    if not s_id2clu:
        generalized_model = input_model
    else:
        generalized_model = generalized_doc.createModel()
        copyElements(input_model, generalized_model)

        #convert
        if groups_sbml:
            doc = SBMLReader().readSBMLFromFile(groups_sbml)
            groups_model = doc.getModel()
            groups_plugin = groups_model.getPlugin("groups")

        i = 0
        s_id2clu = {s_id: clu for (s_id, clu) in s_id2clu.iteritems()}
        clu2s_ids = invert_map(s_id2clu)
        for clu, species_ids in clu2s_ids.iteritems():
            comp2s_ids = {}
            for s_id in species_ids:
                species = input_model.getSpecies(s_id)
                c_id = species.getCompartment()
                add_to_map(comp2s_ids, c_id, s_id)
            for c_id, s_ids in comp2s_ids.iteritems():
                if len(s_ids) > 1:
                    new_species = createSpecies(generalized_model, c_id, type_id=None,
                                                name="{0} ({1})".format(clu.getName(), len(s_ids)))
                    addAnnotation(new_species, BQB_IS, addMiriamPrefix(clu.getId()))
                    for s_id in s_ids:
                        s_id2clu[s_id] = new_species.getId()

                    if groups_sbml and groups_plugin:
                        # save as a group
                        s_group = groups_plugin.createGroup()
                        s_group.setId(new_species.getId())
                        s_group.setKind(GROUP_KIND_CLASSIFICATION)
                        s_group.setSBOTerm(SBO_CHEMICAL_MACROMOLECULE)
                        s_group.setName(clu.getName())
                        addAnnotation(s_group, BQB_IS, addMiriamPrefix(clu.getId()))
                        for s_id in s_ids:
                            member = s_group.createMember()
                            member.setSymbol(s_id)
                        addAnnotation(s_group, BQB_IS_DESCRIBED_BY, GROUP_TYPE_EQUIV)

                else:
                    del s_id2clu[s_ids.pop()]

        generalize_species = lambda species_id: s_id2clu[species_id] if (species_id in s_id2clu) else species_id
        s_id_to_generalize = set(s_id2clu.keys())
        for clu, r_set in clu2rs.iteritems():
            comp2rs = {}
            for r in r_set:
                c_id = get_compartment(r, input_model)
                add_to_map(comp2rs, c_id, r)
            for c_id, rs in comp2rs.iteritems():
                representative = list(rs)[0]
                reactants = getReactants(representative)
                products = getProducts(representative)
                if (len(rs) == 1) and not ((reactants | products) & s_id_to_generalize):
                    generalized_model.addReaction(representative)
                else:
                    reactants = {generalize_species(it) for it in reactants}
                    products = {generalize_species(it) for it in products}
                    r_name = representative.getName()
                    if len(rs) > 1:
                        r_name = "{0} ({1})".format(r_name, len(rs))

                        if groups_sbml and groups_plugin:
                            # save as a group
                            r_group = groups_plugin.createGroup()
                            r_group.setId("g_r_{0}".format(i))
                            r_group.setKind(GROUP_KIND_COLLECTION)
                            r_group.setSBOTerm(SBO_BIOCHEMICAL_REACTION)
                            r_group.setName("generalized {0}".format(representative.getName()))
                            for r in rs:
                                member = r_group.createMember()
                                member.setSymbol(r.getId())
                            addAnnotation(r_group, BQB_IS_DESCRIBED_BY, GROUP_TYPE_EQUIV)

                    createReaction(generalized_model, reactants, products, r_name)

        removeUnusedElements(generalized_model)

        if groups_sbml and groups_model:
            save_as_sbml(groups_model, groups_sbml, verbose)
        save_as_sbml(generalized_model, out_sbml, verbose)


def save_as_sbml(input_model, out_sbml, verbose=True):
    log(verbose, "saving to {0}...".format(out_sbml))
    out_doc = SBMLDocument(input_model.getSBMLNamespaces())
    out_doc.setModel(input_model)
    writeSBMLToFile(out_doc, out_sbml)


def save_as_chain_shortened_sbml(chains, input_model, out_sbml, groups_sbml, verbose):
    log(verbose, "serializing chain shortening...")
    # chain shortened model
    cs_doc = SBMLDocument(input_model.getSBMLNamespaces())
    cs_model = cs_doc.createModel()
    copyElements(input_model, cs_model)

    # convert
    if groups_sbml:
        doc = SBMLReader().readSBMLFromFile(groups_sbml)
        groups_model = doc.getModel()
        groups_plugin = groups_model.getPlugin("groups")

    processed_rs = set()
    for chain in chains:
        species_chain, k, reaction_chain = chain
        processed_rs |= set(reaction_chain)
        r = input_model.getReaction(reaction_chain[0])
        # replace the second species in the chain with the last one
        id_replacer = lambda s_id: species_chain[-1] if s_id == species_chain[1] else s_id
        reactants = {id_replacer(it) for it in getReactants(r)}
        products = {id_replacer(it) for it in getProducts(r)}
        rn = createReaction(cs_model, reactants, products, "{0}{1}".format("shortened chain: ", r.getName()))

        if groups_sbml and groups_plugin:
            # save as a group
            r_group = groups_plugin.createGroup()
            r_group.setId(rn.getId())
            r_group.setKind(GROUP_KIND_COLLECTION)
            r_group.setSBOTerm(SBO_BIOCHEMICAL_REACTION)
            r_group.setName(rn.getName())
            for r_id in reaction_chain:
                r = input_model.getReaction(r_id)
                member = r_group.createMember()
                member.setSymbol(r.getId())
            addAnnotation(r_group, BQB_IS_DESCRIBED_BY, GROUP_TYPE_CHAIN)

    for r in input_model.getListOfReactions():
        if not r.getId() in processed_rs:
            cs_model.addReaction(r)

    removeUnusedElements(cs_model)

    if groups_sbml and groups_model:
        save_as_sbml(groups_model, groups_sbml, verbose)

    save_as_sbml(cs_model, out_sbml, verbose)


def parse_group_sbml(groups_sbml, chebi):
    doc = SBMLReader().readSBMLFromFile(groups_sbml)
    groups_model = doc.getModel()
    groups_plugin = groups_model.getPlugin("groups")
    id2rns_eq, id2rns_ch, id2sps = {}, {}, {}
    ub_sps = []
    if groups_plugin:
        for group in groups_plugin.getListOfGroups():
            gr_members = [it.getSymbol() for it in group.getListOfMembers()]
            gr_id, gr_name = group.getId(), group.getName()
            gr_sbo, gr_type = group.getSBOTermID(), getAllQualifierValues(group.getAnnotation(), BQB_IS_DESCRIBED_BY).pop()
            if SBO_BIOCHEMICAL_REACTION == gr_sbo:
                if GROUP_TYPE_CHAIN == gr_type:
                    id2rns_ch[(gr_id, gr_name,)] = gr_members
                elif GROUP_TYPE_EQUIV == gr_type:
                    id2rns_eq[(gr_id, gr_name,)] = gr_members
            elif SBO_CHEMICAL_MACROMOLECULE == gr_sbo:
                if GROUP_TYPE_UBIQUITOUS == gr_type:
                    ub_sps = gr_members
                elif GROUP_TYPE_EQUIV == gr_type:
                    id2sps[(gr_id, gr_name, get_term(group, chebi), )] = gr_members

    return id2rns_eq, id2rns_ch, id2sps, ub_sps


