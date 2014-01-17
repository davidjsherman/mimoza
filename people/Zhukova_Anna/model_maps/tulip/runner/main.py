from tulip import tlp
import sys
from libsbml import SBMLReader
from modules.color import color
from modules.factoring import factor_nodes, factor_comps
from modules.geojson_helper import tulip2geojson
from modules.html_generator import generate_html
from modules.layout_utils import layout_generalization_based, layout
from modules.sbml2tlp import import_sbml

__author__ = 'anna'
dir = '/Users/anna/Documents/PhD/magnome/model_maps/WS/'
sbml_file = '/Users/anna/Documents/PhD/magnome/model_generalization/code/MODEL1111190000_golgi.xml'


def main(argv=None):
	graph = tlp.newGraph()
	# sbml -> tulip graph
	reader = SBMLReader()
	input_document = reader.readSBML(sbml_file)
	input_model = input_document.getModel()
	graph = import_sbml(graph, input_model, sbml_file)

	# generalized species/reactions -> metanodes
	ns = list(graph.getNodes())
	meta_graph = graph.inducedSubGraph(ns)
	meta_graph.setName("meta graph")
	original_graph = graph.inducedSubGraph(ns)
	original_graph.setName("full graph")
	factor_nodes(meta_graph)

	# compartments -> metanodes
	organelle2meta_node = factor_comps(meta_graph)

	organelle2graphs = {}

	for organelle, meta_node in organelle2meta_node.iteritems():
		print organelle
		comp_graph = meta_graph["viewMetaGraph"][meta_node]
		# layout
		layout(comp_graph)

		# generalization-based layout for the full graph
		comp_graph_full = layout_generalization_based(comp_graph)
		organelle2graphs[organelle] = [comp_graph, comp_graph_full]

	# color
	color(graph)
	for organelle, graphs in organelle2graphs.iteritems():
		# export to geojson
		organelle = organelle.lower().replace(' ', '_')
		full_json = '{0}{1}_f.json'.format(dir, organelle)
		tulip2geojson(graphs[1], full_json)
		generalized_json = '{0}{1}.json'.format(dir, organelle)
		tulip2geojson(graphs[0], generalized_json)


	generate_html(input_model, dir + 'comp.html', organelle2meta_node.keys())

	# TODO: why doesn't it work??
	tlp.saveGraph(graph.getRoot(), dir + 'graph.tlpx')



if __name__ == "__main__":
	sys.exit(main())