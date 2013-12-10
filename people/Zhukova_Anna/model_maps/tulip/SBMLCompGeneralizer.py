from tulip import *
import tulipplugins
from merge_inside_comp import mic
from graph_tools import findSubGraphByName, comp_to_meta_node

class SBMLCompGeneralizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return (True, "")

	def run(self):
		mic(self.graph)
		factor_comps(self.graph)		
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLCompGeneralizer", "SBMLCompGeneralizer", "anna", "09/12/2013", "", "1.0", "Metabolic")


def factor_comps(graph):
	root = graph.getRoot()
	meta_graph = findSubGraphByName(root, "meta graph")
	cyto = root.getAttribute("cytoplasm")
	for it in root.getAttribute("organelles").split(";"):
		comp_to_meta_node(meta_graph, it, cyto)
