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
	if n_type in [TYPE_REACTION, TYPE_COMPARTMENT]:
		# todo: why could these coordinates be the same?
		edge_angle = degrees(atan2(other_y - y, other_x - x)) if other_y != y or other_x != x else 0
		diag_angle = degrees(atan2(h, w))
		abs_edge_angle = abs(edge_angle)
		if diag_angle < abs_edge_angle < 180 - diag_angle:
			y += h if edge_angle > 0 else -h
		else:
			x += w if abs_edge_angle <= 90 else -w
		return x, y
	else:
		diag = pow(pow(x - other_x, 2) + pow(y - other_y, 2), 0.5)
		transformation = lambda z, other_z: (w * (((other_z - z) / diag) if diag else 1)) + z
		return transformation(x, other_x), transformation(y, other_y)


def e2feature(graph, e, scale, e_id):
	root = graph.getRoot()
	layout = root[VIEW_LAYOUT]
	s, t = graph.source(e), graph.target(e)

	level_min, level_max = max(root[MIN_ZOOM][t], root[MIN_ZOOM][s]), min(root[MAX_ZOOM][t], root[MAX_ZOOM][s])

	xy = lambda n: (layout[n].getX(), layout[n].getY())
	wh = lambda n: (root[VIEW_SIZE][n].getW() / 2, root[VIEW_SIZE][n].getH() / 2)
	s_x, s_y = get_border_coord(xy(s), (layout[e][0][0], layout[e][0][1]) if layout[e] else xy(t), wh(s), root[TYPE][s])
	t_x, t_y = get_border_coord(xy(t), (layout[e][-1][0], layout[e][-1][1]) if layout[e] else xy(s), wh(t),
	                            root[TYPE][t])
	geom = geojson.MultiPoint([scale(s_x, s_y)] + [scale(it[0], it[1]) for it in layout[e]] + [scale(t_x, t_y)])
	generalized = graph.isMetaNode(s) or graph.isMetaNode(t)

	options = {t}
	r = s
	while not TYPE_REACTION == root[TYPE][r]:
		if root.isMetaNode(r):
			options |= {nd for nd in root[VIEW_META_GRAPH][r].getNodes()}
		r = options.pop()

	transport = root[TRANSPORT][r]
	ubiquitous = root[UBIQUITOUS][e]
	props = {WIDTH: get_e_size(root, e).getW() / 4, TYPE: TYPE_EDGE, STOICHIOMETRY: graph[STOICHIOMETRY][e],
	         MIN_ZOOM: level_min, MAX_ZOOM: level_max, COLOR: get_edge_color(ubiquitous, generalized, transport)}
	if not transport:
		props["c_id"] = root[COMPARTMENT_ID][r]
	else:
	# let's not store unneeded False
		props[TRANSPORT] = True
	if ubiquitous:
		props[UBIQUITOUS] = True
	return geojson.Feature(geometry=geom, properties=props) #, id=e_id)


def n2feature(graph, n, scale, max_bg_level, c_id2info, scale_coefficient, n_id):
	root = graph.getRoot()

	geom = geojson.Point(scale(root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()))
	c_id = root[COMPARTMENT_ID][n]
	w, h = root[VIEW_SIZE][n].getW() * scale_coefficient / 2, root[VIEW_SIZE][n].getH() * scale_coefficient / 2
	node_type = root[TYPE][n]
	generalized = graph.isMetaNode(n)
	props = {WIDTH: w, TYPE: node_type, MIN_ZOOM: root[MIN_ZOOM][n], MAX_ZOOM: root[MAX_ZOOM][n],
	         COMPARTMENT_ID: c_id, ID: root[ID][n], NAME: root[NAME][n]} #LABEL: get_short_name(graph, n, onto)}
	if TYPE_REACTION == node_type:
		ins, outs = get_formula(graph, n)
		transport = root[TRANSPORT][n]
		genes = get_gene_association_list(root[TERM][n])
		if genes:
			props[TERM] = genes
		if ins:
			props[REACTANTS] = ins
		if outs:
			props[PRODUCTS] = outs
		props[COLOR] = get_reaction_color(generalized, transport)
		if transport:
			del props[COMPARTMENT_ID]
			# let's not store unneeded False
			props[TRANSPORT] = True
		if root[REVERSIBLE][n]:
			props[REVERSIBLE] = True
	elif TYPE_COMPARTMENT == node_type:
		term = root[TERM][n]
		if term:
			props[TERM] = term
		props.update({HEIGHT: h, TRANSPORT: True, COLOR: get_compartment_color()})
	elif TYPE_SPECIES == node_type:
		ubiquitous = root[UBIQUITOUS][n]
		if ubiquitous:
			# let's not store unneeded False
			props[UBIQUITOUS] = True
		s_id = root[ID][n]
		for rs in (root.getInOutNodes(m) for m in root.getNodes() if s_id == root[ID][m]):
			if next((r for r in rs if root[TRANSPORT][r]), False) is not False:
				props[TRANSPORT] = True
				break
		# Get compartment name from c_id2info: c_id -> (name, go, (level, out_c_id))
		comp_name = c_id2info[c_id][0]
		term = root[TERM][n]
		if term:
			props[TERM] = term
		props.update({COMPARTMENT_NAME: comp_name, COLOR: get_species_color(ubiquitous, generalized)})

	bg_feature = None
	if generalized:
		node_type = TYPE_2_BG_TYPE[node_type]
		transport = TRANSPORT in props
		bg_props = {ID: root[ID][n], WIDTH: w, TYPE: node_type,
		            MIN_ZOOM: root[MAX_ZOOM][n] + 1, MAX_ZOOM: max_bg_level, COLOR: get_bg_color(node_type, transport)}
		if transport:
			# let's not store unneeded False
			bg_props[TRANSPORT] = True
		if COMPARTMENT_ID in props:
			bg_props[COMPARTMENT_ID] = c_id
		if TYPE_BG_COMPARTMENT == node_type:
			bg_props[HEIGHT] = h
		bg_feature = geojson.Feature(geometry=geom, properties=bg_props)
	return geojson.Feature(geometry=geom, properties=props), bg_feature #, id=n_id)


def get_gene_association_list(ga):
	gene_association = ga.replace('and', '&').replace('or', '|').replace('OR', '|')
	if not gene_association:
		return []
	try:
		res = to_cnf(gene_association, False)
		gene_association = [[str(it) for it in disjuncts(cjs)] for cjs in conjuncts(res)]
		return gene_association
	except:
		return []


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
	stoich_formatter = lambda edge, node: (root[NAME][node], int(root[STOICHIOMETRY][edge]))
	for s_or_c in graph.getInOutNodes(r):
		for s in get_reaction_participants_inside_compartment(s_or_c, r, root):
			e = root.existEdge(s, r, False)
			if root.isElement(e):
				(ins if s == root.source(e) else outs).add(stoich_formatter(e, s))
	return [[name, st] for (name, st) in sorted(ins)], [[name, st] for (name, st) in sorted(outs)]


def rgb(rrggbb):
	return _HEXDEC[rrggbb[0:2]], _HEXDEC[rrggbb[2:4]], _HEXDEC[rrggbb[4:6]]


def triplet(c, lettercase=LOWERCASE):
	return '#' + format((c.getR() << 16 | c.getG() << 8 | c.getB()), '06' + lettercase)
