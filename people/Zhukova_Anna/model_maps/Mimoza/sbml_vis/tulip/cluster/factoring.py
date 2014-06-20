from collections import defaultdict

from sbml_vis.tulip.node_cloner import merge_nodes
from sbml_vis.tulip.resize import get_n_size, get_e_size
from sbml_vis.tulip.graph_properties import *
from sbml_vis.tulip.layout.layout_utils import layout


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
	for nodes in ancestor2nodes.itervalues():
		if len(nodes) <= 1:
			continue
		id2ub_ns = defaultdict(set)
		for node in nodes:
			for n in (n for n in graph.getInOutNodes(node) if ubiquitous[n]):
				id2ub_ns[root[ID][n]].add(n)
		for ubs in id2ub_ns.itervalues():
			merge_nodes(root, ubs)


def factor_nodes(graph):
	root = graph.getRoot()
	# clone = root.inducedSubGraph(list(graph.getNodes()))

	merge_ubs_for_similar_reactions(graph)

	ancestor2nodes = defaultdict(list)
	for node in graph.getNodes():
		ancestor = root[ANCESTOR_ID][node]
		if ancestor:
			ancestor = ancestor, root[TYPE][node], root[COMPARTMENT][node]
			ancestor2nodes[ancestor].append(node)

	for (ancestor, type_, comp), nodes in ancestor2nodes.iteritems():
		if len(nodes) <= 1:
			continue
		all_nodes = list(nodes)

		meta_node = graph.createMetaNode(all_nodes, False)
		mg = graph[VIEW_META_GRAPH][meta_node]
		n = nodes[0]

		for prop in [COMPARTMENT, TYPE, REVERSIBLE, UBIQUITOUS, VIEW_SHAPE]: #, VIEW_COLOR, VIEW_LAYOUT
			root[prop][meta_node] = root[prop][n]
		for e in root.getInOutEdges(meta_node):
			root[UBIQUITOUS][e] = root[UBIQUITOUS][list(root[VIEW_META_GRAPH][e])[0]]
		root[ID][meta_node] = root[ANCESTOR_ID][n]
		root[NAME][meta_node] = root[ANCESTOR_NAME][n]
		root[VIEW_SIZE][meta_node] = get_n_size(root, meta_node)

		if TYPE_REACTION == type_:
			mg.setName("generalized {0} ({1})".format(root[NAME][n], len(nodes)))
			root[REVERSIBLE][meta_node] = True
			root[TRANSPORT][meta_node] = False
			for n in nodes:
				if not root[REVERSIBLE][n]:
					root[REVERSIBLE][meta_node] = False
				if root[TRANSPORT][n]:
					root[TRANSPORT][meta_node] = True
			root[ANNOTATION][meta_node] = "\nor\n".join({root[ANNOTATION][it] for it in nodes})
		else:
			mg.setName("{0} ({1})".format(root[ANCESTOR_NAME][n], len(nodes)))
			root[ANNOTATION][meta_node] = root[ANCESTOR_ANNOTATION][n]

		root[NAME][meta_node] = mg.getName()

	# root.delSubGraph(clone)
	for n in (n for n in graph.getNodes() if TYPE_REACTION == root[TYPE][n] and graph.isMetaNode(n)):
		for e in graph.getInOutEdges(n):
			root[STOICHIOMETRY][e] = root[STOICHIOMETRY][list(root[VIEW_META_GRAPH][e])[0]]
			root[VIEW_SIZE][e] = get_e_size(graph, e)


def comp_to_meta_node(meta_graph, c_id, (go_id, c_name), out_comp):
	root = meta_graph.getRoot()
	ns = filter(lambda n: root[COMPARTMENT][n] == c_id, meta_graph.getNodes())
	if not ns:
		return None
	meta_node = meta_graph.createMetaNode(ns, False)
	comp_graph = root[VIEW_META_GRAPH][meta_node]
	layout(comp_graph)
	# layout_single_species(comp_graph, {})
	comp_graph.setName("_" + c_id)
	# root[VIEW_LAYOUT][meta_node] = tlp.computeBoundingBox(comp_graph).center()
	root[NAME][meta_node] = c_name
	root[COMPARTMENT][meta_node] = out_comp
	root[TYPE][meta_node] = TYPE_COMPARTMENT
	root[VIEW_SHAPE][meta_node] = REACTION_SHAPE
	root[ID][meta_node] = c_id
	root[ANNOTATION][meta_node] = go_id
	root[VIEW_SIZE][meta_node] = get_n_size(meta_graph, meta_node)
	for e in meta_graph.getInOutEdges(meta_node):
		root[UBIQUITOUS][e] = root[UBIQUITOUS][list(root[VIEW_META_GRAPH][e])[0]]
		# todo: fix size: we have no more metanodes
		root[VIEW_SIZE][e] = get_e_size(meta_graph, e)
	return meta_node


# def factor_comps(meta_graph, c_name2id_go):
# 	mic(meta_graph)
# 	root = meta_graph.getRoot()
# 	cytoplasm = root.getAttribute(CYTOPLASM)
# 	organelle2meta_node = {}
# 	for organelle in root.getAttribute(ORGANELLES).split(";"):
# 		(c_id, go) = c_name2id_go[organelle] if organelle in c_name2id_go else ('', '')
# 		meta_node = comp_to_meta_node(meta_graph, organelle, (c_id, go), cytoplasm)
# 		if meta_node:
# 			organelle2meta_node[organelle] = meta_node
# 	resize_edges(meta_graph)
# 	return organelle2meta_node


# def factor_cytoplasm(meta_graph, c_name2id_go):
# 	root = meta_graph.getRoot()
# 	cytoplasm = root.getAttribute(CYTOPLASM)
# 	(c_id, go) = c_name2id_go[cytoplasm] if cytoplasm in c_name2id_go else ('', '')
# 	meta_node = comp_to_meta_node(meta_graph, cytoplasm, (c_id, go), EXTRACELLULAR)
# 	resize_edges(meta_graph)
# 	return cytoplasm, meta_node