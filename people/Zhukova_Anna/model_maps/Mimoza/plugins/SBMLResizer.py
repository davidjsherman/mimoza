import tulipplugins

from tulip import *
from sbml_vis.tulip.resize import resize


class SBMLResizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, " "

	def run(self):
		resize(self.graph)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLResizer", "SBMLResizer", "anna", "09/12/2013", "", "1.0", "Metabolic")
