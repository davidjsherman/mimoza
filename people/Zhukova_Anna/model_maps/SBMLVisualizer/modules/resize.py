from tulip import *
from modules.graph_tools import *

sp_size = 2.5
ub_sp_size = 2
r_size = 1.5

ub_e_size = 0.5
e_size = 0.8

	
def get_n_size(graph, n):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	view_meta_graph = root.getGraphProperty(VIEW_META_GRAPH)
	num = 1
	if graph.isMetaNode(n):
		num = view_meta_graph[n].numberOfNodes()
	if TYPE_REACTION == root[TYPE][n]:
		s = r_size * num
	elif ubiquitous[n]:
		s = ub_sp_size
	else:
		s = sp_size * num
	return tlp.Size(s, s)


def get_e_size(graph, e):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	view_meta_graph = root.getGraphProperty(VIEW_META_GRAPH)
	s, t = graph.source(e), graph.target(e)
	if ubiquitous[s] or ubiquitous[t]:
		return ub_e_size
	n = s if TYPE_REACTION == root[TYPE][s] else t
	num = 1
	if graph.isMetaNode(n):
		num = view_meta_graph[n].numberOfNodes()
	return e_size * num


def get_comp_size(graph, n):
	root = graph.getRoot()
	view_meta_graph = root.getGraphProperty(VIEW_META_GRAPH)
	comp_graph = view_meta_graph[n]
	bb = tlp.computeBoundingBox(comp_graph)
	return tlp.Size(bb.width() * 1.1, bb.height() * 1.1)


def resize_edges(graph):
	root = graph.getRoot()
	view_size = root.getSizeProperty(VIEW_SIZE)
			
	for e in graph.getEdges():
		sz = get_e_size(graph, e)
		view_size[e] = tlp.Size(sz, sz)
