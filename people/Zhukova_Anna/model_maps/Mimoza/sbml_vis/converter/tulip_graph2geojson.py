import geojson

from sbml_vis.tulip.cluster.factoring import factor_nodes, comp_to_meta_node, r_to_meta_node
from sbml_vis.converter.tlp2geojson import e2feature, n2feature
from sbml_vis.tulip.graph_properties import VIEW_META_GRAPH, MAX_ZOOM, MIN_ZOOM, VIEW_LAYOUT, VIEW_SIZE, TYPE_REACTION, \
	TYPE
from sbml_vis.tulip.resize import get_min_max, get_n_size
from sbml_vis.tulip.layout.generalized_layout import rotate_generalized_ns, align_generalized_ns
from sbml_vis.tulip.layout.ubiquitous_layout import bend_ubiquitous_edges, layout_ub_sps, layout_outer_reactions, \
	ub_or_single
from sbml_vis.tulip.layout.layout_utils import layout, layout_cytoplasm

from sbml_generalization.utils.logger import log
from sbml_generalization.utils.obo_ontology import parse, get_chebi

FAKE = "fake"

DIMENSION = 512

CELL_GO_ID = 'go:0005623'
CELL = 'cell'

__author__ = 'anna'


def initialize_zoom(graph, max_zooming_level, min_zooming_level=0):
	max_zoom = graph.getIntegerProperty(MAX_ZOOM)
	min_zoom = graph.getIntegerProperty(MIN_ZOOM)

	min_zoom.setAllNodeValue(min_zooming_level)
	max_zoom.setAllNodeValue(max_zooming_level)


def meta_graph2features(c_id2info, max_comp_level, max_zooming_level, meta_graph, min_zooming_level, c_id2n):
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
		# if level < max_comp_level:
			# node wasn't yet serialised => we can change its position
			# filter_nd = lambda nd: root[MIN_ZOOM][nd] >= level
			# layout_ub_sps(meta_graph, c_id2n, c_id2outs, filter_nd)
			# layout_outer_reactions(meta_graph, filter_nd)
			# layout_ub_sps(meta_graph, c_id2n, c_id2outs, filter_nd)
		for r in (r for r in meta_graph.getNodes() if root[FAKE][r]):
			ns = root[VIEW_META_GRAPH][r].getNodes()
			meta_graph.openMetaNode(r)
			for n in ns:
				root[VIEW_SIZE][n] = get_n_size(meta_graph, n)

		for e in (e for e in meta_graph.getEdges() if
		          not (meta_graph.target(e) in processed and meta_graph.source(e) in processed)):
			features.append(e2feature(meta_graph, e, scale))

		for n in (n for n in meta_graph.getNodes() if not n in processed):
			f, bg = n2feature(meta_graph, n, scale, max_zooming_level, onto, c_id2info, scale_coefficient)
			features.append(f)
			processed.add(n)
			if bg:
				features.append(bg)

		# metas = [n for n in node2graph.iterkeys() if level == root[MAX_ZOOM][n]]
		metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n) and level == root[MAX_ZOOM][n]]

		level += 1

		if level == max_comp_level:
			align_generalized_ns(meta_graph)
			rotate_generalized_ns(meta_graph)
			bend_ubiquitous_edges(meta_graph, metas)

		for n in metas:
			ns = root[VIEW_META_GRAPH][n].getNodes()
			meta_graph.openMetaNode(n)
			for n in ns:
				root[VIEW_SIZE][n] = get_n_size(meta_graph, n)

		if level != max_comp_level:
			for e in meta_graph.getEdges():
				root[VIEW_LAYOUT][e] = []

	return features


def graph2geojson(c_id2info, graph, verbose):
	root = graph.getRoot()

	max_comp_level = max({info[2][0] for info in c_id2info.itervalues()}) + 1
	min_zooming_level = 0  # max_comp_level - 1
	max_zooming_level = max_comp_level + 3

	initialize_zoom(root, max_zooming_level, min_zooming_level)

	log(verbose, 'generalized species/reactions -> metanodes')
	meta_graph = process_generalized_entities(graph, max_comp_level, min_zooming_level)

	log(verbose, 'compartments -> metanodes')
	c_id2n = process_compartments(c_id2info, max_comp_level - 1, meta_graph, min_zooming_level )

	log(verbose, 'tlp nodes -> geojson features')
	features = meta_graph2features(c_id2info, max_comp_level, max_zooming_level,
	                               meta_graph, min_zooming_level, c_id2n)

	return geojson.FeatureCollection(features, geometry=geojson.Polygon(
		[[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]])), max_zooming_level


def process_generalized_entities(graph, max_level, min_level):
	root = graph.getRoot()

	meta_graph = graph.inducedSubGraph([n for n in graph.getNodes()])
	factor_nodes(meta_graph)

	for n in (n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)):
		root[MAX_ZOOM][n] = max_level - 1
		root[MIN_ZOOM][n] = min_level
		mg = root[VIEW_META_GRAPH][n]
		for m in mg.getNodes():
			root[MIN_ZOOM][m] = max_level

	# layout(meta_graph)
	# align_generalized_ns(meta_graph)

	fake = root.getBooleanProperty(FAKE)
	for r in (r for r in meta_graph.getNodes() if TYPE_REACTION == root[TYPE][r]):
		r_n = r_to_meta_node(meta_graph, r)
		if r_n:
			mg = root[VIEW_META_GRAPH][r_n]
			root[MAX_ZOOM][r_n] = max(root[MAX_ZOOM][n] for n in mg.getNodes())
			root[MIN_ZOOM][r_n] = min(root[MIN_ZOOM][n] for n in mg.getNodes())
			fake[r_n] = True

	layout(meta_graph)

	return meta_graph


def process_compartments(c_id2info, current_zoom_level, meta_graph, min_zoom_level):
	root = meta_graph.getRoot()

	c_id2n = {}
	while current_zoom_level > min_zoom_level:
		for c_id in c_id2info.iterkeys():
			(name, go, (l, out_c_id)) = c_id2info[c_id]
			if current_zoom_level != l:
				continue

			comp_n = comp_to_meta_node(meta_graph, c_id, (go, name), out_c_id)
			if not comp_n:
				continue
			root[MIN_ZOOM][comp_n] = root[MAX_ZOOM][comp_n] = current_zoom_level - 1
			comp_graph = root[VIEW_META_GRAPH][comp_n]
			for m in comp_graph.getNodes():
				root[MIN_ZOOM][m] = current_zoom_level
				if root[FAKE][m]:
					for n in root[VIEW_META_GRAPH][m].getNodes():
						root[MIN_ZOOM][n] = current_zoom_level
			c_id2n[c_id] = comp_n
		layout_cytoplasm(meta_graph)
		# layout_outer_reactions(meta_graph, n2graph)
		# shorten_edges(meta_graph)
		# remove_overlaps(meta_graph)
		current_zoom_level -= 1
	return c_id2n