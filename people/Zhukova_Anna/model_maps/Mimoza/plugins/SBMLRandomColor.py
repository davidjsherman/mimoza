import tulipplugins

from tulip import *
from tulip import color


class SBMLRandomColor(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, ""

	def run(self):
		graph = self.graph.getRoot()
		color(graph)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLRandomColor", "SBMLRandomColor", "anna", "13/12/2013", "", "1.0", "Metabolic")
