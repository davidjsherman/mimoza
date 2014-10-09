from tulip import *
from sbml_vis.graph.graph_properties import *

SPECIES_SIZE = 2.5
UBIQUITOUS_SPECIES_SIZE = 2

REACTION_SIZE = 1.5

UBIQUITOUS_EDGE_SIZE = 0.5
EDGE_SIZE = 1
GENERALIZED_EDGE_SIZE = 2
COMP_EDGE_SIZE = 4


def get_n_length(graph, n):
	return graph.getRoot()[VIEW_META_GRAPH][n].numberOfNodes() if graph.isMetaNode(n) else 1


def _get_e_size(root, e):
	if root[UBIQUITOUS][e]:
		return UBIQUITOUS_EDGE_SIZE
	elif root.isMetaEdge(e):
		return sum(_get_e_size(root, edg) for edg in root[VIEW_META_GRAPH][e])
	else:
		return EDGE_SIZE


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
	sz = _get_e_size(graph.getRoot(), e)
	return tlp.Size(sz, sz)
