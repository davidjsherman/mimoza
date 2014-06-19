from collections import defaultdict

from sbml_vis.tulip.node_cloner import merge_nodes
from sbml_vis.tulip.graph_properties import COMPARTMENT, UBIQUITOUS, ID


def mic(graph):
	root = graph.getRoot()
	compartment = root.getStringProperty(COMPARTMENT)
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	id_ = root.getStringProperty(ID)

	id2unused = defaultdict(list)
	for n in (n for n in graph.getNodes() if ubiquitous[n]):
		comp = compartment[n]
		# Check if it is connected to something inside this compartment
		connected = next((m for m in graph.getInOutNodes(n) if comp == compartment[m]), None)
		_id = comp, id_[n]
		if not connected:
			id2unused[_id].append(n)
	for _id, unused_ns in id2unused.iteritems():
		merge_nodes(graph, unused_ns)
