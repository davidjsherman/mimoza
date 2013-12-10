from tulip import *
from model_utils import merge_nodes

def mic(graph): 
	compartment =  graph.getStringProperty("compartment")
	ubiquitous =  graph.getBooleanProperty("ubiquitous")
	id_ = graph.getStringProperty("id")

	id2cool = {}
	id2danger = {}
	for n in graph.getNodes():
		comp = compartment[n]
		if ubiquitous[n]:			
			danger = True
			for m in graph.getInOutNodes(n):
				comp_m = compartment[m]
				if comp == comp_m:
					danger = False
					break
			_id = comp, id_[n]
			if not danger:
				id2cool[_id] = n
			else:
				if _id in id2danger:
					id2danger[_id].append(n)
				else:
					id2danger[_id] = [n]
	for _id, danger in id2danger.iteritems():
		if _id in id2cool:
			danger.append(id2cool[_id])
		merge_nodes(graph, danger)	
