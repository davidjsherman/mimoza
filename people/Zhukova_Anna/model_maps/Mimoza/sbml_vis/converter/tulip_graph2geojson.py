import geojson

from tulip import tlp

from sbml_vis.tulip.cluster.factoring import factor_nodes, comp_to_meta_node
from sbml_vis.converter.tlp2geojson import e2feature, n2feature
from sbml_vis.tulip.graph_properties import VIEW_META_GRAPH, MAX_ZOOM, MIN_ZOOM, VIEW_LAYOUT
from sbml_vis.tulip.layout.layout_utils import layout, layout_cytoplasm
from sbml_vis.tulip.resize import get_min_max
from sbml_vis.tulip.layout.generalized_layout import rotate_generalized_ns, align_generalized_ns
from sbml_vis.tulip.layout.ubiquitous_layout import bend_ubiquitous_edges

from sbml_generalization.utils.logger import log
from sbml_generalization.utils.obo_ontology import parse, get_chebi


DIMENSION = 512

CELL_GO_ID = 'go:0005623'
CELL = 'cell'

__author__ = 'anna'


def compute_c_id2out_c_ids(c_id2info):
	c_id2outs = {}
	for c_id in c_id2info.iterkeys():
		_, _, (_, out_c_id) = c_id2info[c_id]
		outs = []
		while out_c_id:
			outs.append(out_c_id)
			_, _, (_, out_c_id) = c_id2info[out_c_id]
		c_id2outs[c_id] = outs
	return c_id2outs


def initialize_zoom(graph, max_zooming_level, min_zooming_level=0):
	max_zoom = graph.getIntegerProperty(MAX_ZOOM)
	min_zoom = graph.getIntegerProperty(MIN_ZOOM)

	min_zoom.setAllNodeValue(min_zooming_level)
	max_zoom.setAllNodeValue(max_zooming_level)


def meta_graph2features(c_id2info, c_id2outs, max_comp_level, max_zooming_level, meta_graph, min_zooming_level,
                        node2graph):
	root = meta_graph.getRoot()

	(m_x, m_y), (M_x, M_y) = get_min_max(meta_graph, 5)
	scale_coefficient = DIMENSION / (M_x - m_x)

	def scale(x, y):
		x, y = (x - m_x) * scale_coefficient, (M_y - y) * scale_coefficient
		return [x, y]

	onto = parse(get_chebi())

	e_min_zoom = lambda e, gr: max(root[MIN_ZOOM][gr.target(e)], root[MIN_ZOOM][gr.source(e)])
	e_max_zoom = lambda e, gr: min(root[MAX_ZOOM][gr.target(e)], root[MAX_ZOOM][gr.source(e)])

	features = []
	i = 0
	level = min_zooming_level
	while level <= max_comp_level:
		for e in (e for e in meta_graph.getEdges() if level == e_min_zoom(e, meta_graph)):
			features.append(
				e2feature(meta_graph, e, i, scale, e_min_zoom(e, meta_graph), e_max_zoom(e, meta_graph), c_id2outs,
				          scale_coefficient, node2graph))
			i += 1

		for n in (n for n in meta_graph.getNodes() if level == root[MIN_ZOOM][n]):
			f, bg = n2feature(meta_graph, n, i, scale, root[MIN_ZOOM][n], root[MAX_ZOOM][n], max_zooming_level, onto,
			                  c_id2info, c_id2outs, scale_coefficient, node2graph)
			i += (2 if bg else 1)
			features.append(f)
			if bg:
				features.append(bg)

		metas = [n for n in node2graph.iterkeys() if level == root[MAX_ZOOM][n]]

		level += 1

		if level == max_comp_level:
			rotate_generalized_ns(meta_graph, node2graph)
			bend_ubiquitous_edges(meta_graph, metas, node2graph)

		ns = set()
		for n in metas:
			mg = node2graph[n]
			ms = set(mg.getNodes())
			ns |= ms
			for m in ms:
				for p in root.getInOutNodes(m):
					if meta_graph.isElement(p) and level <= root[MAX_ZOOM][p]:
						ns.add(p)
			n_center = root[VIEW_LAYOUT][n]
			mg_center = tlp.computeBoundingBox(mg).center()
			d_x, d_y = -mg_center.getX() + n_center.getX(), -mg_center.getY() + n_center.getY()
			root[VIEW_LAYOUT].translate(tlp.Coord(d_x, d_y), mg)

		meta_graph = root.inducedSubGraph(list(ns))
	return features


def graph2geojson(c_id2info, graph, input_model, verbose):
	root = graph.getRoot()
	c_id2outs = compute_c_id2out_c_ids(c_id2info)

	max_comp_level = max({info[2][0] for info in c_id2info.itervalues()}) + 1
	min_zooming_level = 0  # max_level - 1
	max_zooming_level = max_comp_level + 3

	initialize_zoom(root, max_zooming_level, min_zooming_level)

	node2graph = {}

	log(verbose, 'generalized species/reactions -> metanodes')
	meta_graph = process_generalized_entities(graph, max_comp_level, min_zooming_level, node2graph)

	log(verbose, 'compartments -> metanodes')
	process_compartments(c_id2info, graph, input_model, max_comp_level - 1, meta_graph, min_zooming_level, node2graph)

	log(verbose, 'tlp nodes -> geojson features')
	features = meta_graph2features(c_id2info, c_id2outs, max_comp_level, max_zooming_level,
	                               meta_graph, min_zooming_level, node2graph)

	return geojson.FeatureCollection(features, geometry=geojson.Polygon(
		[[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]])), max_zooming_level


def process_generalized_entities(graph, max_level, min_level, node2graph):
	root = graph.getRoot()
	edge_def_val, node_def_val = root.getGraphProperty(VIEW_META_GRAPH).getEdgeDefaultValue(), root[VIEW_META_GRAPH].getNodeDefaultValue()

	ns = list(graph.getNodes())
	meta_graph = graph.inducedSubGraph(ns)
	meta_graph.setName("meta graph")
	factor_nodes(meta_graph)

	meta_ns = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)]
	for e in (e for e in meta_graph.getEdges() if meta_graph.isMetaEdge(e)):
		for edg in root[VIEW_META_GRAPH][e]:
			root[VIEW_LAYOUT][edg] = []
		root[VIEW_META_GRAPH][e] = edge_def_val
	for n in meta_ns:
		root[MAX_ZOOM][n] = max_level - 1
		root[MIN_ZOOM][n] = min_level
		mg = root[VIEW_META_GRAPH][n]
		for m in mg.getNodes():
			root[MIN_ZOOM][m] = max_level
		root[VIEW_META_GRAPH][n] = node_def_val
		node2graph[n] = mg

	layout(meta_graph)

	align_generalized_ns(meta_graph, node2graph)

	return meta_graph


def process_compartments(c_id2info, graph, input_model, level, meta_graph, min_zooming_level, node2graph):
	root = graph.getRoot()
	edge_def_val, node_def_val = root[VIEW_META_GRAPH].getEdgeDefaultValue(), root[VIEW_META_GRAPH].getNodeDefaultValue()

	while level > min_zooming_level:
		# mic(meta_graph)
		grs = []
		for c_id in {comp.getId() for comp in input_model.getListOfCompartments() if
		             level == c_id2info[comp.getId()][2][0]}:
			(name, go, (level, out_c_id)) = c_id2info[c_id]
			meta_node = comp_to_meta_node(meta_graph, c_id, (go, name), out_c_id)
			root[MIN_ZOOM][meta_node] = root[MAX_ZOOM][meta_node] = level - 1
			mg = root[VIEW_META_GRAPH][meta_node]
			for m in mg.getNodes():
				root[MIN_ZOOM][m] = level
			node2graph[meta_node] = mg
			for e in meta_graph.getInOutEdges(meta_node):
				for edg in root[VIEW_META_GRAPH][e]:
					root[VIEW_LAYOUT][edg] = []
				root[VIEW_META_GRAPH][e] = edge_def_val
			root[VIEW_META_GRAPH][meta_node] = node_def_val
			grs.append(mg)
		layout_cytoplasm(meta_graph, node2graph)
		# shorten_edges(meta_graph)
		# remove_overlaps(meta_graph)
		# layout_ub_sps(meta_graph)
		# for mg in grs:
		# 	layout_single_species(mg, node2graph)
		level -= 1