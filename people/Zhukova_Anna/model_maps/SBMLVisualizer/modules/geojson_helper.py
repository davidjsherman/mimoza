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
	ga = root.getStringProperty(GENE_ASSOCIATION)
	type_ = root.getStringProperty(TYPE)
	layout = root.getLayoutProperty(VIEW_LAYOUT)
	size = root.getSizeProperty(VIEW_SIZE)
	shape = root[VIEW_SHAPE]
	color = root.getColorProperty(VIEW_COLOR)
	b_color = root.getColorProperty(VIEW_BORDER_COLOR)
	term_id = root.getStringProperty(TERM_ID)

	(m_x, m_y), (M_x, M_y) = get_min_max(graph)
	x_scale = DIMENSION / (M_x - m_x)
	y_scale = DIMENSION / (M_y - m_y)

	features = []

	def get_coords(n):
		return scale(layout[n].getX(), layout[n].getY())

	def scale(x, y):
		return [(x - m_x) * x_scale, (M_y - y) * y_scale]

	onto = parse(get_chebi())

	for e in graph.getEdges():
		s, t = graph.source(e), graph.target(e)
		geom = geojson.MultiPoint([get_coords(s)] + [scale(it[0], it[1]) for it in layout[e]] + [get_coords(t)])
		props = {"color": triplet(color[e]), "width": size[e].getW() * x_scale, "height": size[e].getH() * y_scale,
		         "type": 'edge', "stoichiometry": graph[STOICHIOMETRY][e]}
		f = geojson.Feature(geometry=geom, properties=props)
		features.append(f)

	for n in (n for n in graph.getNodes() if TYPE_BG == type_[n]):
		geom = geojson.Point(get_coords(n))
		props = {"color": triplet(color[n]), "width": size[n].getW() * x_scale, "height": size[n].getH() * y_scale,
		         "type": type_[n], 'shape': shape[n]}
		f = geojson.Feature(geometry=geom, properties=props)
		features.append(f)

	for n in (n for n in graph.getNodes() if type_[n] in [TYPE_REACTION, TYPE_SPECIES, TYPE_COMPARTMENT]):
		geom = geojson.Point(get_coords(n))
		props = {"id": root[ID][n], "name": root[NAME][n], "label": get_short_name(graph, n, onto),
		         "color": triplet(color[n]), "border": triplet(b_color[n]),
		         "width": size[n].getW() * x_scale, "height": size[n].getH() * y_scale,
		         "type": type_[n], 'term': term_id[n]}
		if 'reaction' == type_[n]:
			ins, outs = get_formula(graph, n)
			props.update({"gene_association": get_gene_association_list(ga[n]), "reversible": graph[REVERSIBLE][n],
			              'reactants': ins, 'products': outs})
		f = geojson.Feature(geometry=geom, properties=props)
		features.append(f)
		# if graph.isMetaNode(n):
		# 	for n in graph['viewMetaGraph'][n].getNodes():
		# 		geom = geojson.Point(get_coords(n))
		# 		props = {"color": triplet(color[n]), "width": size[n].getW() * x_scale, "height": size[n].getH() * y_scale,
		# 		         "type": 'background', 'shape': shape[n]}
		# 		f = geojson.Feature(geometry=geom, properties=props)
		# 		features.append(f)

	fc = geojson.FeatureCollection(features, geometry=geojson.Polygon(
		[[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]]))
	with open(geojson_file, 'w+') as f:
		f.write("var gjsn_{1} = {0}\n".format(geojson.dumps(fc).replace('"id": null', ''),
		                                      graph.getName().replace(' ', '_').lower().strip()))


def get_gene_association_list(ga):
	gann = ga.replace('and', '&').replace('or', '|').replace('OR', '|')
	if not gann:
		return ''
	try:
		res = to_cnf(gann, False)
		gann = '&'.join(['|'.join([str(it) for it in disjuncts(cjs)]) for cjs in conjuncts(res)])
		return gann
	except:
		return ''


def get_formula(graph, n):
	root = graph.getRoot()
	ins, outs = [], []
	stoich_formatter = lambda e, nd: "{0} * {1}".format(int(root[STOICHIOMETRY][e]), root[NAME][nd])
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


def rgb(triplet):
	return (_HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]])


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