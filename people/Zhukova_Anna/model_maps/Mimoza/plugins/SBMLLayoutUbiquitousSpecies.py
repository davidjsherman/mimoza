import tulipplugins

from tulip import *
from tulip.layout.layout_utils import layout_ub_sps


class SBMLLayoutUbiquitousSpecies(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, ""

	def run(self):
		layout_ub_sps(self.graph)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLLayoutUbiquitousSpecies", "SBMLLayoutUbiquitousSpecies", "anna", "19/12/2013",
                                   "", "1.0", "Metabolic")
