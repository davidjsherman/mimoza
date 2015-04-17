from collections import defaultdict
from math import sqrt, radians, degrees, cos, sin, atan2
from tulip import tlp

from sbml_vis.graph.layout.layout_utils import pack_cc, layout_components
from sbml_vis.graph.resize import get_n_size, UBIQUITOUS_SPECIES_SIZE, REACTION_SIZE, get_n_length
from sbml_vis.graph.graph_properties import UBIQUITOUS, VIEW_LAYOUT, VIEW_SIZE, TYPE_REACTION, TYPE, TYPE_SPECIES, \
    TYPE_COMPARTMENT, VIEW_META_GRAPH, COMPARTMENT_ID

__author__ = 'anna'


def ub_or_single(nd, graph):
    root = graph.getRoot()
    return (root[UBIQUITOUS][nd] or 1 >= graph.deg(nd)) and TYPE_SPECIES == root[TYPE][nd]


def layout_outer_elements(graph):
    root = graph.getRoot()

    comps = [c for c in graph.getNodes() if TYPE_COMPARTMENT == root[TYPE][c]]
    for c in comps:
        c_bottom_x, c_bottom_y, c_top_x, c_top_y = get_comp_borders(c, root)
        c_w, c_h = (c_top_x - c_bottom_x) / 2, (c_top_y - c_bottom_y) / 2
        rs = sorted([r for r in graph.getInOutNodes(c)
                     if len([s for s in graph.getInOutNodes(r) if not ub_or_single(s, graph)]) == 1],
                    key=lambda r: -get_n_length(root, r))
        comp_mg = root[VIEW_META_GRAPH][c]
        m_x = min(root[VIEW_LAYOUT][s].getX() - root[VIEW_SIZE][s].getW() / 2 for s in comp_mg.getNodes())
        m_y = min(root[VIEW_LAYOUT][s].getY() - root[VIEW_SIZE][s].getH() / 2 for s in comp_mg.getNodes())
        coords = set()
        for r in rs:
            r_w, r_h = root[VIEW_SIZE][r].getW() * 3, root[VIEW_SIZE][r].getH() * 3
            ss = [s for s in root.getInOutNodes(r) if comp_mg.isElement(s)]
            ss_not_ub = [s for s in ss if not ub_or_single(s, comp_mg)]
            if ss_not_ub:
                ss = ss_not_ub
            else:
                ss_not_ub = [s for s in ss if not root[UBIQUITOUS][s]]
                if ss_not_ub:
                    ss = ss_not_ub
            s_x, s_y = sum(root[VIEW_LAYOUT][s].getX() - m_x for s in ss) / len(ss), sum(
                root[VIEW_LAYOUT][s].getY() - m_y for s in ss) / len(ss)
            x = c_bottom_x - r_w if s_x < c_w else c_top_x + r_h
            y = c_bottom_y - r_h if s_y < c_h else c_top_y + r_h

            if abs(c_bottom_x + s_x - x) > abs(c_bottom_y + s_y - y):
                r_x = c_bottom_x + s_x
                r_y = y
                while (r_x, r_y) in coords:
                    r_x += r_w if s_x < c_w else -r_w
                coords.add((r_x, r_y))
            else:
                r_y = c_bottom_y + s_y
                r_x = x
                while (r_x, r_y) in coords:
                    r_y += r_h if s_y < c_h else -r_h
                coords.add((r_x, r_y))
            root[VIEW_LAYOUT][r] = tlp.Coord(r_x, r_y)


def get_comp_borders(c, root):
    c_w, c_h = root[VIEW_SIZE][c].getW() / 2, root[VIEW_SIZE][c].getH() / 2
    c_x, c_y = root[VIEW_LAYOUT][c].getX(), root[VIEW_LAYOUT][c].getY()
    return c_x - c_w, c_y - c_h, c_x + c_w, c_y + c_h


def layout_inner_elements(graph, c_id, (c_bottom_x, c_bottom_y, c_top_x, c_top_y)):
    root = graph.getRoot()

    neighbours_outside_comp = lambda r: [n for n in graph.getInOutNodes(r) if root[COMPARTMENT_ID][n] != c_id]
    neighbours_inside_comp = lambda r: [n for n in graph.getInOutNodes(r) if root[COMPARTMENT_ID][n] == c_id
                                        and not ub_or_single(n, graph)]

    rs = sorted([r for r in graph.getNodes() if root[COMPARTMENT_ID][r] == c_id and not neighbours_inside_comp(r)
                 and neighbours_outside_comp(r)], key=lambda r: -get_n_length(root, r))

    coords = set()
    for r in rs:
        r_w, r_h = root[VIEW_SIZE][r].getW(), root[VIEW_SIZE][r].getH()
        ss = neighbours_outside_comp(r)
        ss_not_ub = [s for s in ss if not ub_or_single(s, graph)]
        if ss_not_ub:
            ss = ss_not_ub
        s_x, s_y = sum(root[VIEW_LAYOUT][s].getX() for s in ss) / len(ss), sum(
            root[VIEW_LAYOUT][s].getY() for s in ss) / len(ss)

        inside_y = c_bottom_y + r_h <= s_y <= c_top_y - r_h
        inside_x = c_bottom_x + r_w <= s_x <= c_top_x - r_w

        if inside_x:
            r_x = s_x
            r_y = c_bottom_y + r_h if abs(s_y - c_bottom_y) < abs(s_y - c_top_y) else c_top_y - r_h
            right = abs(s_x - c_bottom_x) < abs(s_x - c_top_x)
            while (r_x, r_y) in coords:
                if right:
                    r_x += 3 * r_w
                else:
                    r_x -= 3 * r_w
            coords.add((r_x, r_y))
        elif inside_y:
            r_y = s_y
            r_x = c_bottom_x + r_w if abs(s_x - c_bottom_x) < abs(s_x - c_top_x) else c_top_x - r_w
            top = abs(s_y - c_bottom_y) < abs(s_y - c_top_y)
            while (r_x, r_y) in coords:
                if top:
                    r_y += 3 * r_h
                else:
                    r_y -= 3 * r_h
            coords.add((r_x, r_y))
        else:
            i = 1
            while True:
                r_x = max(c_bottom_x + i * r_w, min(s_x, c_top_x - i * r_w))
                r_y = max(c_bottom_y + i * r_h, min(s_y, c_top_y - i * r_h))
                if (r_x, r_y) in coords:
                    i += 1
                else:
                    coords.add((r_x, r_y))
                    break

        root[VIEW_LAYOUT][r] = tlp.Coord(r_x, r_y)

    layout_ub_sps(graph, rs, c_id)

    # open_meta_ns(graph, (r for r in graph.getNodes() if root[FAKE][r]))
    root[VIEW_LAYOUT].setAllEdgeValue([])


def get_reaction_r(r, root):
    return sqrt(pow(root[VIEW_SIZE][r].getW(), 2) + pow(root[VIEW_SIZE][r].getH(), 2)) / 2


def bend_ubiquitous_edges(graph, nodes):
    root = graph.getRoot()
    for r in (r for r in nodes if TYPE_REACTION == root[TYPE][r]):
        r_x, r_y = root[VIEW_LAYOUT][r].getX(), root[VIEW_LAYOUT][r].getY()
        r_r = REACTION_SIZE * sqrt(2) / 2 + UBIQUITOUS_SPECIES_SIZE
        for s in (s for s in graph.getInOutNodes(r) if root[UBIQUITOUS][s] or not graph.isMetaNode(s)):
            s_x, s_y = root[VIEW_LAYOUT][s].getX(), root[VIEW_LAYOUT][s].getY()
            alpha = atan2(s_y - r_y, s_x - r_x)
            x0, y0 = r_x + r_r * cos(alpha), r_y + r_r * sin(alpha)
            for m in root[VIEW_META_GRAPH][r].getNodes():
                for e in root.getInOutEdges(m):
                    if s == root.target(e) or s == root.source(e):
                        root[VIEW_LAYOUT][e] = [tlp.Coord(x0, y0)]


def bend_edges(graph):
    root = graph.getRoot()
    for r in (r for r in graph.getNodes() if TYPE_REACTION == root[TYPE][r]):
        r_x, r_y = root[VIEW_LAYOUT][r].getX(), root[VIEW_LAYOUT][r].getY()
        r_r = get_reaction_r(r, root) + UBIQUITOUS_SPECIES_SIZE / 2
        reactants, products = list(graph.getInNodes(r)), list(graph.getOutNodes(r))

        def get_bend_coord(species):
            sample_species = next((s for s in species if not ub_or_single(s, graph)), None)
            if sample_species:
                s_x, s_y = root[VIEW_LAYOUT][sample_species].getX(), root[VIEW_LAYOUT][sample_species].getY()
            else:
                cs_x, cs_y = [root[VIEW_LAYOUT][s].getX() for s in species], \
                             [root[VIEW_LAYOUT][s].getY() for s in species]
                s_x, s_y = (min(cs_x) + max(cs_x)) / 2, (min(cs_y) + max(cs_y)) / 2
            r_species_angle = atan2(s_y - r_y, s_x - r_x)
            return tlp.Coord(r_x + r_r * cos(r_species_angle), r_y + r_r * sin(r_species_angle))

        if len(products) > 1:
            product_lo = get_bend_coord(products)
            for e in graph.getOutEdges(r):
                root[VIEW_LAYOUT][e] = [product_lo] + root[VIEW_LAYOUT][e]

        if len(reactants) > 1:
            reactant_lo = get_bend_coord(reactants)
            for e in graph.getInEdges(r):
                root[VIEW_LAYOUT][e] = root[VIEW_LAYOUT][e] + [reactant_lo]


def bend_edges_around_compartments(graph, es):
    root = graph.getRoot()
    comps = sorted((c for c in graph.getNodes() if TYPE_COMPARTMENT == root[TYPE][c]),
                   key=lambda c: max(root[VIEW_SIZE][c].getW(), root[VIEW_SIZE][c].getH()))
    for e in es:
        s, t = graph.source(e), graph.target(e)
        s_x, s_y = root[VIEW_LAYOUT][s].getX(), root[VIEW_LAYOUT][s].getY()
        t_x, t_y = root[VIEW_LAYOUT][t].getX(), root[VIEW_LAYOUT][t].getY()

        max_x = max(s_x, t_x)
        min_x = min(s_x, t_x)
        max_y = max(s_y, t_y)
        min_y = min(s_y, t_y)
        w = max(root[VIEW_SIZE][s].getW(), root[VIEW_SIZE][t].getW())
        h = max(root[VIEW_SIZE][s].getH(), root[VIEW_SIZE][t].getH())
        for c in comps:
            if s == c or t == c:
                continue
            c_bottom_x, c_bottom_y, c_top_x, c_top_y = get_comp_borders(c, root)
            if max_x <= c_bottom_x + w or min_x >= c_top_x - w \
                    or max_y <= c_bottom_y + h or min_y >= c_top_y - h:
                continue
            alpha = atan2(t_y - s_y, t_x - s_x)
            c_alphas = [atan2(c_y - s_y, c_x - s_x) for (c_x, c_y) in \
                        [(c_bottom_x + w, c_bottom_y + h), (c_bottom_x + w, c_top_y - h),
                         (c_top_x - w, c_top_y - h), (c_top_x - w, c_bottom_y + h)]]
            if min(c_alphas) < alpha < max(c_alphas):
                bends = []
                if c_bottom_x < min_x <= max_x < c_top_x:
                    if (min_x - c_bottom_x) < (c_top_x - max_x):
                        min_x = c_bottom_x - w * 2
                    else:
                        max_x = c_top_x + w * 2
                elif c_bottom_y < min_y <= max_y < c_top_y:
                    if (min_y - c_bottom_y) < (c_top_y - max_y):
                        min_y = c_bottom_y - h * 2
                    else:
                        max_y = c_top_y + h * 2

                for (x, y) in [(min_x, min_y), (min_x, max_y), (max_x, max_y), (max_x, min_y)]:
                    if (x < c_bottom_x or x > c_top_x) and (y < c_bottom_y or y > c_top_y):
                        if (x, y) != (s_x, s_y) and (x, y) != (t_x, t_y):
                            bends.append((x, y))
                if len(bends) == 2:
                    bends = sorted(bends, key=lambda (x, y): 0 if (s_x == x or s_y == y) else 1)
                if bends:
                    root[VIEW_LAYOUT][e] = [tlp.Coord(x, y) for (x, y) in bends]
                break

    for r in (r for r in graph.getNodes() if TYPE_REACTION == root[TYPE][r]):
        r_x, r_y = root[VIEW_LAYOUT][r].getX(), root[VIEW_LAYOUT][r].getY()
        r_r = get_reaction_r(r, root) + UBIQUITOUS_SPECIES_SIZE / 2
        reactants, products = list(graph.getInNodes(r)), list(graph.getOutNodes(r))

        def get_bend_coord(species):
            sample_species = next((s for s in species if not ub_or_single(s, graph)), None)
            if sample_species:
                s_x, s_y = root[VIEW_LAYOUT][sample_species].getX(), root[VIEW_LAYOUT][sample_species].getY()
            else:
                cs_x, cs_y = [root[VIEW_LAYOUT][s].getX() for s in species], \
                             [root[VIEW_LAYOUT][s].getY() for s in species]
                s_x, s_y = (min(cs_x) + max(cs_x)) / 2, (min(cs_y) + max(cs_y)) / 2
            r_species_angle = atan2(s_y - r_y, s_x - r_x)
            return tlp.Coord(r_x + r_r * cos(r_species_angle), r_y + r_r * sin(r_species_angle))

        if len(products) > 1:
            product_lo = get_bend_coord(products)
            for e in graph.getOutEdges(r):
                root[VIEW_LAYOUT][e] = [product_lo] + root[VIEW_LAYOUT][e]

        if len(reactants) > 1:
            reactant_lo = get_bend_coord(reactants)
            for e in graph.getInEdges(r):
                root[VIEW_LAYOUT][e] = root[VIEW_LAYOUT][e] + [reactant_lo]


def open_meta_ns(meta_graph, ns):
    root = meta_graph.getRoot()
    for n in sorted(ns, key=lambda mn: -root[VIEW_META_GRAPH][mn].getId()):
        inner_ns = root[VIEW_META_GRAPH][n].getNodes()
        meta_graph.openMetaNode(n)
        for inner_n in inner_ns:
            root[VIEW_SIZE][inner_n] = get_n_size(meta_graph, inner_n)


def layout_ub_sps(graph, r_ns=None, c_id=None):
    root = graph.getRoot()
    view_layout = root.getLayoutProperty(VIEW_LAYOUT)
    view_size = root.getSizeProperty(VIEW_SIZE)

    if not r_ns:
        r_ns = (n for n in graph.getNodes() if TYPE_REACTION == root[TYPE][n])

    for r in r_ns:
        x1, y1 = view_layout[r].getX(), view_layout[r].getY()
        for (get_reactants, get_reaction_edges, get_products, direction) in [
            (graph.getInNodes, graph.getOutEdges, graph.getOutNodes, 1),
            (graph.getOutNodes, graph.getInEdges, graph.getInNodes, -1)]:

            ubiquitous_reactants = [n for n in get_reactants(r) if ub_or_single(n, graph)
                                    and (not c_id or root[COMPARTMENT_ID][n] == c_id)]
            ub_reactants_len = len(ubiquitous_reactants)
            if not ub_reactants_len:
                continue
            if ub_reactants_len % 2 == 1:
                ub_reactants_len += 1

            specific_reactants = [n for n in get_reactants(r) if not ub_or_single(n, graph)]
            r_radius = get_reaction_r(r, root)
            size = sum(root[VIEW_SIZE][ub].getW() for ub in ubiquitous_reactants) / len(ubiquitous_reactants)
            edge_len = size * max(ub_reactants_len / 2, 3)
            if specific_reactants:
                specific_reactant_example = specific_reactants[0]
                x2, y2 = view_layout[specific_reactant_example].getX(), view_layout[specific_reactant_example].getY()
                species_size = view_size[specific_reactant_example].getW() / 2
                edge_len = (sqrt(pow(x1 - x2, 2) + pow(y2 - y1, 2)) - r_radius - species_size)
            else:
                specific_products = [n for n in get_products(r) if not ub_or_single(n, graph)]
                if specific_products:
                    specific_product_example = specific_products[0]
                    x3, y3 = view_layout[specific_product_example].getX(), view_layout[specific_product_example].getY()
                    x2, y2 = x1 - (x3 - x1), y1 - (y3 - y1)
                else:
                    x2, y2 = x1 + view_size[r].getW() + size * ub_reactants_len * direction, y1

            # beta is the max angle between the ubiquitous and the specific edges
            gap = 2 * min(100, max(60, ub_reactants_len * 20))
            beta0 = radians(gap / 2)
            beta = beta0
            d_beta = radians(gap / (ub_reactants_len - 1))

            # distance from reaction to the edge bent
            bent = min(size / 2, edge_len / 2)
            s0 = r_radius + bent
            s = s0
            ds = min(2 * (edge_len - bent - size / 2) / ub_reactants_len, size)
            # s += ds * ub_reactants_len / 2

            # angle between the horizontal line and the reaction-specific-species edge
            alpha = atan2(y2 - y1, x2 - x1)

            dc = 0
            towards_edge = -1
            for ub in ubiquitous_reactants:
                # it is the only edge as ubiquitous species are duplicated
                e = get_reaction_edges(ub).next()
                x0, y0 = x1 + s * cos(alpha), y1 + s * sin(alpha)
                view_layout[e] = [tlp.Coord(x0, y0)]

                gamma = alpha + beta
                # edge-after-bent length
                c = min(edge_len - s0 + dc + r_radius - size, 2 * size)

                x3, y3 = x0 + c * cos(gamma), y0 + c * sin(gamma)
                view_layout[ub] = tlp.Coord(x3, y3)
                if degrees(beta) * degrees(beta + towards_edge * d_beta) < 0:
                    beta = -beta0
                    towards_edge = 1
                    s = s0
                    dc = 0
                else:
                    beta += towards_edge * d_beta
                    s += ds / 3
                    dc += ds


def layout(graph):
    root = graph.getRoot()
    gr = graph.inducedSubGraph([n for n in graph.getNodes() if not ub_or_single(n, graph)])
    layout_components(gr)
    pack_cc(gr)
    graph.delAllSubGraphs(gr)
    layout_ub_sps(graph)
    pack_cc(graph)
    layout_outer_elements(graph)
    layout_ub_sps(graph)
    root[VIEW_LAYOUT].setAllEdgeValue([])