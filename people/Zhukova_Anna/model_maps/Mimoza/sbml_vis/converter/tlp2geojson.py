from math import degrees, radians
from geojson.geometry import Geometry
from sympy import to_cnf, atan2, pi, tan
from sympy.logic.boolalg import disjuncts, conjuncts
import geojson

from sbml_vis.graph.rename import get_short_name
from sbml_vis.graph.graph_properties import *
from sbml_vis.graph.resize import get_n_length, get_n_size, get_e_length, get_e_size


__author__ = 'anna'

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x + y for x in _NUMERALS for y in _NUMERALS)}
LOWERCASE, UPPERCASE = 'x', 'X'


def get_border_coord((x, y), (other_x, other_y), (w, h), n_type):
	if n_type in [TYPE_REACTION, TYPE_COMPARTMENT]:
		edge_angle = degrees(atan2(other_y - y, other_x - x))
		diag_angle = degrees(atan2(h, w))
		abs_edge_angle = abs(edge_angle)
		if diag_angle < abs_edge_angle < 180 - diag_angle:
			y += h if edge_angle > 0 else -h
			if abs_edge_angle <= 90:
				return x + h / tan(radians(edge_angle)), y
			else:
				return x - h / tan(radians(edge_angle)), y
		else:
			x += w if abs_edge_angle <= 90 else -w
			if edge_angle > 0:
				return x, y + w * tan(radians(edge_angle))
			else:
				return x, y - w * tan(radians(edge_angle))
	else:
		diag = pow(pow(x - other_x, 2) + pow(y - other_y, 2), 0.5)
		transformation = lambda z, other_z: (w * (((other_z - z) / diag) if diag else 1)) + z
		return transformation(x, other_x), transformation(y, other_y)


def e2feature(graph, e, scale):
	root = graph.getRoot()
	layout = root[VIEW_LAYOUT]
	s, t = graph.source(e), graph.target(e)

	level_min, level_max = max(root[MIN_ZOOM][t], root[MIN_ZOOM][s]), min(root[MAX_ZOOM][t], root[MAX_ZOOM][s])

	xy = lambda n: (layout[n].getX(), layout[n].getY())
	wh = lambda n: (root[VIEW_SIZE][n].getW() / 2, root[VIEW_SIZE][n].getH() / 2)
	s_x, s_y = get_border_coord(xy(s), (layout[e][0][0], layout[e][0][1]) if layout[e] else xy(t), wh(s), root[TYPE][s])
	t_x, t_y = get_border_coord(xy(t), (layout[e][-1][0], layout[e][-1][1]) if layout[e] else xy(s), wh(t), root[TYPE][t])
	geom = geojson.MultiPoint([scale(s_x, s_y)] + [scale(it[0], it[1]) for it in layout[e]] + [scale(t_x, t_y)])
	ubiquitous = graph[UBIQUITOUS][e]
	generalized = graph.isMetaNode(s) or graph.isMetaNode(t)

	options = {t}
	r = s
	while not TYPE_REACTION == root[TYPE][r]:
		if root.isMetaNode(r):
			options |= {nd for nd in root[VIEW_META_GRAPH][r].getNodes()}
		r = options.pop()

	is_transport = root[TRANSPORT][r]
	props = {"size": get_e_size(root, e).getW(), "type": TYPE_EDGE, "stoichiometry": graph[STOICHIOMETRY][e],
	         "ubiquitous": ubiquitous, "generalized": generalized, "transport": is_transport,
	         "zoom_min": level_min, "zoom_max": level_max}
	if not is_transport:
		props["c_id"] = root[COMPARTMENT][r]
	return geojson.Feature(geometry=geom, properties=props)


def n2feature(graph, n, scale, max_bg_level, onto, c_id2info, scale_coefficient):
	root = graph.getRoot()
	type_ = root.getIntegerProperty(TYPE)
	layout = graph.getLayoutProperty(VIEW_LAYOUT)
	transport = root.getBooleanProperty(TRANSPORT)
	annotation = root.getStringProperty(ANNOTATION)

	geom = geojson.Point(scale(layout[n].getX(), layout[n].getY()))
	c_id = root[COMPARTMENT][n]
	size = root[VIEW_SIZE][n].getW() * scale_coefficient
	w, h = root[VIEW_SIZE][n].getW() * scale_coefficient, root[VIEW_SIZE][n].getH() * scale_coefficient
	level_min, level_max = root[MIN_ZOOM][n], root[MAX_ZOOM][n]

	props = {"w": w, "h": h, "size": size, "type": type_[n], "zoom_min": level_min, "zoom_max": level_max,
	         "c_id": c_id}

	if type_[n] in TYPE_BG:
		return geojson.Feature(geometry=geom, properties=props)

	if type_[n] in TYPE_ENTITY:
		generalized = graph.isMetaNode(n)
		props.update({"id": root[ID][n], "name": root[NAME][n], "label": get_short_name(graph, n, onto),
		              "generalized": generalized})
		if TYPE_REACTION == type_[n]:
			ins, outs = get_formula(graph, n)
			props.update(
				{"gene_association": get_gene_association_list(annotation[n]), "reversible": root[REVERSIBLE][n],
				 'reactants': ins, 'products': outs, "transport": transport[n]})
			if transport[n]:
				del props["c_id"]
		elif TYPE_COMPARTMENT == type_[n]:
			props['term'] = annotation[n]
			props['transport'] = True
		elif TYPE_SPECIES == type_[n]:
			n_id = root[ID][n]
			transported = False
			for rs in (root.getInOutNodes(m) for m in root.getNodes() if n_id == root[ID][m]):
				transported = next((r for r in rs if transport[r]), False) is not False
				if transported:
					break
			# Get compartment name from c_id2info: c_id -> (name, go, (level, out_c_id))
			comp_name = c_id2info[c_id][0]
			props.update({"term": annotation[n], "transport": transported, "ubiquitous": root[UBIQUITOUS][n],
			              "compartment": comp_name})

		bg_feature = None
		if generalized:
			bg_props = {"id": root[ID][n], "w": w, "h": h, "size": size, "type": TYPE_2_BG_TYPE[type_[n]],
			            "zoom_min": level_max + 1, "zoom_max": max_bg_level, "transport": props["transport"]}
			if "c_id" in props:
				bg_props["c_id"] = c_id
			bg_feature = geojson.Feature(geometry=geom, properties=bg_props)
		return geojson.Feature(geometry=geom, properties=props), bg_feature


def get_gene_association_list(ga):
	gene_association = ga.replace('and', '&').replace('or', '|').replace('OR', '|')
	if not gene_association:
		return ''
	try:
		res = to_cnf(gene_association, False)
		gene_association = '&'.join(['|'.join([str(it) for it in disjuncts(cjs)]) for cjs in conjuncts(res)])
		return gene_association
	except:
		return ''


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


def get_formula(graph, r):
	root = graph.getRoot()
	ins, outs = set(), set()
	stoich_formatter = lambda edge, node: "{0} * {1}".format(int(root[STOICHIOMETRY][edge]), root[NAME][node])
	for s_or_c in graph.getInOutNodes(r):
		for s in get_reaction_participants_inside_compartment(s_or_c, r, root):
			e = root.existEdge(s, r, False)
			if root.isElement(e):
				(ins if s == root.source(e) else outs).add(stoich_formatter(e, s))
	return '&'.join(sorted(ins)), '&'.join(sorted(outs))


def rgb(rrggbb):
	return _HEXDEC[rrggbb[0:2]], _HEXDEC[rrggbb[2:4]], _HEXDEC[rrggbb[4:6]]


def triplet(c, lettercase=LOWERCASE):
	return '#' + format((c.getR() << 16 | c.getG() << 8 | c.getB()), '06' + lettercase)
