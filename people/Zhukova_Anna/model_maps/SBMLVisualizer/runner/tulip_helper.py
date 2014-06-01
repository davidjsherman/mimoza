import os
from shutil import copyfile
import threading

import geojson

from mimoza.mimoza import MIMOZA_URL, JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON
from modules.combine_archive_creator import archive
from modules.factoring import factor_nodes, comp_to_meta_node
from modules.geojson_helper import DIMENSION, edge2feature, node2feature, get_min_max
from modules.graph_tools import VIEW_META_GRAPH, NAME, TYPE, TYPE_REACTION
from modules.html_generator import create_html, create_embedded_html
from modules.layout_utils import layout, layout_cytoplasm, layout_generalized_nodes, shorten_edges, remove_overlaps
from modules.resize import resize_edges, resize_nodes
from sbml_generalization.utils.logger import log
from sbml_generalization.utils.obo_ontology import parse, get_chebi


CELL_GO_ID = 'go:0005623'
CELL = 'cell'

__author__ = 'anna'


# def visualize_model(directory, m_dir_id, input_model, graph, name2id_go, groups_sbml, url, main_url, scripts, css, fav, verbose):
def visualize_model(directory, m_dir_id, input_model, graph, c_id2info, groups_sbml, url, main_url, scripts, css, fav,
                    verbose):
	max_level = max({info[2][0] for info in c_id2info.itervalues()}) + 1

	root = graph.getRoot()
	min_zoom, max_zoom = root.getIntegerProperty("min_level"), root.getIntegerProperty("max_level")
	min_zoom.setAllNodeValue(0)
	max_zoom.setAllNodeValue(max_level + 1)

	log(verbose, 'generalized species/reactions -> metanodes')
	meta_graph = process_generalized_entities(graph)
	for n in (n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)):
		max_zoom[n] = max_level - 1
		min_zoom[n] = 0
		for m in root[VIEW_META_GRAPH][n].getNodes():
			min_zoom[m] = max_level

	layout(meta_graph)
	root_compartment = c_id2info[min(c_id2info.iterkeys(), key=lambda c_id: c_id2info[c_id][2][0])][0]
	# comp_names = [root_compartment]
	level = max_level - 1
	level2meta_nodes = {}
	while level > 0:
		meta_nodes = []
		for c_id in {comp.getId() for comp in input_model.getListOfCompartments() if
		             level == c_id2info[comp.getId()][2][0]}:
			(name, go, (level, out_c_id)) = c_id2info[c_id]
			meta_node = comp_to_meta_node(meta_graph, c_id, (c_id, go), out_c_id)
			min_zoom[meta_node] = level - 1
			max_zoom[meta_node] = level - 1
			for m in root[VIEW_META_GRAPH][meta_node].getNodes():
				min_zoom[m] = level
			# comp_names.append(name)
			meta_nodes.append(meta_node)
		level2meta_nodes[level] = meta_nodes
		# layout_cytoplasm(meta_graph)
		resize_edges(meta_graph)
		# shorten_edges(meta_graph)
		remove_overlaps(meta_graph)
		level -= 1
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
		print "LEVEL: ", level
		for e in sorted((e for e in meta_graph.getEdges()), key = lambda e: root[NAME][meta_graph.source(e) if TYPE_REACTION == root[TYPE][meta_graph.source(e)] else meta_graph.target(e)]):
			print root[NAME][meta_graph.source(e)], " : ", root[NAME][meta_graph.target(e)], ' - ', e_min_zoom(e), " : ", e_max_zoom(e)
		print
		for e in (e for e in meta_graph.getEdges() if level == e_min_zoom(e)):
			features.append(edge2feature(meta_graph, e, i, scale, e_min_zoom(e), e_max_zoom(e), x_scale, y_scale))
			i += 1

		for n in (n for n in meta_graph.getNodes() if level == min_zoom[n]):
			f, bg = node2feature(meta_graph, n, i, scale, min_zoom[n], max_zoom[n], max_level + 1, onto)
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

	json = '%s/%s.json' % (directory, root_compartment)
	fc = geojson.FeatureCollection(features, geometry=geojson.Polygon([[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]]))
	with open(json, 'w+') as f:
		f.write("var gjsn__{1} = {0}\n".format(geojson.dumps(fc).replace('"id": null', ''), root_compartment))

	comp_names = [root_compartment]

	log(verbose, 'create html')
	groups_sbml_url = os.path.basename(groups_sbml)

	embed_url = '%s/%s/comp_min.html' % (main_url, m_dir_id)
	redirect_url = 'comp.html'
	archive_url = "%s.zip" % m_dir_id
	create_html(input_model, directory, url, embed_url, redirect_url, comp_names, groups_sbml_url, archive_url, scripts,
	            css, fav)

	create_embedded_html(input_model, directory, comp_names, scripts, css, fav)

	archive_path = "%s/../../uploads/%s.zip" % (directory, m_dir_id)
	archive(directory, archive_path)
	if os.path.exists(archive_path):
		copyfile(archive_path, "%s/%s.zip" % (directory, m_dir_id))
		os.remove(archive_path)

	# TODO: why doesn't it work??
	# tlp.saveGraph(graph.getRoot(), m_dir + '/graph.tlpx')

	log(verbose, 'returning url: %s' % url)
	return url


# def process(graph, m_dir, meta_node, compartment, layout_algorithm=layout, args=None):
# if not args:
#         args = []
#     root = graph.getRoot()
#     comp_graph = root[VIEW_META_GRAPH][meta_node]
#     # layout
#     layout_algorithm(comp_graph)
#     # color
#     # simple_color(graph)
#     # generalization-based layout for the full graph
#     comp_graph_full = layout_generalization_based(comp_graph, *args)
#     root[VIEW_SIZE][meta_node] = get_comp_size(graph, meta_node)
#     # export to geojson
#     compartment = compartment.lower().replace(' ', '_')
#     # full_json = '%s/%s_f.json' % (m_dir, compartment)
#     # tulip2geojson(comp_graph_full, full_json)
#     # generalized_json = '%s/%s.json' % (m_dir, compartment)
#     # tulip2geojson(comp_graph, generalized_json)
#
#     json = '%s/%s.json' % (m_dir, compartment)
#     tulip2geojson(comp_graph_full, comp_graph, json, compartment)


def process_generalized_entities(graph):
	ns = list(graph.getNodes())
	meta_graph = graph.inducedSubGraph(ns)
	meta_graph.setName("meta graph")
	original_graph = graph.inducedSubGraph(ns)
	original_graph.setName("full graph")
	factor_nodes(meta_graph)
	return meta_graph


class VisualisationThread(threading.Thread):
	def __init__(self, m_dir_id, sbml):
		threading.Thread.__init__(self)
		self.sbml = sbml
		self.m_dir_id = m_dir_id

	def run(self):
		visualize_model('../html/', self.m_dir_id, MIMOZA_URL, 'comp.html', self.sbml, JS_SCRIPTS, CSS_SCRIPTS,
		                MIMOZA_FAVICON, True)