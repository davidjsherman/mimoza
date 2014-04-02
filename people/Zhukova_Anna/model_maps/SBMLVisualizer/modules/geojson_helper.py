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


def tulip2geojson(graph, geojson_file):
	root = graph.getRoot()
	type_ = root.getIntegerProperty(TYPE)
	layout = root.getLayoutProperty(VIEW_LAYOUT)
	size = root.getSizeProperty(VIEW_SIZE)
	shape = root[VIEW_SHAPE]
	color = root.getColorProperty(VIEW_COLOR)
	transport = root.getBooleanProperty(TRANSPORT)
	annotation = root.getStringProperty(ANNOTATION)

	(m_x, m_y), (M_x, M_y) = get_min_max(graph)
	x_scale = DIMENSION / (M_x - m_x)
	y_scale = DIMENSION / (M_y - m_y)

	features = []

	def get_coords(n):
		return scale(layout[n].getX(), layout[n].getY())

	def scale(x, y):
		return [(x - m_x) * x_scale, (M_y - y) * y_scale]

	onto = parse(get_chebi())

	i = 0
	for e in graph.getEdges():
		s, t = graph.source(e), graph.target(e)
		geom = geojson.MultiPoint([get_coords(s)] + [scale(it[0], it[1]) for it in layout[e]] + [get_coords(t)])
		ubiquitous = graph[UBIQUITOUS][s] or graph[UBIQUITOUS][t]
		props = {"color": triplet(color[e]), "width": size[e].getW() * x_scale, "height": size[e].getH() * y_scale,
		         "type": TYPE_EDGE, "stoichiometry": graph[STOICHIOMETRY][e], "ubiquitous": ubiquitous}
		f = geojson.Feature(geometry=geom, properties=props, id=i)
		i += 1
		features.append(f)

	for n in (n for n in graph.getNodes() if TYPE_BG == type_[n]):
		geom = geojson.Point(get_coords(n))
		props = {"color": triplet(color[n]), "width": size[n].getW() * x_scale, "height": size[n].getH() * y_scale,
		         "type": type_[n], 'shape': shape[n]}
		f = geojson.Feature(geometry=geom, properties=props, id=i)
		i += 1
		features.append(f)

	for n in (n for n in graph.getNodes() if type_[n] in [TYPE_REACTION, TYPE_SPECIES, TYPE_COMPARTMENT]):
		geom = geojson.Point(get_coords(n))
		props = {"id": root[ID][n], "name": root[NAME][n], "label": get_short_name(graph, n, onto),
		         "color": triplet(color[n]), "width": size[n].getW() * x_scale, "height": size[n].getH() * y_scale,
		         "type": type_[n]}
		if TYPE_REACTION == type_[n]:
			ins, outs = get_formula(graph, n)
			props.update(
				{"gene_association": get_gene_association_list(annotation[n]), "reversible": graph[REVERSIBLE][n],
				 'reactants': ins, 'products': outs, "transport": transport[n]})
		elif TYPE_COMPARTMENT == type_[n]:
			props['term'] = annotation[n]
		elif TYPE_SPECIES == type_[n]:
			n_id = root[ID][n]
			transported = False
			for rs in (root.getInOutNodes(m) for m in root.getNodes() if n_id == root[ID][m]):
				transported = next((r for r in rs if graph[TRANSPORT][r]), False) is not False
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