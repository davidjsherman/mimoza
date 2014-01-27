from tulip import tlp
from modules.graph_tools import getSize
from modules.merge_inside_comp import mic
from modules.model_utils import merge_nodes
from modules.resize import get_n_size, resize_edges

__author__ = 'anna'


def factor_nodes(graph):
	root = graph.getRoot()
	clone = root.inducedSubGraph(list(graph.getNodes()))

	ancestor2nodes = {}
	for node in graph.getNodes():
		ancestor = graph["ancestor_id"][node]
		if ancestor:
			ancestor = ancestor, graph["type"][node], graph["compartment"][node]
			if ancestor2nodes.has_key(ancestor):
				ancestor2nodes[ancestor].append(node)
			else:
				ancestor2nodes[ancestor] = [node]

	isUb = graph["ubiquitous"]
	for (ancestor, type_, comp), nodes in ancestor2nodes.iteritems():
		if len(nodes) <= 1:
			continue
		all_nodes = list(nodes)
		id2ubN = {}
		if 'reaction' == type_:
			for node in nodes:
				for n in (n for n in graph.getInOutNodes(node) if isUb[n]):
					id_ = graph["id"][n]
					if id2ubN.has_key(id_):
						id2ubN[id_].append(n)
					else:
						id2ubN[id_] = [n]
			for ubs in id2ubN.itervalues():
				merge_nodes(graph, ubs)

		metaNode = graph.createMetaNode(all_nodes, False)
		mg = graph["viewMetaGraph"][metaNode]
		n = nodes[0]

		for prop in ["compartment", "type", "reversible", "ubiquitous", "viewBorderColor", "viewBorderWidth", "viewColor",\
	             "viewLabelColor", "viewLayout", "viewSelection", "viewShape", "clone"]:
			graph[prop][metaNode] = clone[prop][n]
		graph["id"][metaNode] = clone["ancestor_id"][n]
		graph["name"][metaNode] = clone["ancestor_name"][n]
		root["viewSize"][metaNode] = get_n_size(root, metaNode)

		if 'reaction' == type_:
			mg.setName("generalized {0} ({1})".format(clone["name"][n], len(nodes)))
			root["reversible"][metaNode] = True
			for n in nodes:
				if not clone["reversible"][n]:
					root["reversible"][metaNode] = False
					break
			root["geneAssociation"][metaNode] = "\nor\n".join({clone["geneAssociation"][it] for it in nodes})
		else:
			mg.setName("{0} ({1})".format(clone["ancestor_name"][n], len(nodes)))
			root["chebi_id"][metaNode] = clone["ancestor_chebi_id"][n]

		root["viewLabel"][metaNode] = mg.getName()
		root["name"][metaNode] = root["viewLabel"][metaNode]

	root.delSubGraph(clone)
	for n in (n for n in graph.getNodes() if 'reaction' == graph['type'][n] and graph.isMetaNode(n)):
		for e in graph.getInOutEdges(n):
			graph['stoichiometry'][e] = graph['stoichiometry'][list(graph["viewMetaGraph"][e])[0]]

	resize_edges(graph)


def comp_to_meta_node(meta_graph, comp, out_comp):
	ns = filter(lambda n: meta_graph["compartment"][n] == comp, meta_graph.getNodes())
	meta_node = meta_graph.createMetaNode(ns, False)
	comp_graph = meta_graph["viewMetaGraph"][meta_node]
	comp_graph.setName("_" + comp)
	meta_graph["viewSize"][meta_node] = getSize(comp_graph)
	meta_graph["viewLabel"][meta_node] = comp
	meta_graph["name"][meta_node] = comp
	meta_graph["compartment"][meta_node] = out_comp
	meta_graph["type"][meta_node] = 'compartment'
	meta_graph["viewShape"][meta_node] = 18
	meta_graph["viewColor"][meta_node] = tlp.Color(200, 200, 200, 80)
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


def factor_cyto(meta_graph):
	root = meta_graph.getRoot()
	cytoplasm = root.getAttribute("cytoplasm")
	meta_node = comp_to_meta_node(meta_graph, cytoplasm, 'extracellular')
	resize_edges(meta_graph)
	return cytoplasm, meta_node