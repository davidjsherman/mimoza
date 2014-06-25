from collections import defaultdict
from tulip import tlp

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
		n = nodes[0]

		for prop in [COMPARTMENT, TYPE, REVERSIBLE, UBIQUITOUS, VIEW_SHAPE]: #, VIEW_COLOR, VIEW_LAYOUT
			root[prop][meta_node] = root[prop][n]
		for e in root.getInOutEdges(meta_node):
			sample_e = list(root[VIEW_META_GRAPH][e])[0]
			root[UBIQUITOUS][e] = root[UBIQUITOUS][sample_e]
			root[STOICHIOMETRY][e] = root[STOICHIOMETRY][sample_e]
		root[ID][meta_node] = root[ANCESTOR_ID][n]
		root[NAME][meta_node] = root[ANCESTOR_NAME][n]
		root[VIEW_SIZE][meta_node] = get_n_size(root, meta_node)

		if TYPE_REACTION == type_:
			root[NAME][meta_node] = "generalized %s (%d)" % (root[NAME][n], len(nodes))
			root[REVERSIBLE][meta_node] = True
			root[TRANSPORT][meta_node] = False
			for n in nodes:
				if not root[REVERSIBLE][n]:
					root[REVERSIBLE][meta_node] = False
				if root[TRANSPORT][n]:
					root[TRANSPORT][meta_node] = True
			root[ANNOTATION][meta_node] = "\nor\n".join({root[ANNOTATION][it] for it in nodes})
		else:
			root[NAME][meta_node] = "%s (%d)" % (root[ANCESTOR_NAME][n], len(nodes))
			root[ANNOTATION][meta_node] = root[ANCESTOR_ANNOTATION][n]


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
	root[VIEW_LAYOUT][comp_n] = tlp.computeBoundingBox(comp_graph).center()
	for e in meta_graph.getInOutEdges(comp_n):
		root[UBIQUITOUS][e] = root[UBIQUITOUS][list(root[VIEW_META_GRAPH][e])[0]]
	return comp_n


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