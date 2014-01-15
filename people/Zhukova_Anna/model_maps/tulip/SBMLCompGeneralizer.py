from tulip import *
import tulipplugins
from modules.factoring import factor_comps
from modules.graph_tools import findSubGraphByName


class SBMLCompGeneralizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return (True, "")

	def run(self):
		meta_graph = findSubGraphByName(self.graph.getRoot(), "meta graph")
		factor_comps(meta_graph)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLCompGeneralizer", "SBMLCompGeneralizer", "anna", "09/12/2013", "", "1.0", "Metabolic")

