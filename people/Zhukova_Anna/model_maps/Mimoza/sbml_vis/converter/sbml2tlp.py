from tulip import tlp

from sbml_generalization.utils.logger import log
from sbml_generalization.generalization.sbml_helper import check_names, check_compartments, parse_group_sbml, GrPlError
from sbml_generalization.utils.compartment_positioner import get_comp2go, comp2level
from sbml_generalization.utils.obo_ontology import parse, get_chebi, get_go, Term
from sbml_generalization.generalization.reaction_filters import getGeneAssociation
from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi

from sbml_vis.tulip.node_cloner import clone_node
from sbml_vis.tulip.graph_properties import *
from sbml_vis.tulip.resize import REACTION_SIZE, get_n_size, get_e_size


__author__ = 'anna'


def species2nodes(graph, input_model, species_id2chebi_id, ub_sps):
	id2n = {}
	for s in input_model.getListOfSpecies():
		n = graph.addNode()
		comp = input_model.getCompartment(s.getCompartment())
		graph[COMPARTMENT][n] = comp.getId()
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
		graph[VIEW_SHAPE][n] = SPECIES_SHAPE
		graph[VIEW_SIZE][n] = get_n_size(graph, n)
	return id2n


def reactions2nodes(get_r_comp, graph, id2n, input_model):
	get_sp_comp = lambda _id: graph[COMPARTMENT][id2n[_id]]

	def link_reaction_to_species(reaction_node, sp_ref, all_comps, is_reactant=True):
		s_id = sp_ref.getSpecies()

		all_comps.add(get_sp_comp(s_id))

		species_node = id2n[s_id]
		e = graph.addEdge(species_node, reaction_node) if is_reactant else graph.addEdge(reaction_node, species_node)
		stoich = sp_ref.getStoichiometry()
		if not stoich:
			stoich = sp_ref.getStoichiometryMath()
		if not stoich:
			stoich = 1
		graph[STOICHIOMETRY][e] = stoich
		graph[NAME][e] = input_model.getSpecies(s_id).getName()
		ub = graph[UBIQUITOUS][species_node]
		graph[UBIQUITOUS][e] = ub

	for r in input_model.getListOfReactions():
		name = r.getName()
		# do not add fake isa reactions
		# if name.find("isa ") != -1 and 1 == r.getNumReactants() == r.getNumProducts() and get_sp_comp(
		# 		r.getListOfReactants().get(0).getSpecies()) == get_sp_comp(
		# 		r.getListOfProducts().get(0).getSpecies()):
		# 	continue

		n = graph.addNode()
		graph[ANNOTATION][n] = getGeneAssociation(r)
		graph[ID][n] = r.getId()
		graph[NAME][n] = name
		graph[TYPE][n] = TYPE_REACTION
		graph[REVERSIBLE][n] = r.getReversible()

		graph[VIEW_SHAPE][n] = REACTION_SHAPE
		graph[VIEW_SIZE][n] = get_n_size(graph, n)

		all_comps = set()
		for sp_ref in r.getListOfReactants():
			link_reaction_to_species(n, sp_ref, all_comps, is_reactant=True)
		for sp_ref in r.getListOfProducts():
			link_reaction_to_species(n, sp_ref, all_comps, is_reactant=False)

		graph[TRANSPORT][n] = len(all_comps) > 1
		graph[COMPARTMENT][n] = get_r_comp(all_comps)


def get_quotient_maps(chebi, input_model, sbml_file, verbose):
	try:
		r_id2g_id, s_id2gr_id, ub_sps = parse_group_sbml(sbml_file, chebi)
		species_id2chebi_id = get_species_to_chebi(input_model, chebi) if (r_id2g_id or ub_sps) else {}
		return r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps
	except GrPlError:
		return None, None, None, None, None


def compute_c_id2info(c_id2level, comp2go_term, input_model):
	c_id2info = {}
	for comp in input_model.getListOfCompartments():
		c_id = comp.getId()
		c_name = comp.getName()
		if not c_name:
			c_name = c_id
		c_id2info[c_id] = (c_name, comp2go_term[c_id] if c_id in comp2go_term else None, c_id2level[c_id])

	c_id2outs = {}
	for c_id in c_id2info.iterkeys():
		_, _, (_, out_c_id) = c_id2info[c_id]
		outs = []
		while out_c_id:
			outs.append(out_c_id)
			_, _, (_, out_c_id) = c_id2info[out_c_id]
		c_id2outs[c_id] = outs

	return c_id2info, c_id2outs


def import_sbml(input_model, sbml_file, verbose=False):
	log(verbose, 'parsing ChEBI')
	chebi = parse(get_chebi())

	log(verbose, 'reading generalized model from %s' % sbml_file)
	r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps = get_quotient_maps(chebi, input_model, sbml_file, verbose)

	log(verbose, 'fixing labels and compartments')
	check_names(input_model)
	check_compartments(input_model)

	log(verbose, 'annotating with GO')
	onto = parse(get_go())
	comp2go_term = get_comp2go(input_model, onto)
	c_id2level = comp2level(input_model)
	c_id2info, c_id2outs = compute_c_id2info(c_id2level, comp2go_term, input_model)

	def get_r_comp(all_comp_ids):
		if len(all_comp_ids) == 1:
			return all_comp_ids.pop()
		get_level = lambda c_id: c_id2level[c_id][0]
		outer_most = min(all_comp_ids, key=get_level)
		inner_most = max(all_comp_ids, key=get_level)
		outer_level, inner_level = get_level(outer_most), get_level(inner_most)
		if outer_level == inner_level or not outer_most in c_id2outs[inner_most]:
			return max(set(c_id2outs[inner_most]) & set(c_id2outs[outer_most]), key=get_level)
		if outer_level - inner_level >= 1:
			return max(c_id2outs[inner_most], key=get_level)
		return outer_most

	log(verbose, 'initialising the graph')
	graph = tlp.newGraph()
	graph.setName(input_model.getId())
	create_props(graph)

	log(verbose, 'adding species nodes')
	id2n = species2nodes(graph, input_model, species_id2chebi_id, ub_sps)

	log(verbose, 'adding reaction nodes')
	reactions2nodes(get_r_comp, graph, id2n, input_model)

	log(verbose, 'duplicating nodes')
	duplicate_nodes(graph)

	log(verbose, 'marking species/reaction groups')
	mark_ancestors(graph, r_id2g_id, s_id2gr_id)
	return graph, chebi, c_id2info, c_id2outs


def create_props(graph):
	graph.getStringProperty(ANCESTOR_ANNOTATION)
	graph.getStringProperty(ANCESTOR_ID)
	graph.getStringProperty(ANCESTOR_NAME)

	graph.getStringProperty(ANNOTATION)

	graph.getStringProperty(COMPARTMENT)

	graph.getStringProperty(ID)
	graph.getStringProperty(NAME)

	graph.getIntegerProperty(TYPE)

	graph.getBooleanProperty(REVERSIBLE)
	graph.getDoubleProperty(STOICHIOMETRY)
	graph.getBooleanProperty(TRANSPORT)

	graph.getBooleanProperty(UBIQUITOUS)

	graph.getLayoutProperty(VIEW_LAYOUT)
	# graph.getColorProperty(VIEW_COLOR)
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

