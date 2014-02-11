from tulip import tlp
import sys
from libsbml import SBMLReader, os
from shutil import copyfile
from modules.color import color
from modules.factoring import factor_nodes, factor_comps, factor_cytoplasm
from modules.geojson_helper import tulip2geojson
from modules.html_generator import generate_html
from modules.layout_utils import layout, layout_generalization_based, layout_cytoplasm
from modules.resize import get_comp_size
from modules.sbml2tlp import import_sbml

__author__ = 'anna'
dir = '/Users/anna/Documents/PhD/magnome/model_maps/WS/'
sbml_file = '/Users/anna/Documents/PhD/magnome/model_generalization/code/MODEL1111190000_annotated_with_groups.xml'
# sbml_file = '/Users/anna/Downloads/MODEL1212060001_with_groups.xml'


def create_dir(model_id):
	m_dir = '{0}/{1}'.format(dir, model_id)
	if not os.path.exists(m_dir):
		os.makedirs(m_dir)
	return m_dir


def main(argv=None):
	graph = tlp.newGraph()
	# sbml -> tulip graph
	reader = SBMLReader()
	input_document = reader.readSBML(sbml_file)
	input_model = input_document.getModel()
	model_id = input_model.getId()

	m_dir = create_dir(model_id)
	new_sbml_file = '{0}/{1}.xml'.format(m_dir, model_id)
	if sbml_file != new_sbml_file:
		copyfile(sbml_file, new_sbml_file)
		# os.remove(sbml_file)

	graph, groups_sbml = import_sbml(graph, input_model, new_sbml_file)

	# generalized species/reactions -> metanodes
	ns = list(graph.getNodes())
	meta_graph = graph.inducedSubGraph(ns)
	meta_graph.setName("meta graph")
	original_graph = graph.inducedSubGraph(ns)
	original_graph.setName("full graph")
	factor_nodes(meta_graph)
	root = graph.getRoot()

	# compartments -> metanodes
	organelle2meta_node = factor_comps(meta_graph)

	organelle2graphs = {}

	for organelle, meta_node in organelle2meta_node.iteritems():
		print organelle
		comp_graph = root["viewMetaGraph"][meta_node]
		# layout
		layout(comp_graph)
		# color
		color(graph)
		# generalization-based layout for the full graph
		comp_graph_full = layout_generalization_based(comp_graph)
		# copy_layout(comp_graph_full, graph.getRoot())
		organelle2graphs[organelle] = [comp_graph, comp_graph_full]

		root['viewSize'][meta_node] = get_comp_size(graph, meta_node)

		# export to geojson
		organelle = organelle.lower().replace(' ', '_')
		full_json = '{0}/{1}_f.json'.format(m_dir, organelle)
		tulip2geojson(comp_graph_full, full_json)
		generalized_json = '{0}/{1}.json'.format(m_dir, organelle)
		tulip2geojson(comp_graph, generalized_json)

	# for n in organelle2meta_node.itervalues():
	# 	root['viewSize'][n] = get_comp_size(graph, n)
	#
	# # color
	# color(graph)
	#
	# for organelle, graphs in organelle2graphs.iteritems():
	# 	# export to geojson
	# 	organelle = organelle.lower().replace(' ', '_')
	# 	full_json = '{0}/{1}_f.json'.format(m_dir, organelle)
	# 	tulip2geojson(graphs[1], full_json)
	# 	generalized_json = '{0}/{1}.json'.format(m_dir, organelle)
	# 	tulip2geojson(graphs[0], generalized_json)

	cytoplasm, meta_node = factor_cytoplasm(meta_graph)
	print cytoplasm
	root['viewSize'][meta_node] = get_comp_size(graph, meta_node)
	comp_graph = root["viewMetaGraph"][meta_node]
	# layout
	layout_cytoplasm(comp_graph)
	# color
	color(graph)
	# generalization-based layout for the full graph
	comp_graph_full = layout_generalization_based(comp_graph, set(organelle2meta_node.values()), True)
	organelle2graphs[cytoplasm] = [comp_graph, comp_graph_full]
	organelle2meta_node[cytoplasm] = meta_node

	# export to geojson
	cytoplasm = cytoplasm.lower().replace(' ', '_')
	full_json = '{0}/{1}_f.json'.format(m_dir, cytoplasm)
	tulip2geojson(comp_graph_full, full_json)
	generalized_json = '{0}/{1}.json'.format(m_dir, cytoplasm)
	tulip2geojson(comp_graph, generalized_json)

	generate_html(input_model, '{0}/comp.html'.format(m_dir), organelle2meta_node.keys(), groups_sbml)

	# TODO: why doesn't it work??
	# tlp.saveGraph(graph.getRoot(), m_dir + '/graph.tlpx')



if __name__ == "__main__":
	sys.exit(main())