from tulip import *
from modules.graph_properties import *

sp_size = 2.5
ub_sp_size = 2
r_size = 1.5

ub_e_size = 0.5
e_size = 0.8


def get_n_length(graph, n):
	view_meta_graph = graph.getRoot().getGraphProperty(VIEW_META_GRAPH)
	return view_meta_graph[n].numberOfNodes() if graph.isMetaNode(n) else 1


def get_e_length(graph, e):
	s, t = graph.source(e), graph.target(e)
	r = s if TYPE_REACTION == graph.getRoot()[TYPE][s] else t
	return get_n_length(graph, r)


def get_n_size(graph, n):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	view_meta_graph = root.getGraphProperty(VIEW_META_GRAPH)

	n_type = root[TYPE][n]
	s = 0
	if TYPE_REACTION == n_type:
		s = r_size * get_n_length(graph, n)
	elif TYPE_COMPARTMENT == n_type:
		bb = tlp.computeBoundingBox(view_meta_graph[n])
		s = max(bb.width(), bb.height())
	elif ubiquitous[n]:
		s = ub_sp_size
	else:
		s = sp_size * get_n_length(graph, n)
	return tlp.Size(s, s)


def get_e_size(graph, e):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	if ubiquitous[e]:
		return ub_e_size
	return e_size * get_e_length(graph, e)


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


def resize_nodes(graph):
	root = graph.getRoot()
	view_size = root.getSizeProperty(VIEW_SIZE)

	for n in graph.getNodes():
		view_size[n] = get_n_size(graph, n)


def resize(graph):
	resize_nodes(graph)
	resize_edges(graph)

