from math import atan2, cos, sin, sqrt

from tulip import tlp
from sbml_vis.graph.graph_properties import *
from sbml_vis.graph.layout.ubiquitous_layout import layout_ub_sps, ub_or_single, remove_overlaps


COMPONENT_PACKING = "Connected Component Packing (Polyomino)"  # "Connected Component Packing"

FM3 = "FM^3 (OGDF)"

CIRCULAR = "Circular (OGDF)"

HIERARCHICAL_GRAPH = "Hierarchical Graph"


def shorten_edges(graph):
	root = graph.getRoot()
	diameter = lambda a, b: sqrt(pow(a, 2) + pow(b, 2))
	for i in xrange(5):
		processed = set()
		moved = set()
		for s in sorted((n for n in graph.getNodes() if not ub_or_single(n, graph)),
		                key=lambda n: -root[VIEW_SIZE][n].getW()):
			processed.add(s)
			s_lo, s_s = root[VIEW_LAYOUT][s], root[VIEW_SIZE][s]
			for t in (n for n in graph.getInOutNodes(s) if not ub_or_single(n, graph) and not n in processed):
				t_lo, t_s = root[VIEW_LAYOUT][t], root[VIEW_SIZE][t]
				dx, dy = t_lo.getX() - s_lo.getX(), t_lo.getY() - s_lo.getY()
				e_len = diameter(dx, dy)
				short_len = diameter(s_s.getW(), s_s.getH()) / 2 + diameter(t_s.getW(), t_s.getH()) / 2
				if e_len > short_len:
					if not t in moved:
						alpha = atan2(dx, dy)
						root[VIEW_LAYOUT][t] = tlp.Coord(s_lo.getX() + short_len * sin(alpha),
						                                 s_lo.getY() + short_len * cos(alpha))
						moved.add(t)
					else:
						alpha = atan2(-dx, -dy)
						root[VIEW_LAYOUT][s] = tlp.Coord(t_lo.getX() + short_len * sin(alpha),
						                                 t_lo.getY() + short_len * cos(alpha))
						moved.add(s)

					# layout_ub_sps(graph)


def neighbours(ns, org_ns, graph, processed, limit=500):
	if not ns or limit < len(ns): return set()
	processed |= ns
	all_ns = set()
	for n in ns:
		all_ns |= (set(graph.getInOutNodes(n)) - processed)
	return ns | neighbours(all_ns, org_ns, graph, processed, limit - len(ns))


def layout_cytoplasm(graph, margin=1):
	root = graph.getRoot()
	# for n in graph.getNodes():
	# if TYPE_SPECIES == root[TYPE][n] and not n in node2graph and graph.deg(n) >= 4:
	# clone_node(graph, n)
	sub = graph.inducedSubGraph([n for n in graph.getNodes() if not ub_or_single(n, graph)])
	layout_force(sub, margin)
	remove_overlaps(sub, margin)
	pack_cc(sub)
	graph.delAllSubGraphs(sub)


# layout_ub_sps(graph, c_id2n, c_id2outs)
# graph.applyAlgorithm("Edge bundling")


def get_distance(qo):
	root = qo.getRoot()
	return max(
		root[VIEW_SIZE][n].getW() + (max(root[VIEW_SIZE][m].getW() for m in qo.getOutNodes(n)) if qo.outdeg(n) else 0)
		for n in qo.getNodes()) / 2


def layout_hierarchically(qo, margin=1):
	root = qo.getRoot()
	ds = tlp.getDefaultPluginParameters(HIERARCHICAL_GRAPH, qo)
	if qo.numberOfNodes() > 1:
		# looks like there is a bug in Tulip and it uses the 'layer spacing' value
		# instead of the 'node spacing' one and visa versa
		d = get_distance(qo)
		ds["layer spacing"] = d + margin
		ds["node spacing"] = d + margin
	qo.computeLayoutProperty(HIERARCHICAL_GRAPH, root[VIEW_LAYOUT], ds)


def layout_circle(qo, margin=1):
	root = qo.getRoot()
	ds = tlp.getDefaultPluginParameters(CIRCULAR, qo)
	if qo.numberOfNodes() > 1:
		ds["minDistCircle"] = get_distance(qo) + margin
		ds["minDistLevel"] = margin
		ds["minDistCC"] = 1
		ds["minDistSibling"] = 0
	qo.computeLayoutProperty(CIRCULAR, root[VIEW_LAYOUT], ds)


def layout_force(qo, margin=1):
	root = qo.getRoot()
	ds = tlp.getDefaultPluginParameters(FM3, qo)
	ds["Unit edge length"] = margin
	qo.computeLayoutProperty(FM3, root[VIEW_LAYOUT], ds)


def pack_cc(graph):
	root = graph.getRoot()
	ds = tlp.getDefaultPluginParameters(COMPONENT_PACKING, graph)
	graph.computeLayoutProperty(COMPONENT_PACKING, root[VIEW_LAYOUT], ds)


def layout(graph, margin=1):
	root = graph.getRoot()

	nodes_with_edges = [n for n in graph.getNodes() if graph.deg(n)]
	nodes_wo_edges = [m for m in graph.getNodes() if not graph.deg(m)]
	if nodes_with_edges:
		gr = graph.inducedSubGraph(nodes_with_edges)
		# sub = gr.inducedSubGraph([n for n in gr.getNodes() if not ub_or_single(n, gr)])
		simples, cycles, mess = detect_components(gr)

		# side = None
		for qo in simples:
			layout_hierarchically(qo, margin)
		# d = max((qo.deg(n) for n in qo.getNodes()))
		# if d > 2:
		# layout_hierarchically(qo, margin)
		# else:
		# if not side:
		# 		side = get_side(graph)
		# 	lo_a_line(qo, side)

		for qo in cycles:
			layout_circle(qo, margin)

		for qo in mess:
			layout_force(qo, margin)
			remove_overlaps(qo, margin)

		# layout_ub_sps(gr)
		pack_cc(gr)
		graph.delAllSubGraphs(gr)
	if nodes_wo_edges:
		gr = root.inducedSubGraph(nodes_wo_edges)
		pack_cc(gr)
		root.delAllSubGraphs(gr)
	pack_cc(graph)


# apply_layout(graph, onto)


def detect_components(graph):
	comp_list = tlp.ConnectedTest.computeConnectedComponents(graph)
	cycles, simples, mess = [], [], []
	threshold = 3
	for ns in comp_list:
		gr = graph.inducedSubGraph(ns)
		visited = set()
		cycles_num = dfs(list(ns)[0], gr, visited, None, threshold)
		if cycles_num == 0:
			gr.setName("acyclic")
			simples.append(gr)
		elif cycles_num < threshold * 2 and len(ns) < 100:
			gr.setName("cycle")
			cycles.append(gr)
		else:
			gr.setName("mess ({0})".format(cycles_num))
			mess.append(gr)
	return simples, cycles, mess


# deep-first search
# every cycle will be counted twice
# as every node of a cycle can be approached from two sides
def dfs(n, graph, visited, prev, limit=3, indent=''):
	if n in visited:
		return 1
	num = 0
	visited.add(n)
	for m in graph.getInOutNodes(n):
		if m == prev:
			continue
		else:
			num += dfs(m, graph, visited, n, limit, indent + ' ')
			if num > limit:
				return num
	return num


def get_side(graph):
	root = graph.getRoot()
	l = 0
	for n in graph.getNodes():
		s = root[VIEW_SIZE][n]
		l += s.getW() * s.getH() * 16
	return sqrt(l)


# expects to be called on a subgraph that has no ubiquitous nodes.
def lo_a_line(graph, side=None):
	root = graph.getRoot()
	root[VIEW_LAYOUT].setAllEdgeValue([])

	starts = (n for n in graph.getNodes() if 1 == graph.deg(n))

	if not side:
		side = get_side(graph)

	processed = set()
	x, y = 0, side
	max_h = 0

	def process_n(n, x, y, max_h):

		def get_coord(s, x, y, max_h):
			x += s.getW() / 2 + 2
			if x > side:
				x = 0
				y -= max_h * 4
				max_h = s.getH()
			return x, y, max_h

		processed.add(n)
		s = root[VIEW_SIZE][n]
		max_h = max(max_h, s.getH())
		x, y, max_h = get_coord(s, x, y, max_h)
		root[VIEW_LAYOUT][n] = tlp.Coord(x, y)
		x, y, max_h = get_coord(s, x, y, max_h)
		return x, y, max_h

	for n in starts:
		if n in processed:
			continue
		x = side
		x, y, max_h = process_n(n, x, y, max_h)
		while True:
			n = next((m for m in graph.getInOutNodes(n) if not (m in processed)), None)
			if not n:
				break
			x, y, max_h = process_n(n, x, y, max_h)
	return graph