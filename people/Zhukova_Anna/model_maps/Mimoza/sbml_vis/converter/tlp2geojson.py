from math import degrees

from sympy import to_cnf, atan2
from sympy.logic.boolalg import disjuncts, conjuncts
import geojson

from sbml_vis.graph.color.colorer import get_edge_color, get_reaction_color, get_compartment_color, get_species_color, \
    get_bg_color
from sbml_vis.graph.graph_properties import *
from sbml_vis.graph.resize import get_e_size

__author__ = 'anna'

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x + y for x in _NUMERALS for y in _NUMERALS)}
LOWERCASE, UPPERCASE = 'x', 'X'


def get_border_coord((x, y), (other_x, other_y), (w, h), n_type):
    if n_type == TYPE_REACTION:
        edge_angle = degrees(atan2(other_y - y, other_x - x)) if other_y != y or other_x != x else 0
        diag_angle = degrees(atan2(h, w))
        abs_edge_angle = abs(edge_angle)
        if diag_angle < abs_edge_angle < 180 - diag_angle:
            y += h if edge_angle > 0 else -h
        else:
            x += w if abs_edge_angle <= 90 else -w
        return x, y
    elif n_type == TYPE_COMPARTMENT:
        c_bottom_x, c_bottom_y, c_top_x, c_top_y = x - w, y - h, x + w, y + h
        inside_y = c_bottom_y <= other_y <= c_top_y
        inside_x = c_bottom_x <= other_x <= c_top_x

        if inside_x:
            return other_x, c_bottom_y if abs(other_y - c_bottom_y) < abs(other_y - c_top_y) else c_top_y
        elif inside_y:
            return c_bottom_x if abs(other_x - c_bottom_x) < abs(other_x - c_top_x) else c_top_x, other_y
        else:
            return max(c_bottom_x, min(other_x, c_top_x)), max(c_bottom_y, min(other_y, c_top_y))
    else:
        diag = pow(pow(x - other_x, 2) + pow(y - other_y, 2), 0.5)
        transformation = lambda z, other_z: (w * (((other_z - z) / diag) if diag else 1)) + z
        return transformation(x, other_x), transformation(y, other_y)


def e2feature(graph, e, e_id, transport, inner):
    root = graph.getRoot()
    layout = root[VIEW_LAYOUT]
    s, t = graph.source(e), graph.target(e)

    xy = lambda n: (layout[n].getX(), layout[n].getY())
    wh = lambda n: (root[VIEW_SIZE][n].getW() / 2, root[VIEW_SIZE][n].getH() / 2)
    s_x, s_y = get_border_coord(xy(s), (layout[e][0][0], layout[e][0][1]) if layout[e] else xy(t), wh(s), root[TYPE][s])
    t_x, t_y = get_border_coord(xy(t), (layout[e][-1][0], layout[e][-1][1]) if layout[e] else xy(s), wh(t),
                                root[TYPE][t])
    geom = geojson.MultiPoint([[s_x, s_y]] + [[it[0], it[1]] for it in layout[e]] + [[t_x, t_y]])
    generalized = graph.isMetaNode(s) or graph.isMetaNode(t)

    real_e = e
    while root.isMetaEdge(real_e):
        real_e = next((ee for ee in root[VIEW_META_GRAPH][real_e] if not root[UBIQUITOUS][ee]),
                      next(iter(root[VIEW_META_GRAPH][real_e])))
    ubiquitous = root[UBIQUITOUS][real_e]
    color = triplet(root[VIEW_COLOR][e])
    props = {WIDTH: get_e_size(root, e).getW() / 2, TYPE: TYPE_EDGE, STOICHIOMETRY: graph[STOICHIOMETRY][e],
             COLOR: get_edge_color(ubiquitous, generalized, transport, color)}
    if not transport:
        props[COMPARTMENT_ID] = root[COMPARTMENT_ID][s]
    else:
        # let's not store unneeded False
        props[TRANSPORT] = True
        if inner:
            props[INNER] = True
    if ubiquitous:
        props[UBIQUITOUS] = True
    return geojson.Feature(id=e_id, geometry=geom, properties=props)


def n2feature(graph, n, n_id, c_id2info, r2rs_ps, transport, inner):
    root = graph.getRoot()

    x, y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
    geom = geojson.Point([x, y])
    c_id = root[COMPARTMENT_ID][n]
    w, h = root[VIEW_SIZE][n].getW() / 2, root[VIEW_SIZE][n].getH() / 2
    node_type = root[TYPE][n]
    generalized = graph.isMetaNode(n)
    props = {WIDTH: w, TYPE: node_type, COMPARTMENT_ID: c_id, ID: root[ID][n],
             NAME: root[NAME][n]}  # LABEL: get_short_name(graph, n, onto)}
    color = triplet(root[VIEW_COLOR][n])
    if TYPE_REACTION == node_type:
        # ins, outs = get_formula(graph, n, r2rs_ps)
        formula = get_formula(graph, n, r2rs_ps, root[REVERSIBLE][n])
        genes = get_gene_association_list(root[TERM][n])
        if not next((m for m in root.getInOutNodes(n) if TYPE_SPECIES == root[TYPE][m] and not root[UBIQUITOUS][m]), False):
            props[UBIQUITOUS] = True
        if genes:
            props[TERM] = genes
        # if ins:
        # props[REACTANTS] = ins
        # if outs:
        # props[PRODUCTS] = outs
        if formula:
            props[FORMULA] = formula
        props[COLOR] = get_reaction_color(generalized, transport, color)
        if transport:
            del props[COMPARTMENT_ID]
            # let's not store unneeded False
            props[TRANSPORT] = True
            if inner:
                props[INNER] = True
            # if root[REVERSIBLE][n]:
            # 	props[REVERSIBLE] = True
    elif TYPE_COMPARTMENT == node_type:
        term = root[TERM][n]
        if term:
            term = term.upper()
            props[T] = term
            props[TERM] = "<a href=\'http://www.ebi.ac.uk/QuickGO/GTerm?id=%s\' target=\'_blank\'>%s</a>" % (term, term)

        props.update({HEIGHT: h, COLOR: get_compartment_color()})
    elif TYPE_SPECIES == node_type:
        ubiquitous = root[UBIQUITOUS][n]
        if ubiquitous:
            # let's not store unneeded False
            props[UBIQUITOUS] = True
        if transport and not inner:
            props[TRANSPORT] = True
        # even if a species participates in inner transport,
        # we need to always show it inside its compartment
        # if inner and ubiquitous:
        # props[INNER] = True
        # Get compartment name from c_id2info: c_id -> (name, go, (level, out_c_id))
        comp_name = c_id2info[c_id][0]
        term = root[TERM][n]
        if term:
            term = term.upper()
            if term.find("UNKNOWN") == -1:
                props[T] = term
                props[
                    TERM] = "<a href=\'http://www.ebi.ac.uk/chebi/searchId.do?chebiId=%s\' target=\'_blank\'>%s</a>" % (
                    term, term)
        props.update({COMPARTMENT_NAME: comp_name, COLOR: get_species_color(ubiquitous, generalized, color)})

    bg_feature = None
    # if generalized:
    if generalized:
        node_type = TYPE_2_BG_TYPE[node_type]
        bg_props = {ID: root[ID][n], WIDTH: w, TYPE: node_type, COLOR: get_bg_color(node_type, transport, color)}
        if TRANSPORT in props:
            # let's not store unneeded False
            bg_props[TRANSPORT] = True
            if inner and TYPE_BG_REACTION == node_type:
                bg_props[INNER] = True
        if COMPARTMENT_ID in props:
            bg_props[COMPARTMENT_ID] = root[COMPARTMENT_ID][n]
        if TYPE_BG_COMPARTMENT == node_type:
            bg_props[HEIGHT] = h
            bg_props[COMPARTMENT_ID] = root[ID][n]
        bg_feature = geojson.Feature(id="%s_bg" % n_id, geometry=geom, properties=bg_props)
    return geojson.Feature(id=n_id, geometry=geojson.Point([x, y]), properties=props), bg_feature


def _get_gene_association_list(ga):
    gene_association = ga.replace('and', '&').replace('or', '|').replace('OR', '|')
    if not gene_association:
        return []
    try:
        res = to_cnf(gene_association, False)
        gene_association = [[str(it) for it in disjuncts(cjs)] for cjs in conjuncts(res)]
        return gene_association
    except:
        return []


def get_gene_association_list(ga):
    gene_association = ga.replace('and', '&').replace('or', '|').replace('OR', '|')
    if not gene_association:
        return ""
    try:
        res = to_cnf(gene_association, False)
        gene_association = [[str(it) for it in disjuncts(cjs)] for cjs in conjuncts(res)]
        result = '''<table border="0" width="100%%">
						<tr class="centre"><th colspan="%d" class="centre">Gene association</th></tr>
						<tr>''' % (2 * len(gene_association) - 1)
        first = True
        for genes in gene_association:
            if first:
                first = False
            else:
                result += '<td class="centre"><i>and</i></td>'
            result += '<td><table border="0">'
            if len(genes) > 1:
                result += "<tr><td class='centre'><i>(or)</i></td></tr>"
            for gene in genes:
                result += "<tr><td class='main'><a href=\'http://www.ncbi.nlm.nih.gov/gene/?term=%s[sym]\' target=\'_blank\'>%s</a></td></tr>" % (
                    gene, gene)
            result += '</table></td>'
        result += '</tr></table>'
        return result
    except:
        return ""


def get_reaction_participants_inside_compartment(n, r, root):
    if TYPE_COMPARTMENT == root[TYPE][n]:
        result = set()
        for m in root[VIEW_META_GRAPH][n].getNodes():
            result |= get_reaction_participants_inside_compartment(m, r, root)
        return result
    elif not root.isMetaNode(n) or root.isMetaNode(r):
        return {n}
    else:
        return {s for s in root[VIEW_META_GRAPH][n].getNodes()}


def _get_formula(graph, r, r2rs_ps):
    root = graph.getRoot()
    name_prop = NAME
    formatter = lambda (st, n), prop: [root[prop if root[prop][n] else NAME][n], int(st)]
    if graph.isMetaNode(r):
        r = root[VIEW_META_GRAPH][r].getOneNode()
        name_prop = ANCESTOR_NAME
    rs, ps = r2rs_ps[r]
    return sorted(formatter(it, name_prop) for it in rs), sorted(formatter(it, name_prop) for it in ps)


def get_formula(graph, r, r2rs_ps, reversible):
    root = graph.getRoot()
    name_prop = NAME
    formatter = lambda (st, n), prop: [root[prop if root[prop][n] else NAME][n], int(st)]
    if graph.isMetaNode(r):
        r = root[VIEW_META_GRAPH][r].getOneNode()
        name_prop = ANCESTOR_NAME
    rs, ps = r2rs_ps[r]
    rs, ps = sorted(formatter(it, name_prop) for it in rs), sorted(formatter(it, name_prop) for it in ps)

    res = '<table border="0" width="100%"><tr><td width="45%"><table border="0">'
    if rs:
        for [r, st] in rs:
            res += '<tr><td class="main">%d&nbsp;</td><td>%s</td></tr>' % (st, r)
    res += '</table></td>'
    res += '<th class="centre" width="10%%">%s</th>' % "&#8596;" if reversible else "&#65515;"
    res += '<td  width="45%"><table border="0">'
    if ps:
        for [p, st] in ps:
            res += '<tr><td class="main">%d&nbsp;</td><td>%s</td></tr>' % (st, p)
    res += '</table></td></tr></table>'
    return res


def rgb(rrggbb):
    return _HEXDEC[rrggbb[0:2]], _HEXDEC[rrggbb[2:4]], _HEXDEC[rrggbb[4:6]]


def triplet(c, lettercase=LOWERCASE):
    return '#' + format((c.getR() << 16 | c.getG() << 8 | c.getB()), '06' + lettercase)
