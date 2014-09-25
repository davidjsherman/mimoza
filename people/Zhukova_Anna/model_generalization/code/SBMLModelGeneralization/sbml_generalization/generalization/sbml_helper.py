import logging

from libsbml import *

from sbml_generalization.utils.annotate_with_chebi import get_term
from sbml_generalization.utils.logger import log
from sbml_generalization.utils.misc import invert_map
from sbml_generalization.utils.obo_ontology import to_identifiers_org_format
from rdf_annotation_helper import add_annotation, get_qualifier_values
from reaction_filters import get_products, get_reactants, get_participants


GROUP_TYPE_EQUIV = "equivalent"

GROUP_TYPE_CHAIN = "chain"

GROUP_TYPE_UBIQUITOUS = "ubiquitous"

SBO_CHEMICAL_MACROMOLECULE = "SBO:0000248"

SBO_BIOCHEMICAL_REACTION = "SBO:0000176"

DIMENSIONLESS_UNIT = "dimensionless"

SBO_MATERIAL_ENTITY = "SBO:0000240"

__author__ = 'anna'


def copy_unit_definition(model, prototype, id_=None):
	if prototype:
		id_ = generate_unique_id(model, id_ if id_ else "u_new")
		unit_def = UnitDefinition(prototype)
		unit_def.setId(id_)
		model.addUnitDefinition(unit_def)


def copy_compartment(model, prototype, compartment_id_old2new, id_=None):
	if prototype:
		id_ = generate_unique_id(model, id_ if id_ else "c_new")
		comp = Compartment(prototype)
		comp.setId(id_)
		if prototype.isSetOutside():
			old_outside = prototype.getOutside()
			if old_outside and old_outside in compartment_id_old2new:
				comp.setOutside(compartment_id_old2new[old_outside])
		model.addCompartment(comp)


def copy_species(model, prototype, compartment_id, type_id=None, id_=None):
	if prototype:
		id_ = generate_unique_id(model, id_ if id_ else "s_new")

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


def copy_parameter(model, prototype, unit_id_old2new, id_=None):
	if prototype:
		id_ = generate_unique_id(model, id_ if id_ else "p_new")
		param = Parameter(prototype)
		param.setId(id_)
		old_unit_id = prototype.getUnits()
		if old_unit_id and old_unit_id in unit_id_old2new:
			param.setUnits(unit_id_old2new[old_unit_id])
		model.addParameter(param)


def copy_elements(input_model, output_model):
	output_model.setId(input_model.getId())
	output_model.setNamespaces(input_model.getNamespaces())
	for unit in input_model.getListOfUnitDefinitions():
		output_model.addUnitDefinition(unit)
	for parameter in input_model.getListOfParameters():
		output_model.addParameter(parameter)
	for compartment in input_model.getListOfCompartments():
		output_model.addCompartment(compartment)
	for speciesType in input_model.getListOfSpeciesTypes():
		output_model.addSpeciesType(speciesType)
	for species in input_model.getListOfSpecies():
		output_model.addSpecies(species)


def remove_unused_elements(output_model):
	species_to_keep = []
	for reaction in output_model.getListOfReactions():
		species_to_keep.extend(get_participants(reaction))
	sp_list = list(output_model.getListOfSpecies())
	for species in sp_list:
		species_id = species.getId()
		if not (species_id in species_to_keep):
			output_model.removeSpecies(species_id)
	compartments_to_keep = set()
	for species in output_model.getListOfSpecies():
		compartment_id = species.getCompartment()
		compartments_to_keep.add(compartment_id)
		outer_compartment = output_model.getCompartment(compartment_id).getOutside()
		while outer_compartment:
			compartments_to_keep.add(outer_compartment)
			outer_compartment = output_model.getCompartment(outer_compartment).getOutside()
	c_list = list(output_model.getListOfCompartments())
	for compartment in c_list:
		compartment_id = compartment.getId()
		if not (compartment_id in compartments_to_keep):
			output_model.removeCompartment(compartment_id)


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


def generate_unique_id(model, id_=None):
	if not id_:
		id_ = "new_id"
	if not model.getElementBySId(id_):
		return id_
	id_ = normalize(id_)
	i = generate_unique_id_increment(model, 0, id_)
	return "%s_%d" % (id_, i)


def generate_unique_id_increment(model, i, id_prefix):
	while model.getElementBySId("%s_%d" % (id_prefix, i)):
		i += 1
	return i


def copy_species_type(model, id_, prototype):
	if prototype:
		id_ = generate_unique_id(model, id_ if id_ else "t_new")
		sp_type = SpeciesType(prototype)
		sp_type.setId(id_)
		model.addSpeciesType(sp_type)


def create_species_type(model, name, term_id=None, id_=None):
	new_type = model.createSpeciesType()
	id_ = generate_unique_id(model, id_ if id_ else "t_new")
	new_type.setId(id_)
	new_type.setName(name)
	if term_id:
		add_annotation(new_type, BQB_IS, to_identifiers_org_format(term_id))
	return new_type


def create_compartment(model, name, outside=None, term_id=None, id_=None):
	new_comp = model.createCompartment()
	id_ = generate_unique_id(model, id_ if id_ else "c_new")
	new_comp.setId(id_)
	new_comp.setName(name)
	if outside:
		new_comp.setOutside(outside)
	if term_id:
		add_annotation(new_comp, BQB_IS, to_identifiers_org_format(term_id, "obo.go"))
	return new_comp


def create_species(model, compartment_id, type_id=None, name=None, id_=None, sbo_id=None):
	new_species = model.createSpecies()
	id_ = generate_unique_id(model, id_ if id_ else "s_new")
	if LIBSBML_OPERATION_SUCCESS != new_species.setId(id_):
		logging.error("species  %s creation error" % id_)
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


def create_reaction(model, reactants, products, name=None, id_=None):
	reaction = model.createReaction()
	id_ = generate_unique_id(model, id_ if id_ else "r_new")
	if LIBSBML_OPERATION_SUCCESS != reaction.setId(id_):
		logging.error("reaction  ", id_, " creation error")
	for sp_id in reactants:
		reactant = model.createReactant()
		reactant.setSpecies(sp_id)
	for sp_id in products:
		product = model.createProduct()
		product.setSpecies(sp_id)
	if name:
		reaction.setName(name)
	return reaction


def _copy_species_reference(sp_ref, species_id_replacement_map):
	sp_id = sp_ref.getSpecies()
	new_sp_ref = SpeciesReference(sp_ref)
	new_sp_ref.setStoichiometry(sp_ref.getStoichiometry())
	if sp_id in species_id_replacement_map:
		new_sp_ref.setSpecies(species_id_replacement_map[sp_id])
	return new_sp_ref


def copy_reaction(model, prototype, species_id_old2new, param_id_old2new, unit_id_old2new, name=None, comp_id=None,
                  id_=None):
	new_reaction = Reaction(prototype)
	id_ = generate_unique_id(model, id_ if id_ else "r_new")
	new_reaction.setId(id_)
	if comp_id:
		new_reaction.setCompartment(comp_id)
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
			new_sp_ref = _copy_species_reference(spRef, species_id_old2new)
			new_reaction.addReactant(new_sp_ref)

	model.addReaction(new_reaction)
	return new_reaction


def remove_is_a_reactions(input_model):
	to_remove = []
	for reaction in input_model.getListOfReactions():
		if 1 == reaction.getNumReactants() == reaction.getNumProducts() \
				and reaction.getName().find("isa ") != -1 \
				and input_model.getCompartment(reaction.getListOfReactants().get(0).getSpecies()) == \
						input_model.getCompartment(reaction.getListOfReactants().get(0).getSpecies()):
			to_remove.append(reaction.getId())
	for r_id in to_remove:
		input_model.removeReaction(r_id)


# serialization

def set_consistency_level(doc):
	doc.setConsistencyChecksForConversion(LIBSBML_CAT_GENERAL_CONSISTENCY, False)
	doc.setConsistencyChecksForConversion(LIBSBML_CAT_IDENTIFIER_CONSISTENCY, False)
	doc.setConsistencyChecksForConversion(LIBSBML_CAT_UNITS_CONSISTENCY, False)
	doc.setConsistencyChecksForConversion(LIBSBML_CAT_MATHML_CONSISTENCY, False)
	doc.setConsistencyChecksForConversion(LIBSBML_CAT_SBO_CONSISTENCY, False)
	doc.setConsistencyChecksForConversion(LIBSBML_CAT_OVERDETERMINED_MODEL, False)
	doc.setConsistencyChecksForConversion(LIBSBML_CAT_MODELING_PRACTICE, False)


def convert_to_lev3_v1(model):
	doc = SBMLDocument(model.getSBMLNamespaces())
	doc.setModel(model)
	set_consistency_level(doc)
	doc.checkL3v1Compatibility()
	doc.setLevelAndVersion(3, 1, False)
	doc.enablePackage("http://www.sbml.org/sbml/level3/version1/groups/version1", "groups", True)
	# doc.getSBMLNamespaces().addPackageNamespace("groups", 1)
	return doc


def convert_to_l2v4_with_species_types(sbml):
	doc = SBMLReader().readSBMLFromFile(sbml)
	input_model = doc.getModel()
	doc = SBMLDocument(input_model.getSBMLNamespaces())
	doc.setModel(input_model)
	set_consistency_level(doc)
	doc.checkL2v4Compatibility()
	converted = doc.setLevelAndVersion(2, 4, False)
	if not converted:
		doc = SBMLReader().readSBMLFromFile(sbml)
	input_model = doc.getModel()
	check_names(input_model)
	if converted:
		add_species_types(input_model)
	check_compartments(input_model)
	return doc


def check_compartments(model):
	if not model.getListOfCompartments():
		cell_id = create_compartment(model, "cell", outside=None, term_id="GO:0005623").get_id()
		for sp in model.getListOfSpecies():
			sp.setCompartment(cell_id)


def check_names(model):
	def name_setter(collection):
		for it in collection:
			if not it.isSetName():
				it.setName(it.getId())

	name_setter(model.getListOfCompartments())
	name_setter(model.getListOfSpecies())
	name_setter(model.getListOfSpeciesTypes())


def add_species_types(model):
	name2species_type = {}
	name2species = {}
	for species in model.getListOfSpecies():
		name = species.getName()
		if species.isSetSpeciesType():
			species_type = species.getSpeciesType()
			name2species_type[name] = species_type
		else:
			if name in name2species:
				name2species[name].append(species)
			else:
				name2species[name] = [species]
	for name, species_list in name2species.iteritems():
		s_t_id = name2species_type[name] if name in name2species_type else create_species_type(model, name)
		species_type = model.getSpeciesType(s_t_id)
		for species in species_list:
			species.setSpeciesType(s_t_id)
			if species.isSetAnnotation():
				species_type.setAnnotation(species.getAnnotation())


# def model_to_l3v1(sbml, model):
# doc = convert_to_lev3_v1(Model(model))
# # writeSBMLToFile(doc, sbml)


def annotate_ubiquitous(groups_sbml, ub_sps, verbose=False):
	if groups_sbml:
		#log(verbose, "saving ubiquitous species annotations...")
		doc = SBMLReader().readSBMLFromFile(groups_sbml)
		groups_model = doc.getModel()
		groups_plugin = groups_model.getPlugin("groups")
		if groups_plugin:
			s_group = groups_plugin.createGroup()
			s_group.setId("g_ubiquitous_sps")
			s_group.setKind(GROUP_KIND_COLLECTION)
			s_group.setSBOTerm(SBO_CHEMICAL_MACROMOLECULE)
			s_group.setName("ubiquitous species")
			for s_id in ub_sps:
				member = s_group.createMember()
				member.setIdRef(s_id)
			add_annotation(s_group, BQB_IS_DESCRIBED_BY, GROUP_TYPE_UBIQUITOUS)
			save_as_sbml(groups_model, groups_sbml, verbose)


def save_as_comp_generalized_sbml(input_model, out_sbml, groups_sbml, r_id2clu, s_id2clu, ub_sps, verbose):
	log(verbose, "serializing generalization...")
	s_id_increment, r_id_increment = 0, 0

	if groups_sbml:
		doc = convert_to_lev3_v1(input_model)
		groups_model = doc.getModel()
		groups_plugin = groups_model.getPlugin("groups")
		if groups_plugin:
			log(verbose, "saving ubiquitous species annotations...")
			s_group = groups_plugin.createGroup()
			s_group.setId("g_ubiquitous_sps")
			s_group.setKind(GROUP_KIND_COLLECTION)
			s_group.setSBOTerm(SBO_CHEMICAL_MACROMOLECULE)
			s_group.setName("ubiquitous species")
			for s_id in ub_sps:
				member = s_group.createMember()
				member.setIdRef(s_id)
			add_annotation(s_group, BQB_IS_DESCRIBED_BY, GROUP_TYPE_UBIQUITOUS)
	if out_sbml:
		# generalized model
		generalized_doc = SBMLDocument(input_model.getSBMLNamespaces())
		generalized_model = generalized_doc.createModel()
		copy_elements(input_model, generalized_model)

	r_id2g_eq, s_id2gr_id = {}, {}
	if not s_id2clu:
		log(verbose, "nothing to serialize.")
	else:
		clu2r_ids = invert_map(r_id2clu)

		clu2s_ids = invert_map(s_id2clu)
		log(verbose, "creating species groups...")
		for (c_id, t), s_ids in clu2s_ids.iteritems():
			comp = input_model.getCompartment(c_id)
			if len(s_ids) > 1:
				t_name, t_id = (t.get_name(), t.get_id()) if not isinstance(t, tuple) else (
					' or '.join(input_model.getSpecies(s_id).getName() for s_id in s_ids), None)
				if not t_id:
					t = t_name

				if out_sbml:
					new_species = create_species(generalized_model, comp.getId(), type_id=None,
					                             name="{0} ({1}) [{2}]".format(t_name, len(s_ids), comp.getName()))
					add_annotation(new_species, BQB_IS, to_identifiers_org_format(t_id))
					new_s_id = new_species.getId()
				else:
					s_id_increment += 1
					s_id_increment = generate_unique_id_increment(input_model, s_id_increment, "s_generalized")
					new_s_id = "s_generalized_%d" % s_id_increment
				for s_id in s_ids:
					s_id2gr_id[s_id] = new_s_id, t

				if groups_sbml and groups_plugin:
					# save as a group
					s_group = groups_plugin.createGroup()
					s_group.setId(new_s_id)
					s_group.setKind(GROUP_KIND_CLASSIFICATION)
					s_group.setSBOTerm(SBO_CHEMICAL_MACROMOLECULE)
					g_name = "{0} [{1}]".format(t_name, comp.getName())
					s_group.setName(g_name)
					log(verbose, "%s: %d" % (g_name, len(s_ids)))
					if t_id:
						add_annotation(s_group, BQB_IS, to_identifiers_org_format(t_id))
					for s_id in s_ids:
						member = s_group.createMember()
						member.setIdRef(s_id)
					add_annotation(s_group, BQB_IS_DESCRIBED_BY, GROUP_TYPE_EQUIV)

		generalize_species = lambda species_id: s_id2gr_id[species_id][0] if (species_id in s_id2gr_id) else species_id
		s_id_to_generalize = set(s_id2gr_id.iterkeys())
		log(verbose, "creating reaction groups...")
		for clu, r_ids in clu2r_ids.iteritems():
			representative = input_model.getReaction(list(r_ids)[0])
			r_name = "generalized %s" % representative.getName()
			if out_sbml:
				reactants = get_reactants(representative)
				products = get_products(representative)
				if (len(r_ids) == 1) and not ((reactants | products) & s_id_to_generalize):
					generalized_model.addReaction(representative)
					continue
				reactants = {generalize_species(it) for it in reactants}
				products = {generalize_species(it) for it in products}
				new_reaction = create_reaction(generalized_model, reactants, products, r_name)
				new_r_id = new_reaction.getId()
			elif len(r_ids) > 1:
				r_id_increment += 1
				r_id_increment = generate_unique_id_increment(input_model, r_id_increment, "r_generalized")
				new_r_id = "r_generalized_%d" % r_id_increment

			if len(r_ids) > 1:
				for r_id in r_ids:
					r_id2g_eq[r_id] = new_r_id, r_name
				if groups_sbml and groups_plugin:
					# save as a group
					r_group = groups_plugin.createGroup()
					r_group.setId(new_r_id)
					r_group.setKind(GROUP_KIND_COLLECTION)
					r_group.setSBOTerm(SBO_BIOCHEMICAL_REACTION)
					r_group.setName(r_name)
					log(verbose, "%s: %d" % (r_name, len(r_ids)))
					for r_id in r_ids:
						member = r_group.createMember()
						member.setIdRef(r_id)
					add_annotation(r_group, BQB_IS_DESCRIBED_BY, GROUP_TYPE_EQUIV)

		log(verbose, "done with creating groups.")
	if out_sbml:
		remove_unused_elements(generalized_model)
		save_as_sbml(generalized_model, out_sbml, verbose)
	if groups_sbml and groups_model:
		save_as_sbml(groups_model, groups_sbml, verbose)

	log(verbose, "serialized to " + groups_sbml)
	return r_id2g_eq, s_id2gr_id


def save_as_sbml(input_model, out_sbml, verbose=True):
	log(verbose, "saving to {0}...".format(out_sbml))
	out_doc = SBMLDocument(input_model.getSBMLNamespaces())
	out_doc.setModel(input_model)
	result = writeSBMLToFile(out_doc, out_sbml)
	log(verbose, "saving result: %d" % result)


def parse_group_sbml(groups_sbml, chebi):
	doc = SBMLReader().readSBMLFromFile(groups_sbml)
	groups_model = doc.getModel()
	groups_plugin = groups_model.getPlugin("groups")
	r_id2g_id, s_id2gr_id, ub_sps = {}, {}, set()
	if groups_plugin:
		for group in groups_plugin.getListOfGroups():
			gr_members = [it.getIdRef() for it in group.getListOfMembers()]
			gr_id, gr_name = group.getId(), group.getName()
			gr_sbo = group.getSBOTermID()
			try:
				gr_type = get_qualifier_values(group.getAnnotation(), BQB_IS_DESCRIBED_BY).next()
			except StopIteration:
				continue
			if SBO_BIOCHEMICAL_REACTION == gr_sbo:
				if GROUP_TYPE_EQUIV == gr_type:
					for r_id in gr_members:
						r_id2g_id[r_id] = gr_id, gr_name, len(gr_members)
			elif SBO_CHEMICAL_MACROMOLECULE == gr_sbo:
				if GROUP_TYPE_UBIQUITOUS == gr_type:
					ub_sps = set(gr_members)
				elif GROUP_TYPE_EQUIV == gr_type:
					for s_id in gr_members:
						term = get_term(group, chebi)
						s_id2gr_id[s_id] = gr_id, term if term else gr_name, len(gr_members)
	else:
		raise GrPlError("groups plugin not installed")
	return r_id2g_id, s_id2gr_id, ub_sps


def check_for_groups(groups_sbml, sbo_term, group_type):
	doc = SBMLReader().readSBMLFromFile(groups_sbml)
	groups_plugin = doc.getModel().getPlugin("groups")
	if groups_plugin:
		for group in groups_plugin.getListOfGroups():
			gr_sbo = group.getSBOTermID()
			try:
				gr_type = get_qualifier_values(group.getAnnotation(), BQB_IS_DESCRIBED_BY).next()
			except StopIteration:
				continue
			if sbo_term == gr_sbo and group_type == gr_type:
				return True
	return False


class GrPlError(Exception):
	def __init__(self, msg):
		self.msg = msg
