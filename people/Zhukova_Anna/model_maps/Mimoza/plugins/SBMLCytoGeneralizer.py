from tulip import *
import tulipplugins
from modules.factoring import comp_to_meta_node
from modules.graph_tools import find_subgraph_by_name


class SBMLCytoGeneralizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, ""

	def run(self):
		root = self.graph.getRoot()
		meta_graph = find_subgraph_by_name(root, "meta graph")
		cytoplasm = root.getAttribute("cytoplasm")
		extracellular = next(
			(root["compartment"][n] for n in meta_graph.getNodes() if cytoplasm != root["compartment"][n]),
			'extracellular')
		comp_to_meta_node(meta_graph, cytoplasm, ('', ''), extracellular)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLCytoGeneralizer", "SBMLCytoGeneralizer", "anna", "09/12/2013", "", "1.0",
                                   "Metabolic")
