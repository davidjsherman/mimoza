from tulip import *
from math import radians, atan2, cos, sin, degrees, sqrt
from modules.color import white


def layout_ub_sps(graph): 
	viewLayout = graph.getLayoutProperty('viewLayout')
	ubiquitous = graph.getBooleanProperty("ubiquitous")
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


def shorten_edges(graph, margin=5):
	v_lo = graph.getLayoutProperty("viewLayout")
	ub = graph.getBooleanProperty("ubiquitous")
	v_s = graph.getSizeProperty("viewSize")
	diag = lambda a, b: sqrt(pow(a, 2) + pow(b, 2))
	for i in xrange(5):
		processed = set()
		moved = set()
		for s in sorted((n for n in graph.getNodes() if not ub[n]), key = lambda n: -v_s[n].getW()):
			processed.add(s)
			s_lo, s_s = v_lo[s], v_s[s]
			for t in (n for n in graph.getInOutNodes(s) if not ub[n] and not n in processed):
				t_lo, t_s = v_lo[t],  v_s[t]
				dx, dy = t_lo.getX() - s_lo.getX(), t_lo.getY() - s_lo.getY()
				e_len = diag(dx, dy)
				short_len = diag(s_s.getW(), s_s.getH()) / 2 + diag(t_s.getW(), t_s.getH()) / 2
				if e_len > short_len:
					if not t in moved:
						alpha = atan2(dx, dy)
						v_lo[t] = tlp.Coord(s_lo.getX() + short_len * sin(alpha), s_lo.getY() + short_len * cos(alpha))
						moved.add(t)
					else:
						alpha = atan2(-dx, -dy)
						v_lo[s] = tlp.Coord(t_lo.getX() + short_len * sin(alpha), t_lo.getY() + short_len * cos(alpha))
						moved.add(s)


def neighbours(ns, org_ns, graph, processed, limit=500):
	if not ns or limit < len(ns): return set()
	processed |= ns
	all_ns = set()
	for n in ns:
		all_ns |= (set(graph.getInOutNodes(n)) - processed)
	return ns | neighbours(all_ns, org_ns, graph, processed, limit - len(ns))


def layout_comp(graph):
	root = graph.getRoot()

	ssub = graph.inducedSubGraph([n for n in graph.getNodes() if not graph["ubiquitous"][n]])
	sub = ssub.inducedSubGraph([n for n in graph.getNodes() if not graph["ubiquitous"][n]])

	organelles = root.getAttribute("organelles").split(";")
	comp_ns = {n for n in sub.getNodes() if sub["name"][n] in organelles and sub.isMetaNode(n)}
	org2n = {sub['name'][n] : n for n in comp_ns}

	processed = set(comp_ns)
	mns = []
	for org in sorted(organelles, key=lambda t: -sub["viewSize"][org2n[t]].getW()):
		n = org2n[org]
		ns = [n]
		ns.extend(neighbours({n}, comp_ns, sub, set(processed), sub.numberOfNodes() / len(comp_ns)))
		processed |= set(ns)
		meta_node = sub.createMetaNode(ns, False)
		processed.add(meta_node)
		gr = sub["viewMetaGraph"][meta_node]
		gr.setName(org)
		layout(gr, 1)
		shorten_edges(gr)
		bb = tlp.computeBoundingBox(gr)
		sub["viewSize"][meta_node] = tlp.Size(bb.width(), bb.height())
		sub["viewLabel"][meta_node] = org
		sub["viewShape"][meta_node] = 9
		mns.append(meta_node)
	layout(sub, 1)
	shorten_edges(sub)
#	sub.applyAlgorithm("Edge bundling")
	for m in mns:
		sub.openMetaNode(m)
	copy_layout(sub, graph)
	graph.delAllSubGraphs(ssub)
	layout_ub_sps(graph)


def copy_layout(from_gr, to_gr):
	for n in from_gr.getNodes():
		if to_gr.isElement(n):
			to_gr["viewLayout"][n] = from_gr["viewLayout"][n]
		for m in (m for m in from_gr.getInNodes(n) if to_gr.isElement(m)):
			e = to_gr.existEdge(m, n)
			if e:
				to_gr["viewLayout"][e] = from_gr["viewLayout"][e]


def layout_hierarchically(qo, margin=5):
	ds = tlp.getDefaultPluginParameters("Hierarchical Graph", qo)
	if qo.numberOfNodes() > 1:
		[s, s1] = sorted((qo["viewSize"][n] for n in qo.getNodes()))[-2:]
		# looks like there is a bug in Tulip and it uses the 'layer spacing' value
		# instead of the 'node spacing' one and visa versa
		ds["layer spacing"] = s.getW() / 2 + s1.getW() / 2 + margin
		ds["node spacing"] = s.getH() / 2 + s1.getH() / 2 + margin
	qo.computeLayoutProperty("Hierarchical Graph", qo['viewLayout'], ds)


def layout_circle(qo, margin=5):
	ds = tlp.getDefaultPluginParameters("Circular (OGDF)", qo)
	if qo.numberOfNodes() > 1:
		[s, s1] = sorted((qo["viewSize"][n] for n in qo.getNodes()))[-2:]
		ds["minDistCircle"] = s.getW() / 2 + s1.getW() / 2
		ds["minDistLevel"] = margin
		ds["minDistCC"] = 1
		ds["minDistSibling"] = 0
	qo.computeLayoutProperty("Circular (OGDF)", qo['viewLayout'], ds)


def layout_force(qo, margin=5):
	ds = tlp.getDefaultPluginParameters("FM^3 (OGDF)", qo)
	ds["Unit edge length"] = margin
	qo.computeLayoutProperty("FM^3 (OGDF)", qo['viewLayout'], ds)


def remove_overlaps(graph, margin=5):
	ds = tlp.getDefaultPluginParameters("Fast Overlap Removal", graph)
	ds["x border"] = margin
	ds["y border"] = margin
	graph.computeLayoutProperty("Fast Overlap Removal", graph['viewLayout'], ds)


def pack_cc(graph):
	ds = tlp.getDefaultPluginParameters("Connected Component Packing", graph)
	graph.computeLayoutProperty("Connected Component Packing", graph['viewLayout'], ds)


def layout(graph, margin=5):
	if graph == graph.getRoot():
		graph = tlp.newCloneSubGraph(graph)
		graph.setName("original graph")

	sub = graph.inducedSubGraph([n for n in graph.getNodes()])
	simples, cycles, mess = detect_components(sub)

	side = None
	for gr in simples:
		qo = gr.inducedSubGraph([n for n in gr.getNodes() if not gr["ubiquitous"][n]])
		if qo.numberOfEdges() == 0:
			continue
		d = max((qo.deg(n) for n in qo.getNodes()))
		if d > 2:
			layout_hierarchically(qo, margin)
		else:
			if not side:
				side = get_side(graph)
			lo_a_line(qo, side)
		copy_layout(qo, graph)

	for gr in cycles:
		qo = gr.inducedSubGraph([n for n in gr.getNodes() if not gr["ubiquitous"][n]])
		layout_circle(qo, margin)
		copy_layout(qo, gr)
		layout_ub_sps(gr)
#		remove_overlaps(gr, margin)
		copy_layout(gr, graph)

	for gr in mess:
		qo = gr.inducedSubGraph([n for n in gr.getNodes() if not gr["ubiquitous"][n]])
		layout_force(qo, margin)
		remove_overlaps(qo, margin)
		copy_layout(qo, gr)
		layout_ub_sps(gr)
		copy_layout(gr, graph)

	graph.delAllSubGraphs(sub)

	layout_ub_sps(graph)
	pack_cc(graph)
	layout_ub_sps(graph)


def detect_components(graph):
	comp_list = tlp.ConnectedTest.computeConnectedComponents(graph)
	cycles, simples, mess = [], [], []
	threshold = 3
	for ns in comp_list:
		gr = graph.inducedSubGraph(ns)
		visited = set()
		cycles_num = DFS(list(ns)[0], gr, visited, None, threshold)
		if cycles_num == 0:
			gr.setName("acyclic")
			simples.append(gr)
		elif cycles_num < threshold * 2 and len(ns) < 100:
			gr.setName("cycle")
			cycles.append(gr)
		else:
			gr.setName("mess ({0})".format(cycles_num))
			mess.append(gr)
	return simples, cycles, mess


# deep-first search
# every cycle will be counted twice
# as every node of a cycle can be approached from two sides
def DFS(n, graph, visited, prev, limit=3, indent=''):
	if n in visited:
		return 1
	num = 0
	visited.add(n)
	for m in graph.getInOutNodes(n):
		if m == prev:
			continue
		else:
			num += DFS(m, graph, visited, n, limit, indent + ' ')
			if num > limit:
				return num
	return num


def get_side(graph):
	l = 0
	for n in graph.getNodes():
		s = graph["viewSize"][n]
		l += s.getW() * s.getH() * 16
	return sqrt(l)


# expects to be called on a subgraph that has no ubiquitous nodes.
def lo_a_line(graph, side=None):
	viewLayout = graph.getLayoutProperty('viewLayout')
	viewLayout.setAllEdgeValue([])

	starts = (n for n in graph.getNodes() if 1 == graph.deg(n))

	if not side:
		side = get_side(graph)

	processed = set()
	x, y = 0, side
	max_h = 0
	def process_n(n, x, y, max_h):
		def get_coord(s, x, y, max_h):
			x += s.getW() / 2 + 2
			if x > side:
				x = 0
				y -= max_h * 4
				max_h = s.getH()
			return x, y, max_h
		processed.add(n)
		s = graph["viewSize"][n]
		max_h = max(max_h, s.getH())
		x, y, max_h = get_coord(s, x, y, max_h)
		viewLayout[n] = tlp.Coord(x, y)
		x, y, max_h = get_coord(s, x, y, max_h)
		return x, y, max_h

	for n in starts:
		if n in processed:
			continue
		x = side
		x, y, max_h = process_n(n, x, y, max_h)
		while True:
			ns = [m for m in graph.getInOutNodes(n) if not (m in processed)]
			if not ns:
				break
			n = ns[0]
			x, y, max_h = process_n(n, x, y, max_h)
	return graph


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


def show_reversibility(graph):
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


def layout_generalization_based(graph):
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
			mn2color[n] = c
		else:
			nds.append(n)
	for n in nds:
		graph.getRoot()["viewBorderWidth"][n] = 0.1 * graph.getRoot()["viewSize"][n].width()
		graph.getRoot()["viewBorderColor"][n] = white
	clone = graph.getSuperGraph().inducedSubGraph(nds)
	clone.setName(graph.getName() + "_full")
	vl = {}

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
		clone["viewColor"][nn] = mn2color[n]
		clone["type"][nn] = 'background'

		meta_neighbours = lambda nodes: sorted([t for t in nodes if graph.isMetaNode(t)], key=lambda t: -viewSize[t].getW())
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
	show_reversibility(clone)
	show_reversibility(graph)

	return clone