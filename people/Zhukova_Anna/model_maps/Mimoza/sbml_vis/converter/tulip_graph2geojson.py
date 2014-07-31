from collections import defaultdict
from tulip import tlp

import geojson

from sbml_vis.graph.cluster.factoring import factor_nodes, comp_to_meta_node, merge_ubs_for_similar_reactions
from sbml_vis.converter.tlp2geojson import e2feature, n2feature
from sbml_vis.graph.graph_properties import VIEW_META_GRAPH, MAX_ZOOM, MIN_ZOOM, ID, CLONE_ID, COMPARTMENT_ID, \
	TYPE_COMPARTMENT, TYPE, TYPE_REACTION, STOICHIOMETRY
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


def get_scales_by_metagraph(mg):
	bb = tlp.computeBoundingBox(mg)
	c_x, c_y = bb.center()[0], bb.center()[1]
	bb_w, bb_h = bb.width() / 2, bb.height() / 2
	min_x, min_y, max_x, max_y = c_x - bb_w, c_y - bb_h, c_x + bb_w, c_y + bb_h
	w, h = max_x - min_x, max_y - min_y
	if w > h:
		max_y += (w - h) / 2
	elif h > w:
		min_x -= (h - w) / 2
	scale_coefficient = DIMENSION / max(w, h)

	def scale(x, y):
		x, y = (x - min_x) * scale_coefficient, (max_y - y) * scale_coefficient
		return [float(x), float(y)]

	return scale, scale_coefficient


def get_scale_coefficients(meta_graph, n):
	root = meta_graph.getRoot()
	ns = {n} | {m for m in meta_graph.getInOutNodes(n)}
	rs = [r for r in ns if root[TYPE][r] == TYPE_REACTION]
	for r in rs:
		ns |= set(meta_graph.getInOutNodes(r))

	mg = meta_graph.inducedSubGraph(ns)
	# or has_neighbours_in_compartment(n, c_id, meta_graph)])
	scale, scale_coefficient = get_scales_by_metagraph(mg)

	meta_graph.delAllSubGraphs(mg)
	return scale, scale_coefficient


def update_level2features(feature, c_id2level2features, level_max, level_min, c_id):
	for z in xrange(level_min, level_max + 1):
		if not c_id in c_id2level2features:
			c_id2level2features[c_id] = defaultdict(list)
		c_id2level2features[c_id][z].append(feature)


def process_node(c_id, c_id2info, c_id2level2features, max_zooming_level, meta_graph, n,
                 processed, r2rs_ps, root, get_id, scale, scale_coefficient):
	n_id = get_id(n), c_id
	if n_id in processed:
		return
	level_min, level_max = root[MIN_ZOOM][n], root[MAX_ZOOM][n]
	f, bg = n2feature(meta_graph, n, scale, c_id2info, scale_coefficient, r2rs_ps)
	update_level2features(f, c_id2level2features, level_max, level_min, c_id)
	processed.add(n_id)
	if bg:
		level_min, level_max = root[MAX_ZOOM][n] + 1, max_zooming_level
		if root[TYPE][n] == TYPE_COMPARTMENT:
			if root[COMPARTMENT_ID][n] == c_id:
				update_level2features(bg, c_id2level2features, level_max, level_min, root[ID][n])
		else:
			update_level2features(bg, c_id2level2features, level_max, level_min, c_id)


def meta_graph2features(c_id2info, max_zooming_level, meta_graph, min_zooming_level, r2rs_ps):
	root = meta_graph.getRoot()

	c_id2scales = {}

	c_id2level2features = {}
	processed = set()
	get_id = lambda nd: "%s_%d" % (root[ID][nd], root[CLONE_ID][nd])
	scale, scale_coefficient = get_scales_by_metagraph(meta_graph)
	get_scales = lambda c_id: c_id2scales[c_id] if c_id in c_id2scales else (scale, scale_coefficient)
	for level in xrange(min_zooming_level, 1 + max_zooming_level):
		align_generalized_ns(meta_graph)
		rotate_generalized_ns(meta_graph)
		bend_edges(meta_graph)
		for n in (n for n in meta_graph.getNodes() if TYPE_COMPARTMENT == root[TYPE][n]):
			c_id2scales[root[ID][n]] = get_scale_coefficients(meta_graph, n)

		for n in meta_graph.getNodes():
			n_type = root[TYPE][n]
			c_id = root[COMPARTMENT_ID][n]
			scale, scale_coefficient = get_scales(c_id)
			process_node(c_id, c_id2info, c_id2level2features, max_zooming_level,
			             meta_graph, n, processed, r2rs_ps, root, get_id, scale, scale_coefficient)
			if TYPE_COMPARTMENT == n_type:
				n_id = root[ID][n]
				sc, sc_coefficient = get_scales(n_id)
				process_node(n_id, c_id2info, c_id2level2features, max_zooming_level,
				             meta_graph, n, processed, r2rs_ps, root, get_id, sc, sc_coefficient)

			for e in meta_graph.getInOutEdges(n):
				e_id = "%s-%s" % (get_id(meta_graph.source(e)), get_id(meta_graph.target(e))), c_id
				if not e_id in processed:
					s, t = meta_graph.source(e), meta_graph.target(e)
					s_c = root[COMPARTMENT_ID][s]
					t_c = root[COMPARTMENT_ID][t]
					level_min, level_max = max(root[MIN_ZOOM][t], root[MIN_ZOOM][s]), min(root[MAX_ZOOM][t],
					                                                                      root[MAX_ZOOM][s])
					f = e2feature(meta_graph, e, scale)
					if s_c == t_c:
						update_level2features(f, c_id2level2features, level_max, level_min, c_id)
					processed.add(e_id)
		if not level % 2:
			metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n) and TYPE_COMPARTMENT == root[TYPE][n]]
		else:
			metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n) and TYPE_COMPARTMENT != root[TYPE][n]]
		bend_ubiquitous_edges(meta_graph, metas)
		open_meta_ns(meta_graph, metas)
	return c_id2level2features


def graph2geojson(c_id2info, graph, verbose):
	root = graph.getRoot()

	max_comp_level = 2 * max({info[2][0] for info in c_id2info.itervalues()})
	min_zooming_level = 0
	max_zooming_level = max_comp_level + 2

	log(verbose, 'generalized species/reactions -> metanodes')
	merge_ubs_for_similar_reactions(root)

	r2rs_ps = {}
	for r in (r for r in root.getNodes() if TYPE_REACTION == root[TYPE][r]):
		rs = [(root[STOICHIOMETRY][e], root.source(e)) for e in root.getInEdges(r)]
		ps = [(root[STOICHIOMETRY][e], root.target(e)) for e in root.getOutEdges(r)]
		r2rs_ps[r] = rs, ps

	initialize_zoom(root, max_zooming_level, min_zooming_level)
	meta_graph = graph.inducedSubGraph([n for n in graph.getNodes()])
	# process_generalized_entities(meta_graph, max_comp_level, min_zooming_level)

	log(verbose, 'compartments -> metanodes')
	process_compartments(c_id2info, max_comp_level, meta_graph, min_zooming_level)

	log(verbose, 'tlp nodes -> geojson features')
	c_id2level2features = meta_graph2features(c_id2info, max_zooming_level,
	                                          meta_graph, min_zooming_level, r2rs_ps)

	geometry = geojson.Polygon([[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]])
	get_l2fs = lambda l2fs: {lev: geojson.FeatureCollection(features, geometry=geometry) for (lev, features) in
	                         l2fs.iteritems()}
	return {c_id: get_l2fs(l2fs) for (c_id, l2fs) in c_id2level2features.iteritems()}


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

	while current_zoom_level >= min_zoom_level:
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

	# meta_ns = factor_nodes(meta_graph)
	#
	# for n in meta_ns:
	# 	root[MIN_ZOOM][n] = root[MAX_ZOOM][n] = current_zoom_level
	# 	mg = root[VIEW_META_GRAPH][n]
	# 	for m in mg.getNodes():
	# 		root[MIN_ZOOM][m] = current_zoom_level + 1
	# layout(meta_graph)