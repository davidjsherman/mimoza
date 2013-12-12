from tulip import *
import tulipplugins
import geojson
from sympy.logic.boolalg import to_cnf, conjuncts, disjuncts


_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}
LOWERCASE, UPPERCASE = 'x', 'X'
DIMENSION = 512
MARGIN = 3.8
	
	
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
	ins = '&'.join(["{0} * {1}".format(int(graph['stoichiometry'][e]), graph['name'][graph.source(e)]) for e in graph.getInEdges(n)])
	outs = '&'.join(["{0} * {1}".format(int(graph['stoichiometry'][e]), graph['name'][graph.target(e)]) for e in graph.getOutEdges(n)])
	return ins, outs	
	
				
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
		chebi = graph.getStringProperty("chebi_id")
		
		(m_x, m_y), (M_x, M_y) = getMinMax(graph)
		x_scale = DIMENSION/(M_x - m_x)
		y_scale = DIMENSION/(M_y - m_y)
		
		features = []
			
		for n in graph.getNodes():
			if not type_[n] in ['reaction', 'species', 'compartment']:
				continue
			geom = geojson.Point([(layout[n].getX() - m_x) * x_scale, (M_y - layout[n].getY()) * y_scale])
			props = {"id": graph['id'][n], "name": name[n], "color": triplet(color[n]), \
				"width": size[n].getW() * x_scale, "height": size[n].getH() * y_scale,  "type": type_[n]}
			if 'reaction' == type_[n]:
				props["gene_association"] = get_gene_association_list(ga[n])
				props["reversible"] = graph['reversible'][n]
				ins, outs = get_formula(graph, n)	
				props['reactants'] = ins
				props['products'] = outs			
			else:
				props["chebi"] = chebi[n]
			f = geojson.Feature(geometry=geom, properties=props)
			features.append(f)				
		fc = geojson.FeatureCollection(features, \
			geometry=geojson.Polygon([[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]]))
		with open(self.dataSet["file::GeoJSON"], 'w') as f:
			f.write("var gjsn_{1} = {0}\n".format(geojson.dumps(fc).replace('"id": null', ''), graph.getName()))
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
		
	return (m_x - MARGIN, m_y - MARGIN), (M_x + MARGIN, M_y + MARGIN)
	
