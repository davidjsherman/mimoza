from tulip import *
from math import sqrt, radians, atan2, cos, sin, degrees


def layout_ub_sps(graph): 
	viewLayout = graph.getLayoutProperty('viewLayout')
	ubiquitous =  graph.getBooleanProperty("ubiquitous")
	viewLabel =  graph.getStringProperty("viewLabel")
	viewSize = graph.getSizeProperty("viewSize")
	
	for r in (n for n in graph.getNodes() if 'reaction' == graph['type'][n]):
		x1, y1 = viewLayout[r].getX(), viewLayout[r].getY()
		c = min(viewSize[r].getW() * 1.8, 3.5) # edge-after-bent length
		for (g_n, g_e, g_n1, p) in [(graph.getInNodes, graph.getOutEdges, graph.getOutNodes, 1), (graph.getOutNodes, graph.getInEdges, graph.getInNodes, -1)]:
			in_n = filter(lambda n: not ubiquitous[n], g_n(r))	
			in_ubs = filter(lambda n: ubiquitous[n], g_n(r))	
			n = len(in_ubs)
			if not n: continue
			if n % 2 == 1: n += 1
			if in_n: 
				m = in_n[0]
				x2, y2 = viewLayout[m].getX(), viewLayout[m].getY()
			else:
				out_n = filter(lambda n: not ubiquitous[n], g_n1(r))
				if out_n:
					m = out_n[0]
					x3, y3 = viewLayout[m].getX(), viewLayout[m].getY()
					x2, y2 = x1 - (x3 - x1), y1 - (y3 - y1)					
				else:
					x2, y2 = x1 + 10 * p, y1	
			gap = 2 * min(90, (n if n > 1 else 2)*20)
			beta = radians(gap / 2)
			s = viewSize[r].getW() * 0.7 # distance from reaction to the edge bent
			for ub in in_ubs:
				e = g_e(ub).next()	
				alpha = atan2(y2-y1, x2-x1)
				x0, y0 = x1 + s * cos(alpha), y1 + s * sin(alpha)
				viewLayout.setEdgeValue(e, [tlp.Coord(x0, y0)])
				gamma = alpha - beta
				x3, y3 = x0 + c * cos(gamma), y0 + c * sin(gamma)
				viewLayout.setNodeValue(ub, tlp.Coord(x3, y3))
				if degrees(beta) > 0: 
					s += 1
				if n > 1: 
					beta -= radians(gap/(n - 1))
				if degrees(beta) < 0:
					s -= 1
