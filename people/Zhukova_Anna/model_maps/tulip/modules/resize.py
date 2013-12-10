from tulip import *

sp_size = 2
ub_sp_size = 2.5
r_size = 1.5

ub_e_size = 0.8
e_size = 0.5

def main(graph):
	resize(graph)
	resize_edges(graph)
	
def get_n_size(graph, n):
	ubiquitous =  graph.getBooleanProperty("ubiquitous")
	viewSize =  graph.getSizeProperty("viewSize")
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
	
	
def resize(graph): 
	viewSize =  graph.getSizeProperty("viewSize")
	resizeLabels(graph)
	for n in graph.getNodes():		
		viewSize[n] = get_n_size(graph, n)		
	viewSize.setAllEdgeValue(tlp.Size(0.5, 0.5))

	
def resize_edges(graph): 	
	name = graph.getStringProperty("name")
	reaction =  graph.getBooleanProperty("reaction")
	clone =  graph.getBooleanProperty("clone")
	viewSize =  graph.getSizeProperty("viewSize")
	viewSrcAnchorShape =  graph.getIntegerProperty("viewSrcAnchorShape")
	viewSrcAnchorSize =  graph.getSizeProperty("viewSrcAnchorSize")
	viewTgtAnchorShape =  graph.getIntegerProperty("viewTgtAnchorShape")
	viewTgtAnchorSize =  graph.getSizeProperty("viewTgtAnchorSize")
	viewMetaGraph = graph.getGraphProperty("viewMetaGraph")
			
	for n in graph.getNodes():
		if reaction[n]:
			num = 1
			if graph.isMetaNode(n):
				num = viewMetaGraph[n].numberOfNodes()
			sz = e_size * num
			if sz < ub_e_size: sz = ub_e_size
			for e in graph.getInOutEdges(n):
				viewSize[e] = tlp.Size(sz, sz)
				viewTgtAnchorSize[e] = viewSrcAnchorSize[e] = tlp.Size(sz * 0.6, sz * 0.8)
	for n in graph.getNodes():
		if graph["ubiquitous"][n]:
			for e in graph.getInOutEdges(n):
				viewSize[e] = tlp.Size(ub_e_size, ub_e_size)
				viewTgtAnchorSize[e] = viewSrcAnchorSize[e] = tlp.Size(ub_e_size * 0.6, ub_e_size * 0.8)
		
def resizeLabels(graph):
	reaction =  graph.getBooleanProperty("reaction")
	ubiquitous =  graph.getBooleanProperty("ubiquitous")
	viewFontSize =  graph.getIntegerProperty("viewFontSize")
	metric = graph.getDoubleProperty("metric")
	viewBorderWidth =  graph.getDoubleProperty("viewBorderWidth")
	viewBorderColor =  graph.getColorProperty("viewBorderColor")

	white = tlp.Color(255,255,255)
	grey = tlp.Color(220,220,220)
	for n in graph.getNodes():
		viewBorderWidth[n] = 0
		viewBorderColor[n] = tlp.Color(0,0,0)
		if not reaction[n]:
			viewFontSize[n] = 10 if ubiquitous[n] else 52
			metric[n] = 1 if ubiquitous[n] else 20
		else:
			viewFontSize[n] = 6
			metric[n] = 0
			
	
