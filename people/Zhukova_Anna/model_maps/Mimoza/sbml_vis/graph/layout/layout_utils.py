from tulip import tlp

from sbml_vis.graph.graph_properties import *


COMPONENT_PACKING = "Connected Component Packing"

FM3 = "FM^3 (OGDF)"

CIRCULAR = "Circular (OGDF)"

HIERARCHICAL_GRAPH = "Hierarchical Graph"


def get_distance(qo):
	root = qo.getRoot()
	n2size = {n: max(root[VIEW_SIZE][n].getW(), root[VIEW_SIZE][n].getH()) for n in qo.getNodes()}

	def get_neighbour_size(n):
		neighbour_sizes = {n2size[m] for m in qo.getOutNodes(n) if m in n2size}
		return max(neighbour_sizes) if neighbour_sizes else 0

	return max(n2size[n] + get_neighbour_size(n) for n in n2size.iterkeys()) / 4


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


def detect_components(graph, cycle_number_threshold=3, node_number_threshold=50):
	comp_list = tlp.ConnectedTest.computeConnectedComponents(graph)
	cycles, simples, mess = [], [], []
	for ns in comp_list:
		gr = graph.inducedSubGraph(ns)
		visited = set()
		cycles_num = dfs(list(ns)[0], gr, visited, None, cycle_number_threshold)
		if next((n for n in ns if graph.getRoot()[TYPE][n] == TYPE_COMPARTMENT), None):
			gr.setName("mess (has compartment)")
			mess.append(gr)
		elif cycles_num == 0:
			gr.setName("acyclic")
			simples.append(gr)
		elif cycles_num <= cycle_number_threshold * 2 and len(ns) < node_number_threshold or cycles_num <= 1 * 2:
			gr.setName("cycle")
			cycles.append(gr)
		else:
			gr.setName("mess (%d)" % cycles_num)
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

