from tulip import tlp
import sys
from modules.color import color
from modules.factoring import factor_nodes, factor_comps
from modules.geojson_helper import tulip2geojson
from modules.layout_utils import layout_generalization_based, layout
from modules.sbml2tlp import import_sbml

__author__ = 'anna'


def main(argv=None):
	graph = tlp.newGraph()
	# sbml -> tulip graph
	graph = import_sbml(graph, '/Users/anna/Documents/PhD/magnome/model_generalization/code/MODEL1111190000_pero_with_groups.xml')
	print len([n for n in graph.getNodes()])

	# generalized species/reactions -> metanodes
	ns = list(graph.getNodes())
	meta_graph = graph.inducedSubGraph(ns)
	meta_graph.setName("meta graph")
	original_graph = graph.inducedSubGraph(ns)
	original_graph.setName("full graph")
	factor_nodes(meta_graph)
	print len([n for n in meta_graph.getNodes()])

	# compartments -> metanodes
	organelle2meta_node = factor_comps(meta_graph)
	print organelle2meta_node

	# color
	color(graph)

	for organelle, meta_node in organelle2meta_node.iteritems():
		print organelle
		comp_graph = meta_graph["viewMetaGraph"][meta_node]
		print len([n for n in comp_graph.getNodes()])
		# layout
		layout(comp_graph)

		# generalization-based layout for the full graph
		comp_graph_full = layout_generalization_based(comp_graph)
		print len([n for n in comp_graph_full.getNodes()])

		# export to geojson
		tulip2geojson(comp_graph_full, '/Users/anna/Documents/PhD/magnome/model_generalization/code/perox_f.json')
		tulip2geojson(comp_graph, '/Users/anna/Documents/PhD/magnome/model_generalization/code/perox.json')



if __name__ == "__main__":
	sys.exit(main())