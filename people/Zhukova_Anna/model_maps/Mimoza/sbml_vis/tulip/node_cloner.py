__author__ = 'anna'


def clone_node(graph, n):
	root = graph.getRoot()

	graphs_to_update = get_graphs_by_node(n, root)

	used_n = False
	for e in root.getInOutEdges(n):
		if not used_n:
			used_n = True
			continue
		# duplicate node
		dup = root.addNode()
		for prop_name in root.getProperties():
			root[prop_name][dup] = root[prop_name][n]

		for graph in (graph for graph in graphs_to_update if graph.isElement(e)):
			if not graph.isElement(dup):
				graph.addNode(dup)
			graph.setTarget(e, dup) if n == graph.target(e) else graph.setSource(e, dup)
	for graph in graphs_to_update:
		if graph.deg(n) == 0:
			graph.delNode(n, True)


def get_graphs_by_node(n, root):
	if not root.isElement(n):
		return []
	graphs_to_update = [root]
	for gr in root.getSubGraphs():
		graphs_to_update = get_graphs_by_node(n, gr) + graphs_to_update
	return graphs_to_update


def merge_nodes(graph, ns):
	if len(ns) <= 1:
		return
	root = graph.getRoot()

	n = ns.pop()
	for m in ns:
		for e in root.getInEdges(m):
			root.setTarget(e, n)
		for e in root.getOutEdges(m):
			root.setSource(e, n)
		root.delNode(m, True)
