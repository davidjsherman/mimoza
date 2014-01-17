from tulip import *

sp_size = 2.5
ub_sp_size = 2
r_size = 1.5

ub_e_size = 0.5
e_size = 0.8

	
def get_n_size(graph, n):
	ubiquitous = graph.getBooleanProperty("ubiquitous")
	view_meta_graph = graph.getGraphProperty("viewMetaGraph")
	num = 1
	if graph.isMetaNode(n):
		num = view_meta_graph[n].numberOfNodes()
	if 'reaction' == graph['type'][n]:
		s = r_size * num
	elif ubiquitous[n]:
		s = ub_sp_size
	else:
		s = sp_size * num
	return tlp.Size(s, s)


def get_e_size(graph, e):
	ubiquitous = graph.getBooleanProperty("ubiquitous")
	view_meta_graph = graph.getGraphProperty("viewMetaGraph")
	s, t = graph.source(e), graph.target(e)
	if ubiquitous[s] or ubiquitous[t]:
		return ub_e_size
	n = s if 'reaction' == graph['type'][s] else t
	num = 1
	if graph.isMetaNode(n):
		num = view_meta_graph[n].numberOfNodes()
	return e_size * num


def resize_edges(graph):
	view_size = graph.getSizeProperty("viewSize")
	view_src_anchor_size = graph.getSizeProperty("viewSrcAnchorSize")
	view_tgt_anchor_size = graph.getSizeProperty("viewTgtAnchorSize")
			
	for e in graph.getEdges():
		sz = get_e_size(graph, e)
		view_size[e] = tlp.Size(sz, sz)
		view_tgt_anchor_size[e] = view_src_anchor_size[e] = tlp.Size(sz * 0.6, sz * 0.8)
