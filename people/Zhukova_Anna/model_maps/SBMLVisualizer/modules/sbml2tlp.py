from tulip import tlp
from sbml_generalization.utils.logger import log
from modules.graph_tools import *

from sbml_generalization.generalization.sbml_helper import check_names, check_compartments

from sbml_generalization.utils.compartment_positioner import get_comp2go, sort_comps
from sbml_generalization.utils.obo_ontology import parse, get_chebi, get_go, Term
from sbml_generalization.generalization.reaction_filters import getGeneAssociation

from modules.model_utils import clone_node

from modules.resize import r_size, ub_sp_size, sp_size, ub_e_size, e_size
from runner.mod_gen_helper import generalize_entities


__author__ = 'anna'

arrowShape = 50


def species2nodes(comp2go_term, get_comp, graph, input_model, species_id2chebi_id, ub_sps):
	id2n = {}
	for s in input_model.getListOfSpecies():
		n = graph.addNode()
		comp = input_model.getCompartment(s.getCompartment())
		graph[REAL_COMPARTMENT][n] = '{0}, {1}, {2}'.format(comp.getName(), comp.getId(),
		                                                    comp2go_term[comp.getId()])
		graph[COMPARTMENT][n] = get_comp(comp.getId())

		_id = s.getId()
		graph[ID][n] = _id
		id2n[_id] = n
		name = s.getName()
		graph[NAME][n] = name
		graph[TYPE][n] = TYPE_SPECIES

		ub = _id in ub_sps
		graph[UBIQUITOUS][n] = ub
		if _id in species_id2chebi_id:
			graph[ANNOTATION][n] = species_id2chebi_id[_id]

		graph[VIEW_SHAPE][n] = ROUND_SHAPE
		graph[VIEW_SIZE][n] = tlp.Size(ub_sp_size, ub_sp_size) if ub else tlp.Size(sp_size, sp_size)
	return id2n


def reactions2nodes(get_r_comp, graph, id2n, input_model):
	get_sp_comp = lambda _id: graph[COMPARTMENT][id2n[_id]]

	def link_reaction_to_species(reaction_node, sp_ref, all_comps, is_reactant=True):
		s_id = sp_ref.getSpecies()
		all_comps.add(get_sp_comp(s_id))
		species_node = id2n[s_id]
		e = graph.addEdge(species_node, reaction_node) if is_reactant else graph.addEdge(reaction_node, species_node)
		# graph["viewSrcAnchorShape"][e] = arrowShape if (not is_reactant or r.getReversible()) else -1
		# graph["viewTgtAnchorShape"][e] = -1 if (not is_reactant or r.getReversible()) else arrowShape
		stoich = sp_ref.getStoichiometry()
		if not stoich:
			stoich = sp_ref.getStoichiometryMath()
		if not stoich:
			stoich = 1
		graph[STOICHIOMETRY][e] = stoich
		graph[NAME][e] = input_model.getSpecies(s_id).getName()
		graph[VIEW_SIZE][e] = tlp.Size(ub_e_size, ub_e_size) if graph[UBIQUITOUS][species_node] else tlp.Size(e_size,
		                                                                                                      e_size)

	for r in input_model.getListOfReactions():
		name = r.getName()
		# do not add fake isa reactions
		if name.find("isa ") != -1 and 1 == r.getNumReactants() == r.getNumProducts() and get_sp_comp(
				r.getListOfReactants().get(0).getSpecies()) == get_sp_comp(
				r.getListOfProducts().get(0).getSpecies()):
			continue

		n = graph.addNode()
		graph[ANNOTATION][n] = getGeneAssociation(r)
		graph[ID][n] = r.getId()
		graph[NAME][n] = name
		graph[TYPE][n] = TYPE_REACTION
		graph[REVERSIBLE][n] = r.getReversible()

		graph[VIEW_SHAPE][n] = SQUARE_SHAPE
		graph[VIEW_SIZE][n] = tlp.Size(r_size, r_size)

		all_comps = set()
		for sp_ref in r.getListOfReactants():
			link_reaction_to_species(n, sp_ref, all_comps, is_reactant=True)
		for sp_ref in r.getListOfProducts():
			link_reaction_to_species(n, sp_ref, all_comps, is_reactant=False)

		graph[TRANSPORT][n] = len(all_comps) > 1
		graph[COMPARTMENT][n] = get_r_comp(all_comps)


def import_sbml(graph, input_model, sbml_file, verbose=False, log_file=None):
	chebi = parse(get_chebi())

	log(verbose, 'calling model_generalisation library')
	r_id2ch_id, r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps, groups_sbml = generalize_entities(chebi,
	                                                                                                  input_model,
	                                                                                                  sbml_file,
	                                                                                                  verbose, log_file)
	log(verbose, 'fixing labels and compartments')
	check_names(input_model)
	check_compartments(input_model)

	log(verbose, 'annotating with GO')
	onto = parse(get_go())
	comp2go_term = get_comp2go(input_model, onto)
	part2org, cyto, others = sort_comps(onto, comp2go_term)

	name2id_go = {}
	for comp in input_model.getListOfCompartments():
		c_id = comp.getId()
		c_name = comp.getName()
		if not c_name:
			c_name = c_id
		name2id_go[c_name] = (c_id, comp2go_term[c_id] if c_id in comp2go_term else None)

	r_c2c = {}
	if cyto:
		cytoplasm_comp = input_model.getCompartment(list(cyto)[0])
		cytoplasm = cytoplasm_comp.getName()
		if not cytoplasm:
			cytoplasm = cytoplasm_comp.getId()
	else:
		cytoplasm = CYTOPLASM
	extracellular = EXTRACELLULAR
	organelles = set()

	def get_comp(c_id):
		if c_id in r_c2c:
			return r_c2c[c_id]
		if c_id in part2org:
			comp_id = part2org[c_id]
			compartment = input_model.getCompartment(comp_id)
			c = compartment.getName()
			if not c:
				c = comp_id
			organelles.add(c)
		elif c_id in others:
			c = cytoplasm
		else:
			c = extracellular
		r_c2c[c_id] = c
		return c

	def get_r_comp(all_comps):
		if len(all_comps) == 1:
			return all_comps.pop()
		if extracellular in all_comps:
			return extracellular
		return cytoplasm

	log(verbose, 'initialising the graph')
	graph.setName(input_model.getId())
	create_props(graph)

	log(verbose, 'adding species nodes')
	id2n = species2nodes(comp2go_term, get_comp, graph, input_model, species_id2chebi_id, ub_sps)

	log(verbose, 'adding reaction nodes')
	reactions2nodes(get_r_comp, graph, id2n, input_model)

	log(verbose, 'setting organelles attributes')
	graph.setAttribute(ORGANELLES, ";".join(organelles))
	graph.setAttribute(CYTOPLASM, cytoplasm)

	log(verbose, 'duplicating nodes')
	duplicate_nodes(graph)
	clean(graph)

	log(verbose, 'marking species/reaction groups')
	mark_ancestors(graph, r_id2g_id, s_id2gr_id)
	return graph, groups_sbml, chebi, name2id_go


def create_props(graph):
	graph.getStringProperty(ANCESTOR_ANNOTATION)
	graph.getStringProperty(ANCESTOR_ID)
	graph.getStringProperty(ANCESTOR_NAME)

	graph.getStringProperty(ANNOTATION)

	graph.getStringProperty(COMPARTMENT)
	graph.getStringProperty(REAL_COMPARTMENT)

	graph.getStringProperty(ID)
	graph.getStringProperty(NAME)

	graph.getIntegerProperty(TYPE)

	graph.getBooleanProperty(REVERSIBLE)
	graph.getDoubleProperty(STOICHIOMETRY)
	graph.getBooleanProperty(TRANSPORT)

	graph.getBooleanProperty(UBIQUITOUS)

	graph.getLayoutProperty(VIEW_LAYOUT)
	graph.getColorProperty(VIEW_COLOR)
	graph.getIntegerProperty(VIEW_SHAPE)
	graph.getSizeProperty(VIEW_SIZE)


def duplicate_nodes(graph):
	root = graph.getRoot()
	for n in (n for n in graph.getNodes() if root[UBIQUITOUS][n]):
		clone_node(graph, n)


def clean(graph):
	for n in (n for n in graph.getNodes() if not graph.deg(n)):
		graph.delNode(n)


def mark_ancestors(graph, r_eq2clu, s2clu):
	root = graph.getRoot()
	id_ = root.getStringProperty(ID)
	anc_id = root.getStringProperty(ANCESTOR_ID)
	anc_name = root.getStringProperty(ANCESTOR_NAME)
	anc_ch_id = root.getStringProperty(ANCESTOR_ANNOTATION)
	type_ = root.getIntegerProperty(TYPE)
	for n in graph.getNodes():
		gr_id, gr_name, term = None, None, None
		if TYPE_REACTION == type_[n]:
			if id_[n] in r_eq2clu:
				gr_id, gr_name = r_eq2clu[id_[n]]
		elif id_[n] in s2clu:
			gr_id, term = s2clu[id_[n]]
			if term:
				if isinstance(term, Term):
					gr_name = term.getName()
				else:
					gr_name = term
					term = None
		if gr_name:
			anc_name[n] = gr_name
		if gr_id:
			anc_id[n] = gr_id
		if term:
			anc_ch_id[n] = term.getId()

