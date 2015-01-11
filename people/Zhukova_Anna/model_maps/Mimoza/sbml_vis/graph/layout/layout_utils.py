from tulip import tlp
from sbml_vis.graph.resize import get_mn_size

from sbml_vis.graph.graph_properties import *


COMPONENT_PACKING = "Connected Component Packing"

FM3 = "FM^3 (OGDF)"

CIRCULAR = "Circular (OGDF)"

HIERARCHICAL_GRAPH = "Sugiyama (OGDF)"#"Hierarchical Graph"

OVERLAP_REMOVAL = "Fast Overlap Removal"


def get_distance(qo):
    root = qo.getRoot()
    n2size = {n: max(root[VIEW_SIZE][n].getW(), root[VIEW_SIZE][n].getH()) for n in qo.getNodes()}

    def get_neighbour_size(n):
        neighbour_sizes = {n2size[m] for m in qo.getOutNodes(n) if m in n2size}
        return max(neighbour_sizes) if neighbour_sizes else 0

    return max(min(n2size[n], get_neighbour_size(n)) for n in n2size.iterkeys())


def layout_hierarchically(qo, margin=1):
    root = qo.getRoot()
    ds = tlp.getDefaultPluginParameters(HIERARCHICAL_GRAPH, qo)
    if qo.numberOfNodes() > 1:
        # looks like there is a bug in Tulip and it uses the 'layer spacing' value
        # instead of the 'node spacing' one and visa versa
        d = get_distance(qo)
        # ds["layer spacing"] = d + margin
        # ds["node spacing"] = d + margin
        ds["layer distance"] = d + margin
        ds["node distance"] = d + margin
    qo.computeLayoutProperty(HIERARCHICAL_GRAPH, root[VIEW_LAYOUT], ds)


def layout_circle(qo, margin=1):
    root = qo.getRoot()
    ds = tlp.getDefaultPluginParameters(CIRCULAR, qo)
    if qo.numberOfNodes() > 1:
        dist = get_distance(qo) + margin
        ds["minDistCircle"] = dist
        ds["minDistLevel"] = dist
        ds["minDistCC"] = 1
        ds["minDistSibling"] = dist
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


def remove_overlaps(graph, margin=1):
    root = graph.getRoot()
    ds = tlp.getDefaultPluginParameters(OVERLAP_REMOVAL, graph)
    ds["x border"] = margin
    ds["y border"] = margin
    graph.computeLayoutProperty(OVERLAP_REMOVAL, root[VIEW_LAYOUT], ds)


def layout_components(graph, cycle_number_threshold=25, node_number_threshold=400, margin=5):
    root = graph.getRoot()
    comp_list = tlp.ConnectedTest.computeConnectedComponents(graph)
    for ns in comp_list:
        gr = graph.inducedSubGraph(ns)
        meta_ns = []
        for scc in strongly_connected_components_iterative(gr):
            if len(scc) > 1:
                scc_node = gr.createMetaNode(scc, False)
                scc_graph = root[VIEW_META_GRAPH][scc_node]
                cycles_num = dfs(list(scc)[0], scc_graph, set(), None, cycle_number_threshold)
                if cycles_num > cycle_number_threshold:
                    layout_force(scc_graph, margin)
                    remove_overlaps(scc_graph, margin)
                else:
                    layout_circle(scc_graph, margin)
                root[VIEW_SHAPE][scc_node] = COMPARTMENT_SHAPE
                w, h = get_mn_size(scc_node, root)
                root[VIEW_SIZE][scc_node] = tlp.Size(w, h)
                meta_ns.append(scc_node)
        if gr.numberOfNodes() < node_number_threshold:
            layout_hierarchically(gr)
        else:
            layout_force(gr, margin)
            remove_overlaps(gr, margin)
        for mn in meta_ns:
            gr.openMetaNode(mn)


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


def strongly_connected_components_iterative(graph):
    """
    Find the strongly connected components of a directed graph.

    Uses a recursive linear-time algorithm described by Gabow [1]_ to find all
    strongly connected components of a directed graph.

    Parameters
    ----------
    graph : Graph
        A Tulip graph.

    Returns
    -------
    components : iterator
        An iterator that yields sets of vertices.  Each set produced gives the
        vertices of one strongly connected component.

    Raises
    ------
    RuntimeError
        If the graph is deep enough that the algorithm exceeds Python's
        recursion limit.

    Notes
    -----
    The algorithm has running time proportional to the total number of vertices
    and edges.  It's practical to use this algorithm on graphs with hundreds of
    thousands of vertices and edges.

    References
    ----------
    .. [1] Harold N. Gabow, "Path-based depth-first search for strong and
       biconnected components," Inf. Process. Lett. 74 (2000) 107--114.

    """
    identified = set()
    stack = []
    index = {}
    boundaries = []

    for v in graph.getNodes():
        if v not in index:
            to_do = [('VISIT', v)]
            while to_do:
                operation_type, v = to_do.pop()
                if operation_type == 'VISIT':
                    index[v] = len(stack)
                    stack.append(v)
                    boundaries.append(index[v])
                    to_do.append(('POSTVISIT', v))
                    to_do.extend([('VISITEDGE', w) for w in set(graph.getOutNodes(v)) |
                                  {graph.source(e) for e in graph.getInEdges(v) if graph[REVERSIBLE][e]}])
                elif operation_type == 'VISITEDGE':
                    if v not in index:
                        to_do.append(('VISIT', v))
                    elif v not in identified:
                        while index[v] < boundaries[-1]:
                            boundaries.pop()
                else:
                    # operation_type == 'POSTVISIT'
                    if boundaries[-1] == index[v]:
                        boundaries.pop()
                        scc = set(stack[index[v]:])
                        del stack[index[v]:]
                        identified.update(scc)
                        yield scc


