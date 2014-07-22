from tulip import tlp

import geojson
from graph.cluster.factoring import factor_nodes, comp_to_meta_node

from sbml_vis.converter.tlp2geojson import e2feature, n2feature
from sbml_vis.graph.graph_properties import VIEW_META_GRAPH, MAX_ZOOM, MIN_ZOOM, FAKE, \
	ID, CLONE_ID
from sbml_vis.graph.layout.generalized_layout import rotate_generalized_ns, align_generalized_ns, rotate_fake_ns
from sbml_vis.graph.layout.ubiquitous_layout import bend_ubiquitous_edges, layout_outer_elements, layout_inner_elements
from sbml_vis.graph.layout.layout_utils import layout_cytoplasm, open_meta_ns, shorten_edges, create_fake_rs, layout
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


def meta_graph2features(c_id2info, max_comp_level, max_zooming_level, meta_graph, min_zooming_level):
	root = meta_graph.getRoot()

	scale, scale_coefficient = get_scale_coefficients(meta_graph)

	onto = parse(get_chebi())

	features = []
	processed = set()
	level = min_zooming_level
	get_id = lambda nd: "%s_%d" % (root[ID][nd], root[CLONE_ID][nd])
	while level <= max_comp_level:
		# if level < max_comp_level:
			# node wasn't yet serialised => we can change its position
			# filter_nd = lambda nd: root[MIN_ZOOM][nd] >= level
			# layout_outer_reactions(meta_graph, filter_nd)

		for e in meta_graph.getEdges():
			e_id = "%s-%s" % (get_id(meta_graph.source(e)), get_id(meta_graph.target(e)))
			if not e_id in processed:
				features.append(e2feature(meta_graph, e, scale, e_id))
				processed.add(e_id)

		for n in meta_graph.getNodes():
			n_id = get_id(n)
			if not n_id in processed:
				f, bg = n2feature(meta_graph, n, scale, max_zooming_level, onto, c_id2info, scale_coefficient, n_id)
				features.append(f)
				processed.add(n_id)
				if bg:
					features.append(bg)

		metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n) and level == root[MAX_ZOOM][n]]

		level += 1

		if level == max_comp_level:
			align_generalized_ns(meta_graph)
			rotate_generalized_ns(meta_graph)
			bend_ubiquitous_edges(meta_graph, metas)

		open_meta_ns(meta_graph, metas)
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
	process_compartments(c_id2info, max_comp_level - 1, meta_graph, min_zooming_level )

	log(verbose, 'tlp nodes -> geojson features')
	features = meta_graph2features(c_id2info, max_comp_level, max_zooming_level,
	                               meta_graph, min_zooming_level)

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
	return meta_graph


def process_compartments(c_id2info, current_zoom_level, meta_graph, min_zoom_level):
	root = meta_graph.getRoot()

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
		# create_fake_rs(meta_graph)
		# layout_outer_elements(meta_graph)
		# shorten_edges(meta_graph)
		# remove_overlaps(meta_graph)
		# layout_inner_elements(meta_graph)
		# rotate_fake_ns(meta_graph)
		# open_meta_ns(meta_graph, (r for r in meta_graph.getNodes() if root[FAKE][r]))
		current_zoom_level -= 1
	layout(meta_graph)