import tulipgui
from tulip import tlp
from libsbml import SBMLReader, os
from modules.color import simple_color
from modules.factoring import factor_nodes, factor_comps, factor_cytoplasm
from modules.geojson_helper import tulip2geojson
from modules.html_generator import generate_html
from modules.layout_utils import layout_generalization_based, layout, layout_cytoplasm
from modules.resize import get_comp_size
from modules.sbml2tlp import import_sbml
from runner.os_helper import copy_sbml_file

__author__ = 'anna'


def visualize_model(directory, main_url, url_end, sbml, scripts, css, fav, tile, verbose):
	reader = SBMLReader()
	input_document = reader.readSBML(sbml)
	input_model = input_document.getModel()
	model_id = input_model.getId()
	if not model_id:
		model_id = 'unknown'
	directory = '%s/%s/' % (directory, model_id)
	url = '%s/%s/%s' % (main_url, model_id, url_end)
	new_sbml_file = copy_sbml_file(directory, sbml, model_id)
	# sbml -> tulip graph
	graph = tlp.newGraph()
	graph, groups_sbml, onto = import_sbml(graph, input_model, new_sbml_file, verbose)
	# generalized species/reactions -> metanodes
	meta_graph = process_generalized_entities(graph)
	# compartments -> metanodes
	compartment2meta_node = factor_comps(meta_graph)
	for organelle, meta_node in compartment2meta_node.iteritems():
		process(graph, directory, meta_node, organelle, lambda gr: layout(gr, onto))

	# cytoplasm
	cytoplasm, meta_node = factor_cytoplasm(meta_graph)
	process(graph, directory, meta_node, cytoplasm, layout_cytoplasm, [set(compartment2meta_node.values()), True])
	groups_sbml_url = "%s/%s/%s" % (main_url, model_id, os.path.basename(groups_sbml))
	generate_html(input_model, directory, url, [cytoplasm] + sorted(compartment2meta_node.keys()), groups_sbml_url,
	              scripts, css, fav, tile)

	# TODO: why doesn't it work??
	# tlp.saveGraph(graph.getRoot(), m_dir + '/graph.tlpx')

	return url


def process(graph, m_dir, meta_node, compartment, layout_algorithm=layout, args=None):
	if not args:
		args = []
	root = graph.getRoot()
	comp_graph = root["viewMetaGraph"][meta_node]
	# layout
	layout_algorithm(comp_graph)
	# color
	simple_color(graph)
	# generalization-based layout for the full graph
	comp_graph_full = layout_generalization_based(comp_graph, *args)
	root['viewSize'][meta_node] = get_comp_size(graph, meta_node)
	# export to geojson
	compartment = compartment.lower().replace(' ', '_')
	full_json = '%s/%s_f.json' % (m_dir, compartment)
	tulip2geojson(comp_graph_full, full_json)
	generalized_json = '%s/%s.json' % (m_dir, compartment)
	tulip2geojson(comp_graph, generalized_json)


def process_generalized_entities(graph):
	ns = list(graph.getNodes())
	meta_graph = graph.inducedSubGraph(ns)
	meta_graph.setName("meta graph")
	original_graph = graph.inducedSubGraph(ns)
	original_graph.setName("full graph")
	factor_nodes(meta_graph)
	return meta_graph