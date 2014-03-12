from collections import defaultdict
from tulip import tlp
from modules.merge_inside_comp import mic
from modules.model_utils import merge_nodes
from modules.resize import get_n_size, resize_edges
from modules.graph_tools import *

__author__ = 'anna'


def merge_ubs_for_similar_reactions(graph):
	root = graph.getRoot()

	ancestor2nodes = defaultdict(list)
	for node in graph.getNodes():
		ancestor = root[ANCESTOR_ID][node]
		if ancestor and TYPE_REACTION == root[TYPE][node]:
			ancestor = ancestor, root[TYPE_COMPARTMENT][node]
			ancestor2nodes[ancestor].append(node)

	is_ubiquitous = root[UBIQUITOUS]
	for nodes in ancestor2nodes.itervalues():
		if len(nodes) <= 1:
			continue
		id2ub_ns = defaultdict(set)
		for node in nodes:
			for n in (n for n in graph.getInOutNodes(node) if is_ubiquitous[n]):
				id2ub_ns[root[ID][n]].add(n)
		for ubs in id2ub_ns.itervalues():
			merge_nodes(root, ubs)


def factor_nodes(graph):
	root = graph.getRoot()
	clone = root.inducedSubGraph(list(graph.getNodes()))

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

		for prop in [COMPARTMENT, TYPE, REVERSIBLE, UBIQUITOUS, VIEW_BORDER_COLOR, VIEW_BORDER_WIDTH,
		             VIEW_COLOR, VIEW_LAYOUT, VIEW_SELECTION, VIEW_SHAPE, CLONE]:
			root[prop][meta_node] = root[prop][n]
		root[ID][meta_node] = root[ANCESTOR_ID][n]
		root[NAME][meta_node] = root[ANCESTOR_NAME][n]
		root[VIEW_SIZE][meta_node] = get_n_size(root, meta_node)

		if TYPE_REACTION == type_:
			mg.setName("generalized {0} ({1})".format(root[NAME][n], len(nodes)))
			root[REVERSIBLE][meta_node] = True
			for n in nodes:
				if not root[REVERSIBLE][n]:
					root[REVERSIBLE][meta_node] = False
					break
			root[GENE_ASSOCIATION][meta_node] = "\nor\n".join({root[GENE_ASSOCIATION][it] for it in nodes})
		else:
			mg.setName("{0} ({1})".format(root[ANCESTOR_NAME][n], len(nodes)))
			root[TERM_ID][meta_node] = root[ANCESTOR_TERM_ID][n]

		root[VIEW_LABEL][meta_node] = mg.getName()
		root[NAME][meta_node] = root[VIEW_LABEL][meta_node]

	root.delSubGraph(clone)
	for n in (n for n in graph.getNodes() if TYPE_REACTION == root[TYPE][n] and graph.isMetaNode(n)):
		for e in graph.getInOutEdges(n):
			root[STOICHIOMETRY][e] = root[STOICHIOMETRY][list(root[VIEW_META_GRAPH][e])[0]]

	resize_edges(graph)


def nodes_to_meta_node(comp, meta_graph, ns, (c_id, go_id), out_comp):
	if not ns:
		return None
	root = meta_graph.getRoot()
	comp_graph = meta_graph.getSuperGraph().inducedSubGraph(ns)
	bb = tlp.computeBoundingBox(comp_graph)
	w, h = bb.width(), bb.height()
	meta_node = meta_graph.createMetaNode(comp_graph, False)
	comp_graph.setName("_" + comp)
	root[VIEW_SIZE][meta_node] = tlp.Size(w, h)
	root[VIEW_LAYOUT][meta_node] = bb.center()
	root[VIEW_LABEL][meta_node] = comp
	root[NAME][meta_node] = comp
	root[COMPARTMENT][meta_node] = out_comp
	root[TYPE][meta_node] = TYPE_COMPARTMENT
	root[VIEW_SHAPE][meta_node] = SQUARE_SHAPE
	root[ID][meta_node] = c_id
	root[TERM_ID][meta_node] = go_id
	root[VIEW_COLOR][meta_node] = tlp.Color(200, 200, 200, 80)
	return meta_node


def comp_to_meta_node(meta_graph, comp, (c_id, go_id), out_comp):
	root = meta_graph.getRoot()
	ns = filter(lambda n: root[COMPARTMENT][n] == comp, meta_graph.getNodes())
	return nodes_to_meta_node(comp, meta_graph, ns, (c_id, go_id), out_comp)


def factor_comps(meta_graph, c_name2id_go):
	mic(meta_graph)
	root = meta_graph.getRoot()
	cytoplasm = root.getAttribute(CYTOPLASM)
	organelle2meta_node = {}
	for organelle in root.getAttribute(ORGANELLES).split(";"):
		meta_node = comp_to_meta_node(meta_graph, organelle, c_name2id_go[organelle], cytoplasm)
		if meta_node:
			organelle2meta_node[organelle] = meta_node
	resize_edges(meta_graph)
	return organelle2meta_node


def factor_cytoplasm(meta_graph, c_name2id_go):
	root = meta_graph.getRoot()
	cytoplasm = root.getAttribute(CYTOPLASM)
	meta_node = comp_to_meta_node(meta_graph, cytoplasm, c_name2id_go[cytoplasm], EXTRACELLULAR)
	resize_edges(meta_graph)
	return cytoplasm, meta_node