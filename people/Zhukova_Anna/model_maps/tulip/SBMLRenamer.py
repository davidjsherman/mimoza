from tulip import *
import tulipplugins
from sbml_generalization.utils.obo_ontology import parse, get_chebi
from modules.rename import split_into_parts, get_short_name


class SBMLRenamer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, ""

	def run(self):
		onto = parse(get_chebi())
		shorten(self.graph, onto)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLRenamer", "SBMLRenamer", "anna", "09/12/2013", "", "1.0", "Metabolic")


def shorten(graph, onto):		
	for n in graph.getNodes():
		graph["viewLabel"][n] = split_into_parts(get_short_name(graph, n, onto))
