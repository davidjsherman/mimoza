from tulip import *
import tulipplugins
sp_size = 2
ub_sp_size = 2.5
r_size = 1.5

ub_e_size = 0.8
e_size = 0.5


class SBMLResizer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return (True, "")

	def run(self):
		viewSize = self.graph.getSizeProperty("viewSize")
		for n in self.graph.getNodes():		
			viewSize[n] = get_n_size(self.graph, n)	
		for e in self.graph.getEdges():		
			viewSize[e] = get_e_size(self.graph, e)	
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLResizer", "SBMLResizer", "anna", "09/12/2013", "", "1.0", "Metabolic")


def get_n_size(graph, n):
	ubiquitous =  graph.getBooleanProperty("ubiquitous")
	viewMetaGraph = graph.getGraphProperty("viewMetaGraph")
	num = 1
	if graph.isMetaNode(n):
		num = viewMetaGraph[n].numberOfNodes()
	if 'reaction' == graph['type'][n]:
		s = r_size * num
	elif ubiquitous[n]:
		s = ub_sp_size
	else:
		s = sp_size * num
		if s < ub_sp_size: s = ub_sp_size
	return tlp.Size(s, s)
	
	
def get_e_size(graph, e):
	ubiquitous =  graph.getBooleanProperty("ubiquitous")
	viewMetaGraph = graph.getGraphProperty("viewMetaGraph")
	num = 1
	if graph.isMetaEdge(e):
		num = len(viewMetaGraph[e])
	if ubiquitous[graph.source(e)] or ubiquitous[graph.target(e)]:
		s = ub_e_size
	else:
		s = e_size * num
		if s < ub_e_size: s = ub_e_size
	return tlp.Size(s, s)

	
def resize_edges(graph): 	
	viewSize =  graph.getSizeProperty("viewSize")
	viewSrcAnchorSize =  graph.getSizeProperty("viewSrcAnchorSize")
	viewTgtAnchorSize =  graph.getSizeProperty("viewTgtAnchorSize")
	viewMetaGraph = graph.getGraphProperty("viewMetaGraph")
			
	for n in (n for n in graph.getNodes() if 'reaction' == graph['type'][n]):
		num = 1
		if graph.isMetaNode(n):
			num = viewMetaGraph[n].numberOfNodes()
		sz = e_size * num
		if sz < ub_e_size: sz = ub_e_size
		for e in graph.getInOutEdges(n):
			if graph["ubiquitous"][graph.source(e)] or graph["ubiquitous"][graph.target(e)]:
				sz = ub_e_size
			viewSize[e] = tlp.Size(sz, sz)
			viewTgtAnchorSize[e] = viewSrcAnchorSize[e] = tlp.Size(sz * 0.6, sz * 0.8)
