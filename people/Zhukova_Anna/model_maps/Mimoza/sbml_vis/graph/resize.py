from tulip import *
from sbml_vis.graph.graph_properties import *

SPECIES_SIZE = 2.5
UBIQUITOUS_SPECIES_SIZE = 2

REACTION_SIZE = 1.5

UBIQUITOUS_EDGE_SIZE = 0.2
EDGE_SIZE = 0.5
COMP_EDGE_SIZE = 4


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
	return None


def get_mn_size(n, root):
	(m_x, m_y), (M_x, M_y) = get_min_max(root[VIEW_META_GRAPH][n])
	return M_x - m_x, M_y - m_y


def get_n_size(graph, n):
	root = graph.getRoot()
	n_type = root[TYPE][n]
	if TYPE_REACTION == n_type:
		if root[FAKE][n]:
			w, h = get_mn_size(n, root)
		else:
			w = h = REACTION_SIZE * get_n_length(graph, n)
	elif TYPE_COMPARTMENT == n_type:
		w, h = get_mn_size(n, root)
	elif root[UBIQUITOUS][n]:
		w = h = UBIQUITOUS_SPECIES_SIZE
	else:
		w = h = SPECIES_SIZE * get_n_length(graph, n)
	return tlp.Size(w, h)


def get_e_size(graph, e):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	if ubiquitous[e]:
		return tlp.Size(UBIQUITOUS_EDGE_SIZE, UBIQUITOUS_EDGE_SIZE)
	l = get_e_length(graph, e)
	sz = EDGE_SIZE * l if l else COMP_EDGE_SIZE
	return tlp.Size(sz, sz)


def get_comp_size(graph, n):
	root = graph.getRoot()
	view_meta_graph = root.getGraphProperty(VIEW_META_GRAPH)
	comp_graph = view_meta_graph[n]
	bb = tlp.computeBoundingBox(comp_graph)
	return tlp.Size(bb.width() * 1.1, bb.height() * 1.1)


def resize_edges(graph):
	root = graph.getRoot()
	for e in graph.getEdges():
		root[VIEW_SIZE][e] = get_e_size(graph, e)


def resize_nodes(graph):
	root = graph.getRoot()
	for n in graph.getNodes():
		root[VIEW_SIZE][n] = get_n_size(graph, n)


def resize(graph):
	resize_nodes(graph)
	resize_edges(graph)


def get_min_max(graph, margin=0):
	root = graph.getRoot()
	(m_x, m_y), (M_x, M_y) = (None, None), (None, None)

	for n in graph.getNodes():
		x, y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
		w, h = root[VIEW_SIZE][n].getW() / 2, root[VIEW_SIZE][n].getH() / 2
		if m_x is None or x - w < m_x:
			m_x = x - w
		if M_x is None or x + w > M_x:
			M_x = x + w
		if m_y is None or y - h < m_y:
			m_y = y - h
		if M_y is None or y + h > M_y:
			M_y = y + h

	w, h = M_x - m_x, M_y - m_y
	if w > h:
		m_y -= (w - h) / 2
		M_y += (w - h) / 2
	elif h > w:
		m_x -= (h - w) / 2
		M_x += (h - w) / 2

	return (m_x - margin, m_y - margin), (M_x + margin, M_y + margin)

