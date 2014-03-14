from tulip import *
import tulipplugins
import colorsys
from modules.graph_tools import *

grey = tlp.Color(200, 200, 200)
transparent_grey = tlp.Color(200, 200, 200, 80)
light_red = tlp.Color(255, 100, 100)
light_blue = tlp.Color(100, 100, 255)
white = tlp.Color(255, 255, 255)
transparent = tlp.Color(0, 0, 0, 0)


class SBMLColor(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return True, ""

	def run(self):
		root = self.graph.getRoot()	
		organelles = root.getAttribute(ORGANELLES).split(";")
		cytoplasm = root.getAttribute(CYTOPLASM)
		
		ubiquitous = root.getBooleanProperty(UBIQUITOUS)
		view_color = root.getColorProperty(VIEW_COLOR)
		compartment = root.getStringProperty(COMPARTMENT)
		
		compartments = organelles + [cytoplasm]
		i = len(organelles) + 2
		colors = [colorsys.hsv_to_rgb(x * 1.0 / i, 0.5, 0.8) for x in range(i)]
		colors = [tlp.Color(int(255 * r), int(255 * g), int(255 * b), 255) for (r, g, b) in colors]
		i2color = dict(zip(organelles, colors[2:]))
		c_color = colors[1]
		i2color[cytoplasm] = c_color
		ex_color = colors[0]
		
		get_col = lambda comp: i2color[comp] if comp in compartments else ex_color
		for n in self.graph.getNodes():			
			comp = compartment[n]
			c = get_col(comp)
			type_ = self.graph[TYPE][n]
			if TYPE_COMPARTMENT == type_:
				view_color[n] = transparent_grey
				continue
			if not type_ in [TYPE_SPECIES, TYPE_REACTION]:
				continue
			if self.graph.isMetaNode(n):
				view_color[n] = tlp.Color(c.getR(), c.getG(), c.getB(), 80)
			else:
				view_color[n] = c if not ubiquitous[n] else grey
			
			for e in self.graph.getInOutEdges(n):
				if not ubiquitous[self.graph.source(e)] and not ubiquitous[self.graph.target(e)]:
					view_color[e] = view_color[n]
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLColor", "SBMLColor", "anna", "09/12/2013", "", "1.0", "Metabolic")
