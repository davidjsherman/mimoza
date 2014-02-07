from tulip import *

sp_size = 2.5
ub_sp_size = 2
r_size = 1.5

ub_e_size = 0.5
e_size = 0.8

	
def get_n_size(graph, n):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty("ubiquitous")
	view_meta_graph = root.getGraphProperty("viewMetaGraph")
	num = 1
	if graph.isMetaNode(n):
		num = view_meta_graph[n].numberOfNodes()
	if 'reaction' == root['type'][n]:
		s = r_size * num
	elif ubiquitous[n]:
		s = ub_sp_size
	else:
		s = sp_size * num
	return tlp.Size(s, s)


def get_e_size(graph, e):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty("ubiquitous")
	view_meta_graph = root.getGraphProperty("viewMetaGraph")
	s, t = graph.source(e), graph.target(e)
	if ubiquitous[s] or ubiquitous[t]:
		return ub_e_size
	n = s if 'reaction' == root['type'][s] else t
	num = 1
	if graph.isMetaNode(n):
		num = view_meta_graph[n].numberOfNodes()
	return e_size * num


def get_comp_size(graph, n):
	root = graph.getRoot()
	view_meta_graph = root.getGraphProperty("viewMetaGraph")
	comp_graph = view_meta_graph[n]
	bb = tlp.computeBoundingBox(comp_graph)
	return tlp.Size(bb.width() * 1.1 , bb.height() * 1.1)


def resize_edges(graph):
	root = graph.getRoot()
	view_size = root.getSizeProperty("viewSize")
	view_src_anchor_size = root.getSizeProperty("viewSrcAnchorSize")
	view_tgt_anchor_size = root.getSizeProperty("viewTgtAnchorSize")
			
	for e in graph.getEdges():
		sz = get_e_size(graph, e)
		view_size[e] = tlp.Size(sz, sz)
		view_tgt_anchor_size[e] = view_src_anchor_size[e] = tlp.Size(sz * 0.6, sz * 0.8)
