import tulipplugins

from tulip import *
from tulip.resize import get_n_size, get_e_size


class SBMLResizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, ""

	def run(self):
		view_size = self.graph.getRoot().getSizeProperty("viewSize")
		for n in self.graph.getNodes():		
			view_size[n] = get_n_size(self.graph, n)
		for e in self.graph.getEdges():		
			view_size[e] = get_e_size(self.graph, e)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLResizer", "SBMLResizer", "anna", "09/12/2013", "", "1.0", "Metabolic")
