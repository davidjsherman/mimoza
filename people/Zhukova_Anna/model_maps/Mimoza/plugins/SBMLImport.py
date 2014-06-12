import traceback

from libsbml import SBMLReader
import tulipplugins

from tulip import *
from sbml_vis.converter.sbml2tlp import import_sbml


class SBMLImport(tlp.ImportModule):
	def __init__(self, context):
		tlp.ImportModule.__init__(self, context)
		self.addStringParameter("file::filename", "SBML model to import")

	def importGraph(self):
		try:
			sbml_file = self.dataSet["file::filename"]
			reader = SBMLReader()
			input_document = reader.readSBML(sbml_file)
			input_model = input_document.getModel()
			import_sbml(self.graph, input_model, sbml_file)
			return True
		# this is a workaround to avoid a crash from Tulip when an exception is raised
		# in the import code
		except:
			if self.pluginProgress:
				self.pluginProgress.setError(traceback.format_exc())
			return False


# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPlugin("SBMLImport", "SBMLImport", "anna", "06/12/2013", "", "1.0")
