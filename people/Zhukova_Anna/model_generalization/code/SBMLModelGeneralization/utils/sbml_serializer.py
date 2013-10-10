from libsbml import *
from utils.logger import log
from utils.misc import invert, add2map
from utils.ontology import addMiriamPrefix
from utils.rdf_annotation_helper import addAnnotation
from utils.reaction_filters import getReactants, getProducts, get_compartment
from utils.sbml_creation_helper import createReaction, removeUnusedElements, createSpecies, copyElements

__author__ = 'anna'


def convert_to_chain_shortened_model(chain_shortened_model, input_model, chains):
    processed_rs = set()
    for chain in chains:
        species_chain, k, reaction_chain = chain
        processed_rs |= set(reaction_chain)
        r = input_model.getReaction(reaction_chain[0])
        # replace the second species in the chain with the last one
        id_replacer = lambda s_id: species_chain[-1] if s_id == species_chain[1] else s_id
        reactants = {id_replacer(it) for it in getReactants(r)}
        products = {id_replacer(it) for it in getProducts(r)}
        createReaction(chain_shortened_model, reactants, products, "{0}{1}".format("shortened chain: ", r.getName()))
    for r in input_model.getListOfReactions():
        if not r.getId() in processed_rs:
            chain_shortened_model.addReaction(r)
    removeUnusedElements(chain_shortened_model)


def convert_to_generalized_model(generalized_model, input_model, sp_id2clu, clu2rs):
    s_id2clu = {s_id: clu for (s_id, clu) in sp_id2clu.iteritems()}
    clu2s_ids = invert(s_id2clu)
    for clu, species_ids in clu2s_ids.iteritems():
        comp2s_ids = {}
        for s_id in species_ids:
            species = input_model.getSpecies(s_id)
            c_id = species.getCompartment()
            add2map(comp2s_ids, c_id, s_id)
        for c_id, s_ids in comp2s_ids.iteritems():
            if len(s_ids) > 1:
                new_species = createSpecies(generalized_model, c_id, type_id=None,
                                            name="{0} ({1})".format(clu.getName(), len(s_ids)))
                addAnnotation(new_species, BQB_IS, addMiriamPrefix(clu.getId()))
                for s_id in s_ids:
                    s_id2clu[s_id] = new_species.getId()
            else:
                del s_id2clu[s_ids.pop()]

    generalize_species = lambda species_id: s_id2clu[species_id] if (species_id in s_id2clu) else species_id
    s_id_to_generalize = set(s_id2clu.keys())
    for clu, r_set in clu2rs.iteritems():
        comp2rs = {}
        for r in r_set:
            c_id = get_compartment(r, input_model)
            add2map(comp2rs, c_id, r)
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
                createReaction(generalized_model, reactants, products, r_name)
    removeUnusedElements(generalized_model)


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


def convert_to_groups_model(doc, s_id2clu, clu2rs):
    model = doc.getModel()
    groups_plugin = model.getPlugin("groups")
    clu2s_ids = invert(s_id2clu)
    i = 0
    for clu, species_ids in clu2s_ids.iteritems():
        comp2s_ids = {}
        for s_id in species_ids:
            species = model.getSpecies(s_id)
            c_id = species.getCompartment()
            add2map(comp2s_ids, c_id, s_id)
        for c_id, s_ids in comp2s_ids.iteritems():
            if len(s_ids) > 1:
                s_group = groups_plugin.createGroup()
                s_group.setId("g_s_{0}".format(i))
                s_group.setKind(GROUP_KIND_CLASSIFICATION)
                s_group.setSBOTerm("SBO:0000252")
                s_group.setName(clu.getName())
                addAnnotation(s_group, BQB_IS, addMiriamPrefix(clu.getId()))
                for s_id in s_ids:
                    member = s_group.createMember()
                    member.setSymbol(s_id)
    i = 0
    for clu, r_set in clu2rs.iteritems():
        comp2rs = {}
        for r in r_set:
            c_id = get_compartment(r, model)
            add2map(comp2rs, c_id, r)
        for c_id, rs in comp2rs.iteritems():
            if len(rs) > 1:
                representative = list(rs)[0]
                r_group = groups_plugin.createGroup()
                r_group.setId("g_r_{0}".format(i))
                r_group.setKind(GROUP_KIND_COLLECTION)
                r_group.setSBOTerm("SBO:0000176")
                r_group.setName("generalized {0}".format(representative.getName()))
                for r in rs:
                    member = r_group.createMember()
                    member.setSymbol(r.getId())
    return doc


def save_as_groups_sbml(clu2rs, groups_sbml, input_model, reader, s_id2clu, verbose):
    log(verbose, "saving to {0}...".format(groups_sbml))
    groups_doc = convert_to_lev3_v1(Model(input_model))
    writeSBMLToFile(groups_doc, groups_sbml)
    groups_doc = reader.readSBMLFromFile(groups_sbml)
    groups_doc = convert_to_groups_model(groups_doc, s_id2clu, clu2rs)
    writeSBMLToFile(groups_doc, groups_sbml)


def save_as_generalized_sbml(input_model, out_sbml, r2clu, s_id2clu, verbose):
    log(verbose, "saving to {0}...".format(out_sbml))
    # generalized model
    generalized_doc = SBMLDocument(input_model.getSBMLNamespaces())
    clu2rs = invert(r2clu)
    if not s_id2clu:
        generalized_model = input_model
    else:
        generalized_model = generalized_doc.createModel()
        copyElements(input_model, generalized_model)
        convert_to_generalized_model(generalized_model, input_model, s_id2clu, clu2rs)
    out_doc = SBMLDocument(input_model.getSBMLNamespaces())
    out_doc.setModel(generalized_model)
    writeSBMLToFile(out_doc, out_sbml)


def update_initial_sbml(input_model, out_sbml, verbose):
    log(verbose, "saving to {0}...".format(out_sbml))
    out_doc = SBMLDocument(input_model.getSBMLNamespaces())
    out_doc.setModel(input_model)
    writeSBMLToFile(out_doc, out_sbml)


def save_as_chain_shortened_sbml(chains, input_model, verbose):
    log(verbose, "serializing chain shortening...")
    # chain shortened model
    cs_doc = SBMLDocument(input_model.getSBMLNamespaces())
    cs_model = cs_doc.createModel()
    copyElements(input_model, cs_model)
    convert_to_chain_shortened_model(cs_model, input_model, chains)
    return cs_model
