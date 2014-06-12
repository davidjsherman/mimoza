import tulipplugins

from tulip import *
from converter.tlp2geojson import tulip2geojson


class SBML2GeoJSNExport(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)
		self.addStringParameter("file::GeoJSON", "GeoJSON file to be exported.", "")

	def check(self):
		return True, ""

	def run(self):
		tulip2geojson(self.graph, self.dataSet["file::GeoJSON"])
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBML2GeoJSNExport", "SBML2GeoJSNExport", "anna", "10/12/2013", "", "1.0",
                                   "Metabolic")





