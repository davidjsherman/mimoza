from math import atan2, cos, sin, sqrt
from tulip import tlp

from sbml_vis.graph.layout.generalized_layout import rotate_fake_ns
from sbml_vis.graph.resize import get_n_size
from sbml_vis.graph.graph_properties import *
from sbml_vis.graph.layout.ubiquitous_layout import ub_or_single, remove_overlaps, layout_ub_reaction

COMPONENT_PACKING = "Connected Component Packing"

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


def layout_cytoplasm(graph, margin=1):
	root = graph.getRoot()
	create_fake_rs(graph)
	layout_force(graph, margin)
	remove_overlaps(graph, margin)
	rotate_fake_ns(graph)
	open_meta_ns(graph, (r for r in graph.getNodes() if root[FAKE][r]))
	pack_cc(graph)

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


def open_meta_ns(meta_graph, ns):
	root = meta_graph.getRoot()
	for n in sorted(ns, key=lambda mn: -root[VIEW_META_GRAPH][mn].getId()):
		inner_ns = root[VIEW_META_GRAPH][n].getNodes()
		meta_graph.openMetaNode(n)
		for inner_n in inner_ns:
			root[VIEW_SIZE][inner_n] = get_n_size(meta_graph, inner_n)


def layout(graph, margin=1):
	root = graph.getRoot()
	gr = graph.inducedSubGraph([n for n in graph.getNodes()])
	create_fake_rs(gr)
	simples, cycles, mess = detect_components(gr)
	for qo in simples:
		layout_hierarchically(qo, margin)
	for qo in cycles:
		layout_circle(qo, margin)
	for qo in mess:
		layout_force(qo, margin)
		remove_overlaps(qo, margin)
	rotate_fake_ns(gr)
	open_meta_ns(gr, (r for r in gr.getNodes() if root[FAKE][r]))
	graph.delAllSubGraphs(gr)

	pack_cc(graph)


def create_fake_rs(meta_graph):
	root = meta_graph.getRoot()
	r_ns = [r for r in root.getNodes() if TYPE_REACTION == root[TYPE][r]]
	for r in r_ns:
		r_n = r_to_meta_node(meta_graph, r)
		if r_n:
			mg = root[VIEW_META_GRAPH][r_n]
			root[MAX_ZOOM][r_n] = max(root[MAX_ZOOM][n] for n in mg.getNodes())
			root[MIN_ZOOM][r_n] = min(root[MIN_ZOOM][n] for n in mg.getNodes())


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


def r_to_meta_node(meta_graph, r):
	root = meta_graph.getRoot()

	ubs = []
	for s in root.getInOutNodes(r):
		if ub_or_single(s, root) and meta_graph.isElement(s):
			ubs.append(s)

	if meta_graph.isElement(r):
		ubs.append(r)

	if len(ubs) <= 1:
		return None


	r_n = meta_graph.createMetaNode(ubs, False)
	r_graph = root[VIEW_META_GRAPH][r_n]
	# layout_hierarchically(r_graph)
	layout_ub_reaction(r_graph, r)

	for prop in [NAME, ID, TYPE, ANNOTATION, TRANSPORT, REVERSIBLE]:
		root[prop][r_n] = root[prop][r]

	root[COMPARTMENT][r_n] = root[COMPARTMENT][ubs[0]]

	root[FAKE][r_n] = True
	root[VIEW_SHAPE][r_n] = CIRCLE_SHAPE

	root[VIEW_SIZE][r_n] = get_n_size(meta_graph, r_n)

	return r_n