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
	bb = tlp.computeBoundingBox(root[VIEW_META_GRAPH][n])
	return bb.width(), bb.height()


def get_n_size(graph, n):
	root = graph.getRoot()
	n_type = root[TYPE][n]
	if TYPE_REACTION == n_type:
		if root[FAKE][n]:
			w = h = max(get_mn_size(n, root))
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
