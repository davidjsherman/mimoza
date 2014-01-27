from tulip import *
import tulipplugins
from modules.factoring import comp_to_meta_node
from modules.graph_tools import findSubGraphByName


class SBMLCytoGeneralizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return (True, "")

	def run(self):
		root = self.graph.getRoot()
		meta_graph = findSubGraphByName(root, "meta graph")
		cyto = root.getAttribute("cytoplasm")
		extracellular = 'extracellular'
		for n in meta_graph.getNodes():
			if cyto != meta_graph["compartment"][n]:
				extracellular = meta_graph["compartment"][n]
			break
		comp_to_meta_node(meta_graph, cyto, extracellular)	
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLCytoGeneralizer", "SBMLCytoGeneralizer", "anna", "09/12/2013", "", "1.0", "Metabolic")
