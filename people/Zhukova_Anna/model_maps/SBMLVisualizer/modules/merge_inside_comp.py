from collections import defaultdict
from model_utils import merge_nodes
from modules.graph_properties import COMPARTMENT, UBIQUITOUS, ID


def mic(graph):
	root = graph.getRoot()
	compartment = root.getStringProperty(COMPARTMENT)
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	id_ = root.getStringProperty(ID)

	id2connected = {}
	id2unused = defaultdict(list)
	for n in (n for n in graph.getNodes() if ubiquitous[n]):
		comp = compartment[n]
		# Check if it is connected to something inside this compartment
		connected = next((m for m in graph.getInOutNodes(n) if comp == compartment[m]), None)
		_id = comp, id_[n]
		if connected:
			id2connected[_id] = n
		else:
			id2unused[_id].append(n)
	for _id, unused_ns in id2unused.iteritems():
		if _id in id2connected:
			unused_ns.append(id2connected[_id])
		merge_nodes(graph, unused_ns)
