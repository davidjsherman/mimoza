import tulipplugins

from tulip import *
from tulip.cluster.factoring import factor_nodes


class SBMLGeneralizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, ""

	def run(self):
		ns = list(self.graph.getNodes())
		meta_graph = self.graph.inducedSubGraph(ns)
		meta_graph.setName("meta graph")
		original_graph = self.graph.inducedSubGraph(ns)
		original_graph.setName("full graph")
		factor_nodes(meta_graph)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLGeneralizer", "SBMLGeneralizer", "anna", "09/12/2013", "", "1.0", "Metabolic")


