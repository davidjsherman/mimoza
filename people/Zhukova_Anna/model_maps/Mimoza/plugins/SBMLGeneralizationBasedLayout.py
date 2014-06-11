from tulip import *
import tulipplugins
from modules.layout_utils import layout_generalization_based


class SBMLGeneralizationBasedLayout(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, ""

	def run(self):
		layout_generalization_based(self.graph)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLGeneralizationBasedLayout", "SBMLGeneralizationBasedLayout", "anna",
                                   '09/12/2013', "", "1.0", "Metabolic")
					

