from collections import defaultdict
from tulip import tlp

import geojson

from sbml_vis.graph.cluster.factoring import factor_nodes, comp_to_meta_node, merge_ubs_for_similar_reactions
from sbml_vis.converter.tlp2geojson import e2feature, n2feature
from sbml_vis.graph.graph_properties import VIEW_META_GRAPH, MAX_ZOOM, MIN_ZOOM, FAKE, \
	ID, CLONE_ID, COMPARTMENT_ID, NAME, TYPE_COMPARTMENT, TYPE
from sbml_vis.graph.layout.generalized_layout import rotate_generalized_ns, align_generalized_ns
from sbml_vis.graph.layout.ubiquitous_layout import bend_ubiquitous_edges, bend_edges
from sbml_vis.graph.layout.layout_utils import open_meta_ns, layout
from sbml_generalization.utils.logger import log


DIMENSION = 512

CELL_GO_ID = 'go:0005623'
CELL = 'cell'

__author__ = 'anna'


def initialize_zoom(graph, max_zooming_level, min_zooming_level=0):
	max_zoom = graph.getIntegerProperty(MAX_ZOOM)
	min_zoom = graph.getIntegerProperty(MIN_ZOOM)

	min_zoom.setAllNodeValue(min_zooming_level)
	max_zoom.setAllNodeValue(max_zooming_level)


def get_scale_coefficients(meta_graph):
	bb = tlp.computeBoundingBox(meta_graph)
	c_x, c_y = bb.center()[0], bb.center()[1]
	bb_w, bb_h = bb.width() / 2, bb.height() / 2
	min_x, min_y, max_x, max_y = c_x - bb_w, c_y - bb_h, c_x + bb_w, c_y + bb_h
	w, h = max_x - min_x, max_y - min_y
	if w > h:
		max_y += (w - h) / 2
	elif h > w:
		min_x -= (h - w) / 2

	def scale(x, y):
		x, y = (x - min_x) * scale_coefficient, (max_y - y) * scale_coefficient
		return [float(x), float(y)]

	scale_coefficient = DIMENSION / max(w, h)
	return scale, scale_coefficient


def update_level2features(feature, c_id2level2features, level_max, level_min, c_id, level_0):
	for z in xrange(level_min - level_0, min(1, level_max - level_0) + 1):
		if not c_id in c_id2level2features:
			c_id2level2features[c_id] = defaultdict(list)
		c_id2level2features[c_id][z].append(feature)


def meta_graph2features(c_id2info, max_zooming_level, meta_graph, min_zooming_level):
	root = meta_graph.getRoot()

	scale, scale_coefficient = get_scale_coefficients(meta_graph)

	c_id2level2features = {}
	processed = set()
	get_id = lambda nd: "%s_%d" % (root[ID][nd], root[CLONE_ID][nd])
	cur_min_zoom = min_zooming_level
	for level in xrange(min_zooming_level, 1 + max_zooming_level):
		align_generalized_ns(meta_graph)
		rotate_generalized_ns(meta_graph)
		bend_edges(meta_graph)

		for e in meta_graph.getEdges():
			e_id = "%s-%s" % (get_id(meta_graph.source(e)), get_id(meta_graph.target(e)))
			if not e_id in processed:
				s, t = meta_graph.source(e), meta_graph.target(e)
				c_id = root[COMPARTMENT_ID][s]
				if c_id != root[COMPARTMENT_ID][t]:
					continue
				level_min, level_max = max(root[MIN_ZOOM][t], root[MIN_ZOOM][s]), min(root[MAX_ZOOM][t],
				                                                                      root[MAX_ZOOM][s])
				f = e2feature(meta_graph, e, scale, e_id)
				update_level2features(f, c_id2level2features, level_max, level_min, c_id, cur_min_zoom)
				processed.add(e_id)

		for n in meta_graph.getNodes():
			n_id = get_id(n)
			if not n_id in processed:
				f, bg = n2feature(meta_graph, n, scale, c_id2info, scale_coefficient, n_id)
				level_min, level_max = root[MIN_ZOOM][n], root[MAX_ZOOM][n]
				update_level2features(f, c_id2level2features, level_max, level_min, root[COMPARTMENT_ID][n],
				                      cur_min_zoom)
				processed.add(n_id)
				if bg:
					level_min, level_max = root[MAX_ZOOM][n] + 1, max_zooming_level
					update_level2features(bg, c_id2level2features, level_max, level_min, root[COMPARTMENT_ID][n],
					                      cur_min_zoom)
		if level % 2:
			metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n) and TYPE_COMPARTMENT == root[TYPE][n]]
			cur_min_zoom += 2
		else:
			metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n) and TYPE_COMPARTMENT != root[TYPE][n]]
		bend_ubiquitous_edges(meta_graph, metas)

		open_meta_ns(meta_graph, metas)
	return c_id2level2features


def graph2geojson(c_id2info, graph, verbose):
	root = graph.getRoot()

	max_comp_level = 2 * max({info[2][0] for info in c_id2info.itervalues()})
	min_zooming_level = 0  # max_comp_level - 1
	max_zooming_level = max_comp_level + 1

	log(verbose, 'generalized species/reactions -> metanodes')
	merge_ubs_for_similar_reactions(root)

	initialize_zoom(root, max_zooming_level, min_zooming_level)
	meta_graph = graph.inducedSubGraph([n for n in graph.getNodes()])
	# process_generalized_entities(meta_graph, max_comp_level, min_zooming_level)

	log(verbose, 'compartments -> metanodes')
	process_compartments(c_id2info, max_comp_level, meta_graph, min_zooming_level)

	log(verbose, 'tlp nodes -> geojson features')
	c_id2level2features = meta_graph2features(c_id2info, max_zooming_level,
	                                          meta_graph, min_zooming_level)

	geometry = geojson.Polygon([[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]])
	get_l2fs = lambda l2fs: {lev: geojson.FeatureCollection(features, geometry=geometry) for (lev, features) in l2fs.iteritems()}
	return {c_id: get_l2fs(l2fs) for (c_id, l2fs) in c_id2level2features.iteritems()}, max_zooming_level


def process_generalized_entities(meta_graph, max_level, min_level):
	root = meta_graph.getRoot()

	factor_nodes(meta_graph)

	for n in (n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)):
		root[MAX_ZOOM][n] = max_level - 1
		root[MIN_ZOOM][n] = min_level
		mg = root[VIEW_META_GRAPH][n]
		for m in mg.getNodes():
			root[MIN_ZOOM][m] = max_level
	return meta_graph


def process_compartments(c_id2info, current_zoom_level, meta_graph, min_zoom_level):
	root = meta_graph.getRoot()

	while current_zoom_level > min_zoom_level:
		for c_id in c_id2info.iterkeys():
			(name, go, (l, out_c_id)) = c_id2info[c_id]
			if current_zoom_level / 2 != l:
				continue
			ns = (n for n in meta_graph.getNodes() if root[COMPARTMENT_ID][n] == c_id)
			meta_ns = factor_nodes(meta_graph, ns)

			for n in meta_ns:
				root[MIN_ZOOM][n] = root[MAX_ZOOM][n] = current_zoom_level
				mg = root[VIEW_META_GRAPH][n]
				for m in mg.getNodes():
					root[MIN_ZOOM][m] = current_zoom_level + 1

			comp_n = comp_to_meta_node(meta_graph, c_id, (go, name), out_c_id)
			if not comp_n:
				continue
			root[MIN_ZOOM][comp_n] = current_zoom_level - 2
			root[MAX_ZOOM][comp_n] = current_zoom_level - 1
			comp_graph = root[VIEW_META_GRAPH][comp_n]
			for m in comp_graph.getNodes():
				root[MIN_ZOOM][m] = current_zoom_level
		current_zoom_level -= 2
		layout(meta_graph)

	meta_ns = factor_nodes(meta_graph)

	for n in meta_ns:
		root[MIN_ZOOM][n] = root[MAX_ZOOM][n] = current_zoom_level
		mg = root[VIEW_META_GRAPH][n]
		for m in mg.getNodes():
			root[MIN_ZOOM][m] = current_zoom_level + 1
	layout(meta_graph)