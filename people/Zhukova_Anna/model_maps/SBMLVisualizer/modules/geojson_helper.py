from sympy import to_cnf
from sympy.logic.boolalg import disjuncts, conjuncts
import geojson
from sbml_generalization.utils.obo_ontology import get_chebi, parse
from modules.rename import get_short_name
from modules.graph_tools import *

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
	transformation = lambda z, other_z: r * (other_z - z) / diag + z
	return transformation(x_center, other_x), transformation(y_center, other_y)


def tulip2geojson(graph_full, graph, geojson_file):
	root = graph.getRoot()
	type_ = root.getIntegerProperty(TYPE)
	layout = root.getLayoutProperty(VIEW_LAYOUT)
	size = root.getSizeProperty(VIEW_SIZE)
	transport = root.getBooleanProperty(TRANSPORT)
	annotation = root.getStringProperty(ANNOTATION)

	(m_x, m_y), (M_x, M_y) = get_min_max(graph_full)
	x_scale = DIMENSION / (M_x - m_x)
	y_scale = DIMENSION / (M_y - m_y)

	features = []

	def get_coords(n):
		return scale(layout[n].getX(), layout[n].getY())

	def scale(x, y):
		return [(x - m_x) * x_scale, (M_y - y) * y_scale]

	onto = parse(get_chebi())

	i = 0
	for (g1, g2, add_common, level) in [(graph, graph_full, True, ZOOM_OUT), (graph_full, graph, False, ZOOM_IN)]:
		for e in g1.getEdges():
			s, t = g1.source(e), g1.target(e)
			zoom = level
			if g2.isElement(s) and g2.isElement(t) and g2.existEdge(s, t):
				if not add_common:
					continue
				else:
					zoom = ZOOM_ANY
			xy = lambda n: (layout[n].getX(), layout[n].getY())
			s_x, s_y = get_border_coord(xy(s), (layout[e][0][0], layout[e][0][1]) if layout[e] else xy(t), size[s].getW() / 2)
			t_x, t_y = get_border_coord(xy(t), (layout[e][-1][0], layout[e][-1][1]) if layout[e] else xy(s), size[t].getW() / 2)
			geom = geojson.MultiPoint([scale(s_x, s_y)] + [scale(it[0], it[1]) for it in layout[e]] + [scale(t_x, t_y)])
			# geom = geojson.MultiPoint([get_coords(s)] + [scale(it[0], it[1]) for it in layout[e]] + [get_coords(t)])
			ubiquitous = g1[UBIQUITOUS][s] or g1[UBIQUITOUS][t]
			generalized = g1.isMetaNode(s) or g1.isMetaNode(t)
			is_transport = transport[s] or transport[t]
			props = {"width": size[e].getW() * x_scale, "height": size[e].getH() * y_scale,
			         "type": TYPE_EDGE, "stoichiometry": g1[STOICHIOMETRY][e], "ubiquitous": ubiquitous,
			         "generalized": generalized, "transport": is_transport, "zoom": zoom}
			f = geojson.Feature(geometry=geom, properties=props, id=i)
			i += 1
			features.append(f)

		for n in (n for n in g1.getNodes() if type_[n] in TYPE_BG):
			geom = geojson.Point(get_coords(n))
			zoom = level
			if g2.isElement(n):
				if not add_common:
					continue
				else:
					zoom = ZOOM_ANY
			props = {"width": size[n].getW() * x_scale, "height": size[n].getH() * y_scale,
			         "type": type_[n], "transport": transport[n], "zoom": zoom}
			f = geojson.Feature(geometry=geom, properties=props, id=i)
			i += 1
			features.append(f)

		for n in (n for n in g1.getNodes() if type_[n] in TYPE_ENTITY):
			geom = geojson.Point(get_coords(n))
			generalized = g1.isMetaNode(n)
			zoom = level
			if g2.isElement(n):
				if not add_common:
					continue
				else:
					zoom = ZOOM_ANY
			props = {"id": root[ID][n], "name": root[NAME][n], "label": get_short_name(g1, n, onto),
			         "width": size[n].getW() * x_scale, "height": size[n].getH() * y_scale,
			         "type": type_[n], "generalized": generalized, "zoom": zoom}
			if TYPE_REACTION == type_[n]:
				ins, outs = get_formula(g1, n)
				props.update(
					{"gene_association": get_gene_association_list(annotation[n]), "reversible": g1[REVERSIBLE][n],
					 'reactants': ins, 'products': outs, "transport": transport[n]})
			elif TYPE_COMPARTMENT == type_[n]:
				props['term'] = annotation[n]
			elif TYPE_SPECIES == type_[n]:
				n_id = root[ID][n]
				transported = False
				for rs in (root.getInOutNodes(m) for m in root.getNodes() if n_id == root[ID][m]):
					transported = next((r for r in rs if g1[TRANSPORT][r]), False) is not False
					if transported:
						break
				props.update({"term": annotation[n], "transport": transported, "ubiquitous": root[UBIQUITOUS][n]})
			f = geojson.Feature(geometry=geom, properties=props, id=i)
			i += 1
			features.append(f)

	fc = geojson.FeatureCollection(features, geometry=geojson.Polygon(
		[[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]]))
	with open(geojson_file, 'w+') as f:
		f.write("var gjsn_{1} = {0}\n".format(geojson.dumps(fc).replace('"id": null', ''),
		                                      graph.getName().replace(' ', '_').lower().strip()))


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
	lo = graph.getRoot().getLayoutProperty(VIEW_LAYOUT)
	# (m_x, m_y), (M_x, M_y) = get_corners(graph)
	m, M = lo.getMin(graph), lo.getMax(graph)
	(m_x, m_y), (M_x, M_y) = (m.getX(), m.getY()), (M.getX(), M.getY())

	w, h = M_x - m_x, M_y - m_y
	if w > h:
		m_y -= (w - h) / 2
		M_y += (w - h) / 2
	elif h > w:
		m_x -= (h - w) / 2
		M_x += (h - w) / 2

	return (m_x - MARGIN, m_y - MARGIN), (M_x + MARGIN, M_y + MARGIN)