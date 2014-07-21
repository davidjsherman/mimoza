from collections import defaultdict

from sbml_vis.graph.node_cloner import merge_nodes
from sbml_vis.graph.resize import get_n_size
from sbml_vis.graph.graph_properties import *
from sbml_vis.graph.layout.layout_utils import layout, layout_cytoplasm


__author__ = 'anna'


def merge_ubs_for_similar_reactions(graph):
	root = graph.getRoot()

	ancestor2nodes = defaultdict(list)
	for node in graph.getNodes():
		ancestor = root[ANCESTOR_ID][node]
		if ancestor and TYPE_REACTION == root[TYPE][node]:
			ancestor = ancestor, root[COMPARTMENT][node]
			ancestor2nodes[ancestor].append(node)

	ubiquitous = root[UBIQUITOUS]
	for nodes in (nodes for nodes in ancestor2nodes.itervalues() if len(nodes) > 1):
		id2ub_ns = defaultdict(set)
		for node in nodes:
			for n in (n for n in graph.getInOutNodes(node) if ubiquitous[n]):
				id2ub_ns[root[ID][n]].add(n)
		for ubs in id2ub_ns.itervalues():
			merge_nodes(root, ubs)


def factor_nodes(graph):
	root = graph.getRoot()
	merge_ubs_for_similar_reactions(root)

	ancestor2nodes = defaultdict(list)
	for node in graph.getNodes():
		ancestor = root[ANCESTOR_ID][node]
		if ancestor:
			ancestor = ancestor, root[TYPE][node], root[COMPARTMENT][node]
			ancestor2nodes[ancestor].append(node)

	for (ancestor, type_, comp), nodes in ((k, ns) for (k, ns) in ancestor2nodes.iteritems() if len(ns) > 1):
		sample_n = nodes[0]
		meta_n = graph.createMetaNode(nodes, False)

		for prop in [COMPARTMENT, TYPE, REVERSIBLE, UBIQUITOUS, VIEW_SHAPE]:
			root[prop][meta_n] = root[prop][sample_n]
		root[ID][meta_n] = root[ANCESTOR_ID][sample_n]
		root[VIEW_SIZE][meta_n] = get_n_size(root, meta_n)

		for meta_e in root.getInOutEdges(meta_n):
			sample_e = next(e for e in root[VIEW_META_GRAPH][meta_e])
			root[UBIQUITOUS][meta_e] = root[UBIQUITOUS][sample_e]
			root[STOICHIOMETRY][meta_e] = root[STOICHIOMETRY][sample_e]

		if TYPE_REACTION == type_:
			root[NAME][meta_n] = "generalized %s (%d)" % (root[NAME][sample_n], len(nodes))
			root[REVERSIBLE][meta_n] = True
			root[TRANSPORT][meta_n] = False
			for sample_n in nodes:
				if not root[REVERSIBLE][sample_n]:
					root[REVERSIBLE][meta_n] = False
				if root[TRANSPORT][sample_n]:
					root[TRANSPORT][meta_n] = True
			root[ANNOTATION][meta_n] = "\nor\n".join({root[ANNOTATION][it] for it in nodes})
		else:
			root[NAME][meta_n] = "%s (%d)" % (root[ANCESTOR_NAME][sample_n], len(nodes))
			root[ANNOTATION][meta_n] = root[ANCESTOR_ANNOTATION][sample_n]


def comp_to_meta_node(meta_graph, c_id, (go_id, c_name), out_comp):
	root = meta_graph.getRoot()
	ns = filter(lambda n: root[COMPARTMENT][n] == c_id, meta_graph.getNodes())
	if not ns:
		return None
	comp_n = meta_graph.createMetaNode(ns, False)
	comp_graph = root[VIEW_META_GRAPH][comp_n]
	layout(comp_graph)
	root[NAME][comp_n] = c_name
	root[COMPARTMENT][comp_n] = out_comp
	root[TYPE][comp_n] = TYPE_COMPARTMENT
	root[VIEW_SHAPE][comp_n] = COMPARTMENT_SHAPE
	root[ID][comp_n] = c_id
	root[ANNOTATION][comp_n] = go_id
	root[VIEW_SIZE][comp_n] = get_n_size(meta_graph, comp_n)
	for meta_e in root.getInOutEdges(comp_n):
		sample_e = next(e for e in root[VIEW_META_GRAPH][meta_e])
		root[UBIQUITOUS][meta_e] = root[UBIQUITOUS][sample_e]
		root[STOICHIOMETRY][meta_e] = root[STOICHIOMETRY][sample_e]
	return comp_n


def mic(graph):
	root = graph.getRoot()
	compartment = root.getStringProperty(COMPARTMENT)
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	id_ = root.getStringProperty(ID)

	id2unused = defaultdict(list)
	for n in (n for n in graph.getNodes() if ubiquitous[n]):
		comp = compartment[n]
		# Check if it is connected to something inside this compartment
		connected = next((m for m in graph.getInOutNodes(n) if comp == compartment[m]), None)
		_id = comp, id_[n]
		if not connected:
			id2unused[_id].append(n)
	for _id, unused_ns in id2unused.iteritems():
		merge_nodes(graph, unused_ns)