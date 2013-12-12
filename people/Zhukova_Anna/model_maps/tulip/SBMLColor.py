from tulip import *
import tulipplugins
import colorsys

grey = tlp.Color(200, 200, 200)
light_red = tlp.Color(255, 100, 100)
light_blue = tlp.Color(100, 100, 255)
white = tlp.Color(255, 255, 255)
transparent = tlp.Color(0, 0, 0, 0)

class SBMLColor(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return (True, "")

	def run(self):
		root = self.graph.getRoot()	
		organelles = root.getAttribute("organelles").split(";")
		cyto = root.getAttribute("cytoplasm")
		
		ubiquitous =  self.graph.getBooleanProperty("ubiquitous")
		viewColor =  self.graph.getColorProperty("viewColor")
		compartment = self.graph.getStringProperty("compartment")
		viewBorderColor =  self.graph.getColorProperty("viewBorderColor")
		viewBorderWidth =  self.graph.getDoubleProperty("viewBorderWidth")
		
#		viewColor.setAllNodeValue(grey)
		viewColor.setAllEdgeValue(grey)
		viewBorderWidth.setAllNodeValue(2)
		
		orgcyto = organelles + [cyto]
		i = len(organelles) + 2
		colors = [colorsys.hsv_to_rgb(x * 1.0 / i, 0.5, 0.8) for x in range(i)]
		colors = [tlp.Color(int(255 * r), int(255 *g), int(255 *b), 255) for (r,g,b) in colors]	
		i2color = dict(zip(organelles, colors[2:]))
		c_color = colors[1]
		i2color[cyto] = c_color
		ex_color = colors[0]
		
		get_col = lambda comp: i2color[comp] if comp in orgcyto else ex_color
		for n in self.graph.getNodes():			
			comp = compartment[n]
			c = get_col(comp)
			type_ = self.graph['type'][n]
			if 'compartment' == type_:
				viewColor[n] = transparent
				viewBorderColor[n] = grey
				continue
			if not type_ in ['reaction', 'species']:
				viewBorderColor[n] == transparent
				continue
			if self.graph.isMetaNode(n):
				viewColor[n] = tlp.Color(c.getR(), c.getG(), c.getB(), 80)
			else:
				viewColor[n] = c if not ubiquitous[n] else grey
			cs = {get_col(compartment[m]) for m in self.graph.getInOutNodes(n)} - {c}
			viewBorderColor[n] = cs.pop() if cs else viewColor[n]
			
			for e in self.graph.getInOutEdges(n):
				if not ubiquitous[self.graph.source(e)] and not ubiquitous[self.graph.target(e)]:
					viewColor[e] = viewColor[n]
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLColor", "SBMLColor", "anna", "09/12/2013", "", "1.0", "Metabolic")
