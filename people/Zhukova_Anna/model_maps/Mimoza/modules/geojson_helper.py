from sympy import to_cnf
from sympy.logic.boolalg import disjuncts, conjuncts
import geojson
from modules.resize import get_n_size, get_n_length, get_e_length
from sbml_generalization.utils.obo_ontology import get_chebi, parse
from modules.rename import get_short_name
from modules.graph_properties import *

__author__ = 'anna'

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x + y for x in _NUMERALS for y in _NUMERALS)}
LOWERCASE, UPPERCASE = 'x', 'X'
DIMENSION = 512
MARGIN = 3.8

ZOOM_OUT, ZOOM_IN, ZOOM_ANY = 1, 2, 3


def get_border_coord(xy_center, other_xy, r):
	(x_center, y_center) = xy_center
	(other_x, other_y) = other_xy
	diag = pow(pow(x_center - other_x, 2) + pow(y_center - other_y, 2), 0.5)
	transformation = lambda z, other_z: (r * (((other_z - z) / diag) if diag else 1)) + z
	return transformation(x_center, other_x), transformation(y_center, other_y)


def edge2feature(graph, e, id, scale, level_min, level_max, c_id2outs):
	root = graph.getRoot()
	layout = root.getLayoutProperty(VIEW_LAYOUT)
	transport = root.getBooleanProperty(TRANSPORT)
	size = root.getSizeProperty(VIEW_SIZE)

	s, t = graph.source(e), graph.target(e)
	xy = lambda n: (layout[n].getX(), layout[n].getY())
	s_x, s_y = get_border_coord(xy(s), (layout[e][0][0], layout[e][0][1]) if layout[e] else xy(t), size[s].getW() / 2)
	t_x, t_y = get_border_coord(xy(t), (layout[e][-1][0], layout[e][-1][1]) if layout[e] else xy(s), size[t].getW() / 2)
	geom = geojson.MultiPoint([scale(s_x, s_y)] + [scale(it[0], it[1]) for it in layout[e]] + [scale(t_x, t_y)])
	ubiquitous = graph[UBIQUITOUS][e]
	generalized = graph.isMetaNode(s) or graph.isMetaNode(t)
	is_transport = transport[s] or transport[t]
	props = {"size": get_e_length(graph, e),#"width": size[e].getW() * x_scale, "height": size[e].getH() * y_scale,
	         "type": TYPE_EDGE, "stoichiometry": graph[STOICHIOMETRY][e], "ubiquitous": ubiquitous,
	         "generalized": generalized, "transport": is_transport, "zoom_min": level_min,
	         "zoom_max": level_max}
	s_c_id = root[COMPARTMENT][s]
	t_c_id = root[COMPARTMENT][t]
	if s_c_id == t_c_id:
		props["c_id"] = s_c_id
		props["c_outs"] = ','.join(c_id2outs[s_c_id])
	else:
		props["c_outs"] = ','.join(set(c_id2outs[s_c_id]) | set(c_id2outs[t_c_id]))
	return geojson.Feature(geometry=geom, properties=props, id=id)


def node2feature(graph, n, id, scale, level_min, level_max, max_bg_level, onto, c_id2info, c_id2outs, scale_coefficient):
	root = graph.getRoot()
	type_ = root.getIntegerProperty(TYPE)
	layout = graph.getLayoutProperty(VIEW_LAYOUT)
	transport = root.getBooleanProperty(TRANSPORT)
	annotation = root.getStringProperty(ANNOTATION)

	geom = geojson.Point(scale(layout[n].getX(), layout[n].getY()))
	c_id = root[COMPARTMENT][n]
	size = get_n_size(graph, n).getW() * scale_coefficient if type_[n] in [TYPE_COMPARTMENT,
	                                                                     COMPARTMENT] else get_n_length(graph, n)
	props = {"size": size, "type": type_[n], "zoom_min": level_min, "zoom_max": level_max,
	         "c_id": c_id, "c_outs": ','.join(c_id2outs[c_id])}

	if type_[n] in TYPE_BG:
		return geojson.Feature(geometry=geom, properties=props, id=id)

	if type_[n] in TYPE_ENTITY:
		generalized = graph.isMetaNode(n)
		props.update({"id": root[ID][n], "name": root[NAME][n], "label": get_short_name(graph, n, onto),
		              "generalized": generalized})
		if TYPE_REACTION == type_[n]:
			ins, outs = get_formula(graph, n)
			props.update(
				{"gene_association": get_gene_association_list(annotation[n]), "reversible": root[REVERSIBLE][n],
				 'reactants': ins, 'products': outs, "transport": transport[n]})
			for m in graph.getInOutNodes(n):
				if c_id != root[COMPARTMENT][m]:
					del props["c_id"]
					break
		elif TYPE_COMPARTMENT == type_[n]:
			props['term'] = annotation[n]
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
			bg_props = {"size": size, "type": TYPE_2_BG_TYPE[type_[n]], "zoom_min": level_max + 1, "zoom_max": max_bg_level,
			            "c_id": c_id, "c_outs": ','.join(c_id2outs[c_id])}
			bg_feature = geojson.Feature(geometry=geom, properties=bg_props, id=id + 1)
		return geojson.Feature(geometry=geom, properties=props, id=id), bg_feature


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


def get_formula(graph, n):
	root = graph.getRoot()
	ins, outs = [], []
	stoich_formatter = lambda edge, node: "{0} * {1}".format(int(root[STOICHIOMETRY][edge]), root[NAME][node])
	for edge in graph.getInOutEdges(n):
		es = [edge]
		if TYPE_COMPARTMENT == root[TYPE][graph.source(edge)] or TYPE_COMPARTMENT == root[TYPE][graph.target(edge)]:
			es = root[VIEW_META_GRAPH][edge]
		for e in es:
			nd = root.source(e)
			if nd == n:
				nd = root.target(e)
				outs.append(stoich_formatter(e, nd))
			else:
				ins.append(stoich_formatter(e, nd))
	return '&'.join(ins), '&'.join(outs)


def rgb(rrggbb):
	return _HEXDEC[rrggbb[0:2]], _HEXDEC[rrggbb[2:4]], _HEXDEC[rrggbb[4:6]]


def triplet(c, lettercase=LOWERCASE):
	return '#' + format((c.getR() << 16 | c.getG() << 8 | c.getB()), '06' + lettercase)


def get_min_max(graph):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty(VIEW_LAYOUT)
	view_size = root.getSizeProperty(VIEW_SIZE)
	m, M = view_layout.getMin(graph), view_layout.getMax(graph)
	(m_x, m_y), (M_x, M_y) = (m.getX(), m.getY()), (M.getX(), M.getY())

	for n in graph.getNodes():
		x, y = view_layout[n].getX(), view_layout[n].getY()
		w, h = view_size[n].getW() / 2, view_size[n].getH() / 2
		if x - w < m_x:
			m_x = x - w
		if x + w > M_x:
			M_x = x + w
		if y - h < m_y:
			m_y = y - h
		if y + h > M_y:
			M_y = y + h

	w, h = M_x - m_x, M_y - m_y
	if w > h:
		m_y -= (w - h) / 2
		M_y += (w - h) / 2
	elif h > w:
		m_x -= (h - w) / 2
		M_x += (h - w) / 2

	return (m_x - MARGIN, m_y - MARGIN), (M_x + MARGIN, M_y + MARGIN)