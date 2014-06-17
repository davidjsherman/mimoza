from tulip import *
from sbml_vis.tulip.graph_properties import *

SPECIES_SIZE = 2.5
UBIQUITOUS_SPECIES_SIZE = 2
REACTION_SIZE = 1.5

UBIQUITOUS_EDGE_SIZE = 0.4
EDGE_SIZE = 0.5


def get_n_length(graph, n):
	view_meta_graph = graph.getRoot().getGraphProperty(VIEW_META_GRAPH)
	return view_meta_graph[n].numberOfNodes() if graph.isMetaNode(n) else 1


def get_e_length(graph, e):
	s, t = graph.source(e), graph.target(e)
	r = None
	if TYPE_REACTION == graph.getRoot()[TYPE][s]:
		r = s
	elif TYPE_REACTION == graph.getRoot()[TYPE][t]:
		r = t
	if r:
		return graph.getRoot()[VIEW_SIZE][r].getW() / REACTION_SIZE
	return len(list(graph.getRoot()[VIEW_META_GRAPH][e])) if graph.isMetaEdge(e) else 1


def get_n_size(graph, n):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	view_meta_graph = root.getGraphProperty(VIEW_META_GRAPH)

	n_type = root[TYPE][n]
	if TYPE_REACTION == n_type:
		s = REACTION_SIZE * get_n_length(graph, n)
	elif TYPE_COMPARTMENT == n_type:
		bb = tlp.computeBoundingBox(view_meta_graph[n])
		s = max(bb.width(), bb.height())
	elif ubiquitous[n]:
		s = UBIQUITOUS_SPECIES_SIZE
	else:
		s = SPECIES_SIZE * get_n_length(graph, n)
	return tlp.Size(s, s)


def get_e_size(graph, e):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	sz = UBIQUITOUS_EDGE_SIZE if ubiquitous[e] else EDGE_SIZE * get_e_length(graph, e)
	return tlp.Size(sz, sz)


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
		view_size[e] = get_e_size(graph, e)


def resize_nodes(graph):
	root = graph.getRoot()
	view_size = root.getSizeProperty(VIEW_SIZE)

	for n in graph.getNodes():
		view_size[n] = get_n_size(graph, n)


def resize(graph):
	resize_nodes(graph)
	resize_edges(graph)


def get_min_max(graph, margin=0):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty(VIEW_LAYOUT)
	view_size = root.getSizeProperty(VIEW_SIZE)
	m, M = view_layout.getMin(graph), view_layout.getMax(graph)
	(m_x, m_y), (M_x, M_y) = (m.getX(), m.getY()), (M.getX(), M.getY())

	for n in graph.getNodes():
		x, y = view_layout[n].getX(), view_layout[n].getY()
		w, h = view_size[n].getW() / 2, view_size[n].getH() / 2
		if x - w < m_x:
			m_x = x - w
		if x + w > M_x:
			M_x = x + w
		if y - h < m_y:
			m_y = y - h
		if y + h > M_y:
			M_y = y + h

	w, h = M_x - m_x, M_y - m_y
	if w > h:
		m_y -= (w - h) / 2
		M_y += (w - h) / 2
	elif h > w:
		m_x -= (h - w) / 2
		M_x += (h - w) / 2

	return (m_x - margin, m_y - margin), (M_x + margin, M_y + margin)

