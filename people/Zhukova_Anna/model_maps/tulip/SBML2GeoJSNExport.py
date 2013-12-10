from tulip import *
import tulipplugins
import geojson
from sympy.logic.boolalg import to_cnf, conjuncts, disjuncts


_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}
LOWERCASE, UPPERCASE = 'x', 'X'
DIMENSION = 512
	
class SBML2GeoJSNExport(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)
		self.addStringParameter("file::GeoJSON", "GeoJSON file to be exported.", "")		

	def check(self):
		return (True, "")

	def run(self):
		graph = self.graph
		ga =  graph.getStringProperty("geneAssociation")
		type_ =  graph.getStringProperty("type")
		name = graph.getStringProperty("name")
		layout = graph.getLayoutProperty("viewLayout")
		size = graph.getSizeProperty("viewSize")
		color = graph.getColorProperty("viewColor")
		fake = graph.getBooleanProperty("fake")
		chebi = graph.getStringProperty("chebi_id")
		
		(m_x, m_y), (M_x, M_y) = getMinMax(graph)
		x_scale = DIMENSION/(M_x - m_x)
		y_scale = DIMENSION/(M_y - m_y)
		
		features = []
		
		def stoich(e):
			st = int(graph['stoichiometry'][e])
			return '' if 1 == st else st
			
		for n in graph.getNodes():
			if fake[n]: continue
			geom = geojson.Point([(layout[n].getX() - m_x) * x_scale, (M_y - layout[n].getY()) * y_scale])
			props = {"name": name[n], "color": triplet(color[n]), \
				"radius": size[n].getW() * x_scale, "type": type_[n]}
			if 'reaction' == type_[n]:
				gann = ga[n].replace(' and ', ' & ').replace(' or ', ' | ').replace('(and ', '(& ').replace('(or ', '(| ').replace(' and)', ' &)').replace(' or)', ' |)')
				if gann:
					res = to_cnf(gann, False)
					gann = '&'.join(['|'.join([str(it) for it in disjuncts(cjs)]) for cjs in conjuncts(res)])
				props["gene_association"] = gann
				ins = ' + '.join(["{0} * {1}".format(stoich(e), graph['name'][graph.source(e)]) for e in graph.getInEdges(n)])
				outs = ' + '.join(["{0} * {1}".format(stoich(e), graph['name'][graph.source(e)]) for e in graph.getOutEdges(n)])
				props["formula"] = ins + (' -> ' if graph['reversible'][n] else ' <-> ') + outs				
			else:
				props["chebi"] = chebi[n]
			f = geojson.Feature(geometry=geom, properties=props)
			features.append(f)				
		fc = geojson.FeatureCollection(features, \
			geometry=geojson.Polygon([[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]]))
		with open(self.dataSet["file::GeoJSON"], 'w') as f:
			f.write("var gjsn = {0}\n".format(geojson.dumps(fc).replace('"id": null', '')))
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBML2GeoJSNExport", "SBML2GeoJSNExport", "anna", "10/12/2013", "", "1.0", "Metabolic")



def rgb(triplet):
    return (_HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]])

def triplet(c, lettercase=LOWERCASE):
    return '#' + format((c.getR()<<16 | c.getG()<<8 | c.getB()), '06'+lettercase)

def getMinMax(graph):
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
		
	return (m_x, m_y), (M_x, M_y)
	
