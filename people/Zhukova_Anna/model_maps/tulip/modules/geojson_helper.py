from sympy import to_cnf
from sympy.logic.boolalg import disjuncts, conjuncts
import geojson
from sbml_generalization.utils.obo_ontology import get_chebi, parse
from modules.rename import get_short_name

__author__ = 'anna'

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x + y for x in _NUMERALS for y in _NUMERALS)}
LOWERCASE, UPPERCASE = 'x', 'X'
DIMENSION = 512
MARGIN = 3.8


def tulip2geojson(graph, geojson_file):
	ga = graph.getStringProperty("geneAssociation")
	type_ = graph.getStringProperty("type")
	layout = graph.getLayoutProperty("viewLayout")
	size = graph.getSizeProperty("viewSize")
	color = graph.getColorProperty("viewColor")
	b_color = graph.getColorProperty("viewBorderColor")
	chebi = graph.getStringProperty("chebi_id")

	(m_x, m_y), (M_x, M_y) = get_min_max(graph)
	x_scale = DIMENSION / (M_x - m_x)
	y_scale = DIMENSION / (M_y - m_y)

	features = []

	def get_coords(n):
		return [(layout[n].getX() - m_x) * x_scale, (M_y - layout[n].getY()) * y_scale]

	onto = parse(get_chebi())

	for e in graph.getEdges():
		s, t = graph.source(e), graph.target(e)
		geom = geojson.MultiPoint([get_coords(s), get_coords(t)])
		props = {"color": triplet(color[e]), "width": size[e].getW() * x_scale, "height": size[e].getH() * y_scale,
		         "type": 'edge', "stoichiometry": graph['stoichiometry'][e]}
		f = geojson.Feature(geometry=geom, properties=props)
		features.append(f)

	for n in graph.getNodes():
		if not type_[n] in ['reaction', 'species', 'compartment', 'background']:
			continue
		geom = geojson.Point(get_coords(n))
		props = {"id": graph['id'][n], "name": get_short_name(graph, n, onto), "color": triplet(color[n]),
		         "bcolor": triplet(b_color[n]), "width": size[n].getW() * x_scale, "height": size[n].getH() * y_scale,
		         "type": type_[n]}
		if 'reaction' == type_[n]:
			ins, outs = get_formula(graph, n, onto)
			props.update({"gene_association": get_gene_association_list(ga[n]), "reversible": graph['reversible'][n],
			              'reactants': ins, 'products': outs})
		elif 'species' == type_[n]:
			props["chebi"] = chebi[n]
		elif 'background' == type_[n]:
			props['shape'] = graph['viewShape'][n]
		f = geojson.Feature(geometry=geom, properties=props)
		features.append(f)

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


def get_formula(graph, n, onto):
	ins = '&'.join(
		["{0} * {1}".format(int(graph['stoichiometry'][e]), get_short_name(graph, graph.source(e), onto)) for e in
		 graph.getInEdges(n)])
	outs = '&'.join(
		["{0} * {1}".format(int(graph['stoichiometry'][e]), get_short_name(graph, graph.target(e), onto)) for e in
		 graph.getOutEdges(n)])
	return ins, outs


def rgb(triplet):
	return (_HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]])


def triplet(c, lettercase=LOWERCASE):
	return '#' + format((c.getR() << 16 | c.getG() << 8 | c.getB()), '06' + lettercase)


def get_min_max(graph):
	layout = graph.getLayoutProperty("viewLayout")
	size = graph.getSizeProperty("viewSize")

	m = lambda l, s: (l.getX() - s.getW() / 2, l.getY() - s.getH() / 2)
	M = lambda l, s: (l.getX() + s.getW() / 2, l.getY() + s.getH() / 2)
	mM = lambda n: (m(layout[n], size[n]), M(layout[n], size[n]))
	(m_x, m_y), (M_x, M_y) = mM(graph.getNodes().next())
	for n in graph.getNodes():
		(m_x_, m_y_), (M_x_, M_y_) = mM(n)
		if m_x_ < m_x: m_x = m_x_
		if m_y_ < m_y: m_y = m_y_
		if M_x_ > M_x: M_x = M_x_
		if M_y_ > M_y: M_y = M_y_

	w, h = M_x - m_x, M_y - m_y
	if w > h:
		m_y -= (w - h) / 2
		M_y += (w - h) / 2
	elif h > w:
		m_x -= (h - w) / 2
		M_x += (h - w) / 2

	return (m_x - MARGIN, m_y - MARGIN), (M_x + MARGIN, M_y + MARGIN)