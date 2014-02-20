from collections import defaultdict
import tulipgui
from tulip import tlp
from modules.merge_inside_comp import mic
from modules.model_utils import merge_nodes
from modules.resize import get_n_size, resize_edges

__author__ = 'anna'


def factor_nodes(graph):
	root = graph.getRoot()
	clone = root.inducedSubGraph(list(graph.getNodes()))

	ancestor2nodes = defaultdict(list)
	for node in graph.getNodes():
		ancestor = root["ancestor_id"][node]
		if ancestor:
			ancestor = ancestor, root["type"][node], root["compartment"][node]
			ancestor2nodes[ancestor].append(node)

	is_ubiquitous = root["ubiquitous"]
	for (ancestor, type_, comp), nodes in ancestor2nodes.iteritems():
		if len(nodes) <= 1:
			continue
		all_nodes = list(nodes)
		id2ub_ns = defaultdict(set)
		if 'reaction' == type_:
			for node in nodes:
				for n in (n for n in graph.getInOutNodes(node) if is_ubiquitous[n]):
					id2ub_ns[root["id"][n]].add(n)
			for ubs in id2ub_ns.itervalues():
				merge_nodes(graph, ubs)

		meta_node = graph.createMetaNode(all_nodes, False)
		mg = graph["viewMetaGraph"][meta_node]
		n = nodes[0]

		for prop in ["compartment", "type", "reversible", "ubiquitous", "viewBorderColor", "viewBorderWidth",
		             "viewColor", "viewLabelColor", "viewLayout", "viewSelection", "viewShape", "clone"]:
			root[prop][meta_node] = root[prop][n]
		root["id"][meta_node] = root["ancestor_id"][n]
		root["name"][meta_node] = root["ancestor_name"][n]
		root["viewSize"][meta_node] = get_n_size(root, meta_node)

		if 'reaction' == type_:
			mg.setName("generalized {0} ({1})".format(root["name"][n], len(nodes)))
			root["reversible"][meta_node] = True
			for n in nodes:
				if not root["reversible"][n]:
					root["reversible"][meta_node] = False
					break
			root["geneAssociation"][meta_node] = "\nor\n".join({root["geneAssociation"][it] for it in nodes})
		else:
			mg.setName("{0} ({1})".format(root["ancestor_name"][n], len(nodes)))
			root["chebi_id"][meta_node] = root["ancestor_chebi_id"][n]

		root["viewLabel"][meta_node] = mg.getName()
		root["name"][meta_node] = root["viewLabel"][meta_node]

	root.delSubGraph(clone)
	for n in (n for n in graph.getNodes() if 'reaction' == root['type'][n] and graph.isMetaNode(n)):
		for e in graph.getInOutEdges(n):
			root['stoichiometry'][e] = root['stoichiometry'][list(root["viewMetaGraph"][e])[0]]

	resize_edges(graph)


def comp_to_meta_node(meta_graph, comp, out_comp):
	root = meta_graph.getRoot()
	ns = filter(lambda n: root["compartment"][n] == comp, meta_graph.getNodes())
	comp_graph = meta_graph.getSuperGraph().inducedSubGraph(ns)
	bb = tlp.computeBoundingBox(comp_graph)
	meta_node = meta_graph.createMetaNode(comp_graph, False)
	comp_graph.setName("_" + comp)
	root["viewSize"][meta_node] = tlp.Size(bb.width(), bb.height())
	root["viewLayout"][meta_node] = bb.center()
	root["viewLabel"][meta_node] = comp
	root["name"][meta_node] = comp
	root["compartment"][meta_node] = out_comp
	root["type"][meta_node] = 'compartment'
	root["viewShape"][meta_node] = 18
	root["viewColor"][meta_node] = tlp.Color(200, 200, 200, 80)
	return meta_node


def factor_comps(meta_graph):
	mic(meta_graph)
	root = meta_graph.getRoot()
	cytoplasm = root.getAttribute("cytoplasm")
	organelle2meta_node = {}
	for organelle in root.getAttribute("organelles").split(";"):
		meta_node = comp_to_meta_node(meta_graph, organelle, cytoplasm)
		organelle2meta_node[organelle] = meta_node
	resize_edges(meta_graph)
	return organelle2meta_node


def factor_cytoplasm(meta_graph):
	root = meta_graph.getRoot()
	cytoplasm = root.getAttribute("cytoplasm")
	meta_node = comp_to_meta_node(meta_graph, cytoplasm, 'extracellular')
	resize_edges(meta_graph)
	return cytoplasm, meta_node