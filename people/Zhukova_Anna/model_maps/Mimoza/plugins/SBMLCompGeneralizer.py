import tulipplugins

from tulip import *
from tulip.cluster.factoring import factor_comps
from sbml_vis.graph_tools import find_subgraph_by_name


class SBMLCompGeneralizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, ""

	def run(self):
		meta_graph = find_subgraph_by_name(self.graph.getRoot(), "meta graph")
		factor_comps(meta_graph, {})
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLCompGeneralizer", "SBMLCompGeneralizer", "anna", "09/12/2013", "", "1.0", "Metabolic")

