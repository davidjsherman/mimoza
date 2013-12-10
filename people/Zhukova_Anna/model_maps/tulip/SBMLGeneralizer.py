from tulip import *
import tulipplugins
from resize import resize_edges, get_n_size
from model_utils import merge_nodes

class SBMLGeneralizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return (True, "")

	def run(self):
		ns = list(self.graph.getNodes())
		meta_graph = self.graph.inducedSubGraph(ns)
		meta_graph.setName("meta graph")
		original_graph = self.graph.inducedSubGraph(ns)
		original_graph.setName("full graph")
		factor_nodes(meta_graph)
		resize_edges(meta_graph)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLGeneralizer", "SBMLGeneralizer", "anna", "09/12/2013", "", "1.0", "Metabolic")


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
		sz = root["viewSize"][n]
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
