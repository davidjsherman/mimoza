import geojson

from modules.factoring import factor_nodes, comp_to_meta_node
from modules.geojson_helper import DIMENSION, edge2feature, node2feature, get_min_max
from modules.graph_tools import VIEW_META_GRAPH, NAME, TYPE, TYPE_REACTION, ID
from modules.layout_utils import layout, layout_generalized_nodes, shorten_edges
from modules.resize import resize_edges, resize_nodes
from sbml_generalization.utils.logger import log
from sbml_generalization.utils.obo_ontology import parse, get_chebi


CELL_GO_ID = 'go:0005623'
CELL = 'cell'

__author__ = 'anna'


def print_info(level, meta_graph):
	print level, " : ", meta_graph.numberOfEdges(), " ", meta_graph.numberOfNodes()
	for n in sorted((n for n in meta_graph.getNodes() if meta_graph[TYPE][n] == TYPE_REACTION),
	                key=lambda n: meta_graph[ID][n]):
		print meta_graph[ID][n], " (", meta_graph[NAME][n], ') : ', sorted(
			meta_graph[NAME][m] for m in meta_graph.getInOutNodes(n))
	print '======================='
	print


def graph2geojson(c_id2info, graph, input_model, verbose):
	max_level = max({info[2][0] for info in c_id2info.itervalues()}) + 1
	root = graph.getRoot()
	min_zoom, max_zoom = root.getIntegerProperty("min_level"), root.getIntegerProperty("max_level")
	min_level = 0  # max_level - 1
	min_zoom.setAllNodeValue(min_level)
	max_zooming_level = max_level + 2
	max_zoom.setAllNodeValue(max_zooming_level)
	log(verbose, 'generalized species/reactions -> metanodes')
	meta_graph = process_generalized_entities(graph)
	for n in (n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)):
		max_zoom[n] = max_level - 1
		min_zoom[n] = min_level
		for m in root[VIEW_META_GRAPH][n].getNodes():
			min_zoom[m] = max_level
	layout(meta_graph)
	root_compartment = c_id2info[min(c_id2info.iterkeys(), key=lambda c_id: c_id2info[c_id][2][0])][0]
	level = max_level - 1
	while level > 0:
		meta_nodes = []
		for c_id in {comp.getId() for comp in input_model.getListOfCompartments() if
		             level == c_id2info[comp.getId()][2][0]}:
			(name, go, (level, out_c_id)) = c_id2info[c_id]
			meta_node = comp_to_meta_node(meta_graph, c_id, (go, name), out_c_id)
			min_zoom[meta_node] = max_zoom[meta_node] = level - 1
			for m in root[VIEW_META_GRAPH][meta_node].getNodes():
				min_zoom[m] = level
			meta_nodes.append(meta_node)
		# resize_nodes(meta_graph)
		resize_edges(meta_graph)
		layout(meta_graph)
		shorten_edges(meta_graph)
		level -= 1
	# print_info(level, meta_graph)
	features = []
	(m_x, m_y), (M_x, M_y) = get_min_max(meta_graph)
	x_scale = DIMENSION / (M_x - m_x)
	y_scale = DIMENSION / (M_y - m_y)

	def scale(x, y):
		return [(x - m_x) * x_scale, (M_y - y) * y_scale]

	onto = parse(get_chebi())
	i = 0
	e_min_zoom = lambda e: max(min_zoom[meta_graph.target(e)], min_zoom[meta_graph.source(e)])
	e_max_zoom = lambda e: min(max_zoom[meta_graph.target(e)], max_zoom[meta_graph.source(e)])

	while level <= max_level:
		# print_info(level, meta_graph)

		for e in (e for e in meta_graph.getEdges() if level == e_min_zoom(e)):
			features.append(edge2feature(meta_graph, e, i, scale, e_min_zoom(e), e_max_zoom(e), x_scale, y_scale))
			i += 1

		for n in (n for n in meta_graph.getNodes() if level == min_zoom[n]):
			f, bg = node2feature(meta_graph, n, i, scale, min_zoom[n], max_zoom[n], max_zooming_level, onto, c_id2info)
			i += (2 if bg else 1)
			features.append(f)
			if bg:
				features.append(bg)

		level += 1

		if level == max_level:
			layout_generalized_nodes(meta_graph)

		metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)]
		for n in metas:
			meta_graph.openMetaNode(n)

		if level == max_level:
			resize_nodes(meta_graph)
	return geojson.FeatureCollection(features, geometry=geojson.Polygon(
		[[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]])), root_compartment, max_zooming_level


def process_generalized_entities(graph):
	ns = list(graph.getNodes())
	meta_graph = graph.inducedSubGraph(ns)
	meta_graph.setName("meta graph")
	original_graph = graph.inducedSubGraph(ns)
	original_graph.setName("full graph")
	factor_nodes(meta_graph)
	return meta_graph
