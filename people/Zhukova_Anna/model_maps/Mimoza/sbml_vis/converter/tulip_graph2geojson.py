import geojson

from tulip import tlp

from sbml_vis.tulip.cluster.factoring import factor_nodes, comp_to_meta_node
from sbml_vis.converter.tlp2geojson import e2feature, n2feature
from sbml_vis.tulip.graph_properties import VIEW_META_GRAPH, MAX_ZOOM, MIN_ZOOM, VIEW_LAYOUT, NAME, TYPE_REACTION, TYPE, \
	ID, VIEW_SIZE
from sbml_vis.tulip.resize import get_min_max
from sbml_vis.tulip.layout.generalized_layout import rotate_generalized_ns, align_generalized_ns
from sbml_vis.tulip.layout.ubiquitous_layout import bend_ubiquitous_edges, layout_ub_sps, layout_outer_reactions, \
	remove_overlaps
from sbml_vis.tulip.layout.layout_utils import layout, layout_cytoplasm, shorten_edges

from sbml_generalization.utils.logger import log
from sbml_generalization.utils.obo_ontology import parse, get_chebi


DIMENSION = 512

CELL_GO_ID = 'go:0005623'
CELL = 'cell'

__author__ = 'anna'


def initialize_zoom(graph, max_zooming_level, min_zooming_level=0):
	max_zoom = graph.getIntegerProperty(MAX_ZOOM)
	min_zoom = graph.getIntegerProperty(MIN_ZOOM)

	min_zoom.setAllNodeValue(min_zooming_level)
	max_zoom.setAllNodeValue(max_zooming_level)


def meta_graph2features(c_id2info, c_id2outs, max_comp_level, max_zooming_level, meta_graph, min_zooming_level,
                        node2graph, c_id2n):
	root = meta_graph.getRoot()

	(m_x, m_y), (M_x, M_y) = get_min_max(meta_graph, 5)
	scale_coefficient = DIMENSION / (M_x - m_x)

	def scale(x, y):
		x, y = (x - m_x) * scale_coefficient, (M_y - y) * scale_coefficient
		return [x, y]

	onto = parse(get_chebi())

	features = []
	processed = set()
	level = min_zooming_level
	while level <= max_comp_level:
		if level < max_comp_level:
			# node wasn't yet serialised => we can change its position
			filter_nd=lambda nd: root[MIN_ZOOM][nd] >= level
			layout_ub_sps(meta_graph, c_id2n, c_id2outs, filter_nd)
			layout_outer_reactions(meta_graph, node2graph, filter_nd)
			layout_ub_sps(meta_graph, c_id2n, c_id2outs, filter_nd)
		for e in (e for e in meta_graph.getEdges() if not (meta_graph.target(e) in processed and meta_graph.source(e) in processed)):
			features.append(e2feature(meta_graph, e, scale, c_id2outs, node2graph))

		for n in (n for n in meta_graph.getNodes() if not n in processed):
			f, bg = n2feature(meta_graph, n, scale, max_zooming_level, onto,
			                  c_id2info, c_id2outs, scale_coefficient, node2graph)
			features.append(f)
			if bg:
				features.append(bg)

		metas = [n for n in node2graph.iterkeys() if level == root[MAX_ZOOM][n]]

		level += 1

		if level == max_comp_level:
			rotate_generalized_ns(meta_graph, node2graph)
			bend_ubiquitous_edges(meta_graph, metas, node2graph)

		for n in metas:
			mg = node2graph[n]
			n_x, n_y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
			mg_bb = tlp.computeBoundingBox(mg)
			mg_x, mg_y = mg_bb.center().getX(), mg_bb.center().getY()
			d_x, d_y = -mg_x + n_x, -mg_y + n_y
			root[VIEW_LAYOUT].translate(tlp.Coord(d_x, d_y), mg)

		ns = [n for n in root.getNodes() if root[MIN_ZOOM][n] <= level <= root[MAX_ZOOM][n]]
		root.delSubGraph(meta_graph)
		meta_graph = root.inducedSubGraph(list(ns))

	return features


def graph2geojson(c_id2info, c_id2outs, graph, verbose):
	root = graph.getRoot()

	max_comp_level = max({info[2][0] for info in c_id2info.itervalues()}) + 1
	min_zooming_level = 0 # max_comp_level - 1
	max_zooming_level = max_comp_level + 3

	initialize_zoom(root, max_zooming_level, min_zooming_level)

	node2graph = {}

	log(verbose, 'generalized species/reactions -> metanodes')
	meta_graph = process_generalized_entities(graph, max_comp_level, min_zooming_level, node2graph)

	log(verbose, 'compartments -> metanodes')
	c_id2n = process_compartments(c_id2info, c_id2outs, max_comp_level - 1, meta_graph, min_zooming_level, node2graph)

	log(verbose, 'tlp nodes -> geojson features')
	features = meta_graph2features(c_id2info, c_id2outs, max_comp_level, max_zooming_level,
	                               meta_graph, min_zooming_level, node2graph, c_id2n)

	return geojson.FeatureCollection(features, geometry=geojson.Polygon(
		[[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]])), max_zooming_level


def process_generalized_entities(graph, max_level, min_level, node2graph):
	root = graph.getRoot()

	meta_graph = graph.inducedSubGraph([n for n in graph.getNodes()])
	factor_nodes(meta_graph)

	for n in (n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)):
		root[MAX_ZOOM][n] = max_level - 1
		root[MIN_ZOOM][n] = min_level
		mg = root[VIEW_META_GRAPH][n]
		for m in mg.getNodes():
			root[MIN_ZOOM][m] = max_level
		node2graph[n] = mg

	unmetanode(meta_graph)

	layout(meta_graph)
	align_generalized_ns(meta_graph, node2graph)

	return meta_graph


def unmetanode(meta_graph, meta_ns=None):
	root = meta_graph.getRoot()
	edge_def_val, node_def_val = root.getGraphProperty(VIEW_META_GRAPH).getEdgeDefaultValue(), root[VIEW_META_GRAPH].getNodeDefaultValue()
	if not meta_ns:
		meta_ns = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)]
	root[VIEW_LAYOUT].setAllEdgeValue([])
	root[VIEW_META_GRAPH].setAllEdgeValue(edge_def_val)
	for n in meta_ns:
		root[VIEW_META_GRAPH][n] = node_def_val
		for e in (e for e in root.getInOutEdges(n) if not meta_graph.isElement(e)):
			root.delEdge(e, True)


def process_compartments(c_id2info, c_id2outs, current_zoom_level, meta_graph, min_zoom_level, n2graph):
	root = meta_graph.getRoot()

	c_id2n = {}
	while current_zoom_level > min_zoom_level:
		for c_id in c_id2info.iterkeys():
			(name, go, (l, out_c_id)) = c_id2info[c_id]
			if current_zoom_level != l:
				continue

			comp_n = comp_to_meta_node(meta_graph, c_id, (go, name), out_c_id)
			root[MIN_ZOOM][comp_n] = root[MAX_ZOOM][comp_n] = current_zoom_level - 1
			comp_graph = root[VIEW_META_GRAPH][comp_n]
			for m in comp_graph.getNodes():
				root[MIN_ZOOM][m] = current_zoom_level
			n2graph[comp_n] = comp_graph
			c_id2n[c_id] = comp_n
			unmetanode(meta_graph, [comp_n])
		layout_cytoplasm(meta_graph, n2graph, c_id2n, c_id2outs)
		# layout_outer_reactions(meta_graph, n2graph)
		# shorten_edges(meta_graph)
		# remove_overlaps(meta_graph)
		current_zoom_level -= 1
	return c_id2n