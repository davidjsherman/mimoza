from sbml_vis.tulip.graph_properties import VIEW_META_GRAPH

__author__ = 'anna'


def clone_node(graph, n):
	root = graph.getRoot()

	graphs_to_update = get_graphs_by_node(n, root)
		
	e_to_delete = set(graph.getInOutEdges(n))
	for out_e in graph.getOutEdges(n):
		out = graph.target(out_e)
		gr_up = filter(lambda g: g.isElement(out) and g.existEdge(n, out), graphs_to_update)
		dup = duplicate_node(gr_up, n)
		copy_edge(gr_up, out_e, dup, out, graph)
			
	for in_e in graph.getInEdges(n):
		in_n = graph.source(in_e)
		gr_up = filter(lambda g: g.isElement(in_n) and g.existEdge(in_n, n), graphs_to_update)
		dup = duplicate_node(gr_up, n)
		copy_edge(gr_up, in_e, in_n, dup, graph)
		
	for e in e_to_delete:
		root.delEdge(e)
	for gr in graphs_to_update:
		if gr.isElement(n) and gr.deg(n) == 0:	
			gr.delNode(n)


def duplicate_node(graphs_to_update, node, banned_props=None):
	root = graphs_to_update[0].getRoot()
	dup = root.addNode()
	for graph in graphs_to_update:
		if not graph.isElement(dup):
			graph.addNode(dup)
	for prop_name in root.getProperties():
		if banned_props and prop_name in banned_props:
			continue
		root[prop_name][dup] = root[prop_name][node]
	return dup


def copy_node(graph, n):
	root = graph.getRoot()

	graphs_to_update = get_graphs_by_node(n, root)
	banned_props = [VIEW_META_GRAPH]
	dup = duplicate_node(graphs_to_update, n, banned_props)

	e_to_delete = set(graph.getInOutEdges(n))
	for out_e in graph.getOutEdges(n):
		out = graph.target(out_e)
		gr_up = filter(lambda g: g.isElement(out) and g.existEdge(n, out), graphs_to_update)
		copy_edge(gr_up, out_e, dup, out, graph, banned_props)

	for in_e in graph.getInEdges(n):
		in_n = graph.source(in_e)
		gr_up = filter(lambda g: g.isElement(in_n) and g.existEdge(in_n, n), graphs_to_update)
		copy_edge(gr_up, in_e, in_n, dup, graph, banned_props)

	for e in e_to_delete:
		root.delEdge(e, True)
	root.delNode(n, True)

	return dup


def copy_edge(graphs_to_update, edge, from_n, to_n, graph, banned_props=None):
	for gr in graphs_to_update:
		e = gr.addEdge(from_n, to_n)
		for prop_name in gr.getProperties():
			if banned_props and prop_name in banned_props:
				continue
			gr[prop_name][e] = graph[prop_name][edge]


def get_graphs_by_node(n, root):
	if not root.isElement(n):
		return []
	graphs_to_update = [root]
	for gr in root.getSubGraphs():
		graphs_to_update.extend(get_graphs_by_node(n, gr))
	return graphs_to_update


def merge_nodes(graph, ns):
	if len(ns) <= 1:
		return

	root = graph.getRoot()
	
	# graphs_to_update = set()
	# for m in ns:
	# 	graphs_to_update |= set(get_graphs_by_node(m, root))
	# graphs_to_update -= {root}
	n = ns.pop()
	for m in ns:
		for e in root.getInEdges(m):
			root.setTarget(e, n)
		for e in root.getOutEdges(m):
			root.setSource(e, n)
		root.delNode(m, True)
