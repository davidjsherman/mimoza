from tulip import *
#from metabolic_widgets import SpeciesTypeSelectionDialog

def getCurrentUbiquitousSpecific(graph, nodes):
	ub = graph.getRoot().getBooleanProperty("ubiquitous")
	parentProp = graph.getRoot().getStringProperty("ancestor")
	ubs = set(filter(lambda it: ub[it], nodes))
	if not ubs: ubs = computeUbiquotousSpecies(graph, nodes)
	return ubs, {graph["id"][n] : parentProp[n] \
	if parentProp[n] else graph["id"][n] for n in nodes - ubs}
	
def getReactionsSpecies(graph):
	ns = set(graph.getNodes())
	rs = set(filter(lambda it: graph["reaction"][it], ns))
	return rs, ns - rs

#def computeUbiquotousSpecies(graph, species):
#	ubiquitous = graph.getRoot().getBooleanProperty("ubiquitous")
#	speciesType = graph.getStringProperty("speciesType")
#	id_ = graph.getStringProperty("id")
#	ubiquotous_species = set()
#	speciesTypeSelDialog = SpeciesTypeSelectionDialog(graph, title="Select ubiquitous species", \
#	condition="Mark ubiquitous those with degree greater than: ", left_label="Specific species:", \
#	right_label="Ubiquitous species:")
#	speciesTypeSelDialog.exec_()
#	toDuplicate = speciesTypeSelDialog.getSpeciesTypesToDuplicate()
#	for n in species:
#		if speciesType[n] in toDuplicate:
#			ubiquotous_species.add(id_[n])
#			ubiquitous[n] = True
#	return ubiquotous_species
	
def getReaction2compartment(reactions, graph):
	compartment = graph.getStringProperty("compartment")
	compartment2reactions = {}
	for n in reactions:
		comp = compartment[n]
		if not comp:
				comps = set(map(lambda it: compartment[it], graph.getInOutNodes(n)))
				if len(comps) == 1:
					comp = comps.pop()
		if comp:
				if not compartment2reactions.has_key(comp): compartment2reactions[comp] = []
				compartment2reactions[comp].append(n)
	return compartment2reactions
	
def getRP(r, graph):
	id_ =  graph.getStringProperty("id")
	transform = lambda f: set(map(lambda it: id_[it], f))
	return transform(graph.getInNodes(r)), transform(graph.getOutNodes(r))
	
def cloneNode(graph, n):		
	root = graph.getRoot()
	clone = root.getBooleanProperty("clone")			
	nbClones = root.getIntegerProperty("nbClones")
	
	clone[n] = True
	if nbClones[n]:
		nbClones[n] = nbClones[n] - 1 + graph.deg(n)
	else:
		nbClones[n] = graph.deg(n)
	graphs_to_update = getGraphsByNode(n, root)	
		
	e_to_delete = set(graph.getInOutEdges(n))
	for out_e in graph.getOutEdges(n):
		out = graph.target(out_e)
		gr_up = filter(lambda g: g.isElement(out) and g.existEdge(n, out), graphs_to_update)
		dup = duplicateNode(gr_up, n)
		copyEdge(gr_up, out_e, dup, out, graph)
			
	for in_e in graph.getInEdges(n):
		in_n = graph.source(in_e)
		gr_up = filter(lambda g: g.isElement(in_n) and g.existEdge(in_n, n), graphs_to_update)
		dup = duplicateNode(gr_up, n)
		copyEdge(gr_up, in_e, in_n, dup, graph)
		
	for e in e_to_delete:
		root.delEdge(e)
	for gr in graphs_to_update:
		if gr.isElement(n) and gr.deg(n) == 0:	
			gr.delNode(n)
				
def duplicateNode(graphs_to_update, node):
	root = graphs_to_update[0].getRoot()
	dup = root.addNode()
	for graph in graphs_to_update:
		if not graph.isElement(dup):
			graph.addNode(dup)
		for propName in graph.getProperties():
			graph[propName][dup] = graph[propName][node]
	return dup
	
def copyEdge(graphs_to_update, edge, from_n, to_n, graph):
	for gr in graphs_to_update:
		e = gr.addEdge(from_n, to_n)
		for propName in gr.getProperties():
			gr[propName][e] = graph[propName][edge]
	return e

def getGraphsByNode(n, root):
	if not root.isElement(n):
		return []
	graphs_to_update = [root]
	for gr in root.getSubGraphs():
		graphs_to_update.extend(getGraphsByNode(n, gr))
	return graphs_to_update
	
def clone_nodes(graph, threshold): 
	for n in graph.getNodes():
		if not graph.isMetaNode(n) and not graph["reaction"][n] and graph.deg(n) > threshold:
			cloneNode(graph, n)
			
def merge_nodes(graph, ns):
	root = graph.getRoot()
	clone = root.getBooleanProperty("clone")			
	nbClones = root.getIntegerProperty("nbClones")
	
	graphs_to_update = set()
	for m in ns:
		graphs_to_update |= set(getGraphsByNode(m, root))
	n = ns[0]
	ns = ns[1:]
	for m in ns:
		for from_m in root.getInNodes(m):
			e = root.addEdge(from_m, n)
			for gr in graphs_to_update:
				if gr.isElement(from_m) and gr.isElement(m):
					if not gr.isElement(n):
						gr.addNode(n)	
					gr.addEdge(e)
		for to_m in root.getOutNodes(m):
			e = root.addEdge(n, to_m)
			for gr in graphs_to_update:
				if gr.isElement(to_m) and gr.isElement(m):
					if not gr.isElement(n):
						gr.addNode(n)	
					gr.addEdge(e)
		root.delNode(m, True)
	nbClones[n] = nbClones[n] - len(ns)	

		
