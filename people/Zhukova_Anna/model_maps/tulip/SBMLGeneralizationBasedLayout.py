from tulip import *
import tulipplugins
from math import sin, cos, atan2, degrees, sqrt


class SBMLGeneralizationBasedLayout(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return (True, "")

	def run(self):
		graph = self.graph
		viewLayout =  graph.getLayoutProperty("viewLayout")
		viewMetaGraph =  graph.getGraphProperty("viewMetaGraph")
		viewSize =  graph.getSizeProperty("viewSize")	
		
		nds = []
		mn2color = {}
		for n in graph.getNodes():
			if graph.isMetaNode(n):
				mg = viewMetaGraph[n]
				ns = list(mg.getNodes())
				nds.extend(ns)
				c = graph["viewColor"][n]
				mn2color[n] = tlp.Color(c.getR(), c.getG(), c.getB(), 200)
			else:
				nds.append(n)
		for n in nds:
			graph.getRoot()["viewBorderWidth"][n] = 1
			graph.getRoot()["viewBorderColor"][n] = tlp.Color(255, 255, 255)
		clone = graph.getSuperGraph().inducedSubGraph(nds)
		clone.setName(graph.getName() + "_full")
		vl = {}
		fakenn2color = {}
		
		meta_ns = {n for n in graph.getNodes() if graph.isMetaNode(n)}
		meta_sps = {n for n in meta_ns if 'species' == graph["type"][n]}
		meta_rs = meta_ns - meta_sps
		
		depends_on = {}
		our_sps = set()
		for s in meta_sps:
			rs = set(graph.getInOutNodes(s)) & meta_rs
			sps = set()
			for r in rs:
				sps |= set(graph.getInOutNodes(s)) & meta_sps
			depends_on[s] = sps - {s}
			our_sps |= set(viewMetaGraph[s].getNodes())
			
		n2k = {}
		while meta_sps:
			n = min(meta_sps, key=lambda s: len(depends_on[s] & meta_sps))
			meta_sps -= {n}
			mg = viewMetaGraph[n]
			for s in mg.getNodes():
				rs = clone.getInOutNodes(s)
				sps = set()
				for r in rs:
					sps |= set(clone.getInOutNodes(r)) & our_sps
				sps -= {s}
				n2k[s] = (graph["id"][n], clone.deg(s), clone["id"][s])
				for ss in sps:
					if ss in n2k:
						n2k[s] = n2k[ss]
		for n in meta_rs:
			mg = viewMetaGraph[n]
			for r in mg.getNodes():
				n2k[r] = sorted(n2k[it] for it in set(clone.getInOutNodes(r)) & our_sps)
						
		for n in meta_ns:		
			lo = viewLayout[n]				
			s = viewSize[n].getW()
			mg = viewMetaGraph[n]
					
			# add a fake node to keep a common background for similar nodes
			nn = clone.addNode()
			clone["viewSize"][nn] = graph["viewSize"][n]
			clone["viewShape"][nn] = graph["viewShape"][n]			
			clone["viewBorderWidth"][nn] = 0	
			clone["viewBorderColor"][nn] = graph["viewBorderColor"][n]
			co = graph["viewLayout"][n]
			clone["viewLayout"][nn] = tlp.Coord(co.getX(), co.getY(), 0)
			fakenn2color[nn] = mn2color[n]
			clone["type"][nn] = 'background'
			
			meta_neighbours = lambda nodes: sorted([t for t in nodes if graph.isMetaNode(t)], \
			key=lambda t: -viewSize[t].getW())
			o_n_1 = meta_neighbours(graph.getInNodes(n))
			o_n_2 = meta_neighbours(graph.getOutNodes(n))
			if not o_n_1:
				alpha = get_alpha(lo, viewLayout[o_n_2[0]]) if o_n_2 else 0
			elif not o_n_2:
				alpha = get_alpha(viewLayout[o_n_1[0]], lo)
			else:
				alpha = get_alpha(viewLayout[o_n_1[0]], viewLayout[o_n_2[0]])
			if alpha < 0: alpha = - alpha
			vl[mg] = lo.getX(), lo.getY(), alpha
				
				
			ns = sorted(mg.getNodes(), key=lambda it: n2k[it])
			s_m = tlp.Size(s / len(ns), s / len(ns))
			if 'reaction' == graph["type"][n] and (alpha == 45 or alpha == 135 or alpha == -45 or alpha == -135):
				s *= sqrt(2)
			dy = s / len(ns)
			x0, y0 = lo.getX(), lo.getY() - s / 2 + dy / 2
			x, y = x0, y0
			for m in ns:
				mg["viewSize"][m] = s_m
				mg["viewLayout"][m] = tlp.Coord(x, y)	
				clone["viewLayout"][m]	 = tlp.Coord(x, y)	
				clone["viewSize"][m] = s_m		
				y += dy
				
			for o_n in filter(lambda t: graph["ubiquitous"][t], graph.getInOutNodes(n)):
				lo_n = viewLayout[o_n]
				alpha = atan2(lo_n.getY()-lo.getY(), lo_n.getX()-lo.getX())
				x0, y0 = lo.getX() + s * 0.7 * cos(alpha), lo.getY() + s * 0.7 * sin(alpha)
				for m in ns:
					for e in clone.getInOutEdges(m):
						if o_n == clone.target(e) or o_n == clone.source(e):
							clone["viewLayout"][e] = [tlp.Coord(x0, y0)]
			
					
		for mg, (x0, y0, alpha) in vl.iteritems():
			mg["viewLayout"].translate(tlp.Coord(-x0, -y0), mg)
			mg["viewLayout"].rotateZ(-alpha, mg)
			mg["viewLayout"].translate(tlp.Coord(x0, y0), mg)
			for m in mg.getNodes():
				clone["viewLayout"][m] = mg["viewLayout"][m]
		vrr(clone)
		vrr(graph)
		for nn, c in fakenn2color.iteritems():
			clone["viewColor"][nn] = c
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLGeneralizationBasedLayout", "SBMLGeneralizationBasedLayout", "anna", "09/12/2013", "", "1.0", "Metabolic")
					
				
def get_alpha(lo, o_lo):
	alpha = degrees(atan2(lo.getY() - o_lo.getY(), o_lo.getX() - lo.getX()))
	if -22.5 <= alpha < 22.5:
		return 0
	elif 22.5 <= alpha < 67.5:
		return 45
	elif 67.5 <= alpha < 112.5:
		return 90
	elif 112.5 <= alpha < 157.5:
		return 135
	elif 157.5 <= alpha <= 180:
		return 180
	elif -180 <= alpha < -157.5:
		return  -180
	elif -157.5 <= alpha < -112.5:
		return -135
	elif -112.5 <= alpha < -67.5:
		return -90
	elif -67.5 <= alpha < -22.5:
		return -45
		
		
def simple_layout_ub_sps(graph): 
	reaction =  graph.getBooleanProperty("reaction")
	ubiquitous =  graph.getBooleanProperty("ubiquitous")
	viewLabel =  graph.getStringProperty("viewLabel")
	viewLayout =  graph.getLayoutProperty("viewLayout")
	viewSize = graph.getSizeProperty("viewSize")
	
	for r in filter(lambda n: reaction[n], graph.getNodes()):
		x1, y1 = viewLayout[r].getX(), viewLayout[r].getY()
		for (g_n, g_e) in [(graph.getInNodes, graph.getOutEdges), \
		(graph.getOutNodes, graph.getInEdges)]:
			in_n = sorted(filter(lambda n: not ubiquitous[n], g_n(r)), key=lambda n: viewLabel[n])	
			in_ubs = sorted(filter(lambda n: ubiquitous[n], g_n(r)), key=lambda n: viewLabel[n])	
			if not in_ubs: continue
			if in_n: 
				m = in_n[0]
				x2, y2 = viewLayout[m].getX(), viewLayout[m].getY()
			else:
				m = in_ubs[0]
				x2, y2 = viewLayout[m].getX(), viewLayout[m].getY()	
			s = viewSize[r].getW() * 0.7 # distance from reaction to the edge bent
			for ub in in_ubs:
				e = g_e(ub).next()	
				alpha = atan2(y2-y1, x1-x2)
				x0, y0 = x1 - s * cos(alpha), y1 + s * sin(alpha)
				viewLayout.setEdgeValue(e, [tlp.Coord(x0, y0)])
				

def vrr(graph):
	reversible =  graph.getBooleanProperty("reversible")
	viewTgtAnchorShape =  graph.getIntegerProperty("viewTgtAnchorShape")
	viewSrcAnchorShape =  graph.getIntegerProperty("viewSrcAnchorShape")

	for n in (n for n in graph.getNodes() if 'reaction' == graph['type'][n] and reversible[n]):
			for e in graph.getInEdges(n):
				viewTgtAnchorShape[e] = -1
				viewSrcAnchorShape[e] = 50
			for e in graph.getOutEdges(n):
				viewTgtAnchorShape[e] = 50
				viewSrcAnchorShape[e] = -1
