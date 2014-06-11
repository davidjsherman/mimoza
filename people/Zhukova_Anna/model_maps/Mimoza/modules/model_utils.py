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


def duplicate_node(graphs_to_update, node):
	root = graphs_to_update[0].getRoot()
	dup = root.addNode()
	for graph in graphs_to_update:
		if not graph.isElement(dup):
			graph.addNode(dup)
		for propName in graph.getProperties():
			graph[propName][dup] = graph[propName][node]
	return dup


def copy_edge(graphs_to_update, edge, from_n, to_n, graph):
	for gr in graphs_to_update:
		e = gr.addEdge(from_n, to_n)
		for propName in gr.getProperties():
			gr[propName][e] = graph[propName][edge]


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
	
	graphs_to_update = set()
	for m in ns:
		graphs_to_update |= set(get_graphs_by_node(m, root))
	graphs_to_update -= {root}
	n = ns.pop()
	for m in ns:
		for old_e in root.getInEdges(m):
			from_m = root.source(old_e)
			e = None#root.addEdge(from_m, n)
			for gr in graphs_to_update:
				if gr.isElement(from_m) and gr.isElement(m):
					if not gr.isElement(n):
						gr.addNode(n)
					if e:
						gr.addEdge(e)
					else:
						e = gr.addEdge(from_m, n)
			for propName in root.getProperties():
				root[propName][e] = root[propName][old_e]
		for old_e in root.getOutEdges(m):
			to_m = root.target(old_e)
			e = None#root.addEdge(n, to_m)
			for gr in graphs_to_update:
				if gr.isElement(to_m) and gr.isElement(m):
					if not gr.isElement(n):
						gr.addNode(n)
					if e:
						gr.addEdge(e)
					else:
						e = gr.addEdge(n, to_m)
			for propName in root.getProperties():
				root[propName][e] = root[propName][old_e]
		root.delNode(m, True)
