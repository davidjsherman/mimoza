from tulip import *
from math import radians, atan2, cos, sin, degrees, sqrt
from modules.color import white
from modules.model_utils import clone_node
from modules.resize import ub_sp_size


def layout_ub_sps(graph):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty('viewLayout')
	ubiquitous = root.getBooleanProperty("ubiquitous")
	view_size = root.getSizeProperty("viewSize")

	for r in (n for n in graph.getNodes() if 'reaction' == root['type'][n]):
		x1, y1 = view_layout[r].getX(), view_layout[r].getY()
		# c = min(view_size[r].getW() * 1.8, 3.5)  # edge-after-bent length
		for (get_reactants, get_reaction_edges, get_products, direction) in [
			(graph.getInNodes, graph.getOutEdges, graph.getOutNodes, 1),
			(graph.getOutNodes, graph.getInEdges, graph.getInNodes, -1)]:

			ubiquitous_reactants = filter(lambda nd: ubiquitous[nd], get_reactants(r))
			ub_reactants_len = len(ubiquitous_reactants)
			if not ub_reactants_len:
				continue
			if ub_reactants_len % 2 == 1:
				ub_reactants_len += 1

			specific_reactants = filter(lambda nd: not ubiquitous[nd], get_reactants(r))
			r_radius = view_size[r].getW() * sqrt(2) / 2
			edge_len = ub_sp_size * max(ub_reactants_len / 2, 3)
			if specific_reactants:
				specific_reactant_example = specific_reactants[0]
				x2, y2 = view_layout[specific_reactant_example].getX(), view_layout[specific_reactant_example].getY()
				species_size = view_size[specific_reactant_example].getW() / 2
				edge_len = (sqrt(pow(x1 - x2, 2) + pow(y2 - y1, 2)) - r_radius - species_size)
			else:
				specific_products = filter(lambda n: not ubiquitous[n], get_products(r))
				if specific_products:
					specific_product_example = specific_products[0]
					x3, y3 = view_layout[specific_product_example].getX(), view_layout[specific_product_example].getY()
					x2, y2 = x1 - (x3 - x1), y1 - (y3 - y1)					
				else:
					x2, y2 = x1 + view_size[r].getW() + ub_sp_size * ub_reactants_len * direction, y1

			# beta is the max angle between the ubiquitous and the specific edges
			gap = 2 * min(100, max(60, ub_reactants_len * 20))
			beta0 = radians(gap / 2)
			beta = beta0
			d_beta = radians(gap/(ub_reactants_len - 1))

			# distance from reaction to the edge bent
			bent = min(ub_sp_size / 2, edge_len / 2)
			s0 = r_radius + bent
			s = s0
			ds = min(2 * (edge_len - bent - ub_sp_size / 2) / ub_reactants_len, ub_sp_size)
			# s += ds * ub_reactants_len / 2

			# angle between the horizontal line and the reaction-specific-species edge
			alpha = atan2(y2 - y1, x2 - x1)

			dc = 0
			towards_edge = -1
			for ub in ubiquitous_reactants:
				# it is the only edge as ubiquitous species are duplicated
				e = get_reaction_edges(ub).next()
				x0, y0 = x1 + s * cos(alpha), y1 + s * sin(alpha)
				view_layout.setEdgeValue(e, [tlp.Coord(x0, y0)])

				gamma = alpha + beta
				# edge-after-bent length
				c = min(edge_len - s0 + dc + r_radius - ub_sp_size, 2 * ub_sp_size)

				x3, y3 = x0 + c * cos(gamma), y0 + c * sin(gamma)
				view_layout.setNodeValue(ub, tlp.Coord(x3, y3))
				# if degrees(beta) > 0:
				# 	s += ds
				if degrees(beta) * degrees(beta + towards_edge * d_beta) < 0:
					beta = -beta0
					towards_edge = 1
					s = s0
					dc = 0
				else:
					beta += towards_edge * d_beta
					s += ds / 3
					dc += ds
				# if degrees(beta) < 0:
				# 	s -= ds


def shorten_edges(graph, margin=5):
	root = graph.getRoot()
	v_lo = root.getLayoutProperty("viewLayout")
	ub = root.getBooleanProperty("ubiquitous")
	v_s = root.getSizeProperty("viewSize")
	diameter = lambda a, b: sqrt(pow(a, 2) + pow(b, 2))
	for i in xrange(5):
		processed = set()
		moved = set()
		for s in sorted((n for n in graph.getNodes() if not ub[n]), key=lambda n: -v_s[n].getW()):
			processed.add(s)
			s_lo, s_s = v_lo[s], v_s[s]
			for t in (n for n in graph.getInOutNodes(s) if not ub[n] and not n in processed):
				t_lo, t_s = v_lo[t],  v_s[t]
				dx, dy = t_lo.getX() - s_lo.getX(), t_lo.getY() - s_lo.getY()
				e_len = diameter(dx, dy)
				short_len = diameter(s_s.getW(), s_s.getH()) / 2 + diameter(t_s.getW(), t_s.getH()) / 2
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


def layout_cytoplasm(graph, margin=5):
	root = graph.getRoot()
	for n in graph.getNodes():
		if 'species' == root['type'][n] and not graph.isMetaNode(n) and graph.deg(n) >= 4:
			clone_node(graph, n)
	sub = graph.inducedSubGraph([n for n in graph.getNodes()])
	qo = sub.inducedSubGraph([n for n in sub.getNodes() if not root["ubiquitous"][n]])
	layout_force(qo, margin)
	remove_overlaps(qo, margin)
	graph.delAllSubGraphs(sub)
	layout_ub_sps(graph)
	pack_cc(graph)
	graph.applyAlgorithm("Edge bundling")



def layout_comp(graph):
	root = graph.getRoot()

	ssub = graph.inducedSubGraph([n for n in graph.getNodes() if not root["ubiquitous"][n]])
	sub = ssub.inducedSubGraph([n for n in ssub.getNodes()])

	organelles = root.getAttribute("organelles").split(";")
	comp_ns = {n for n in sub.getNodes() if root["name"][n] in organelles and sub.isMetaNode(n)}
	org2n = {root['name'][n]: n for n in comp_ns}

	processed = set(comp_ns)
	mns = []
	for org in sorted(organelles, key=lambda t: -root["viewSize"][org2n[t]].getW()):
		n = org2n[org]
		ns = [n]
		ns.extend(neighbours({n}, comp_ns, sub, set(processed), sub.numberOfNodes() / len(comp_ns)))
		processed |= set(ns)
		meta_node = sub.createMetaNode(ns, False)
		processed.add(meta_node)
		gr = root["viewMetaGraph"][meta_node]
		gr.setName(org)
		layout(gr, 1)
		shorten_edges(gr)
		bb = tlp.computeBoundingBox(gr)
		root["viewSize"][meta_node] = tlp.Size(bb.width(), bb.height())
		root["viewLabel"][meta_node] = org
		root["viewShape"][meta_node] = 9
		mns.append(meta_node)
	layout(sub, 1)
	shorten_edges(sub)
#	sub.applyAlgorithm("Edge bundling")
	for m in mns:
		sub.openMetaNode(m)
	graph.delAllSubGraphs(ssub)
	layout_ub_sps(graph)
	pack_cc(graph)


def layout_hierarchically(qo, margin=5):
	root = qo.getRoot()
	ds = tlp.getDefaultPluginParameters("Hierarchical Graph", qo)
	if qo.numberOfNodes() > 1:
		[s, s1] = sorted((root["viewSize"][n] for n in qo.getNodes()))[-2:]
		# looks like there is a bug in Tulip and it uses the 'layer spacing' value
		# instead of the 'node spacing' one and visa versa
		ds["layer spacing"] = s.getW() / 2 + s1.getW() / 2 + margin
		ds["node spacing"] = s.getH() / 2 + s1.getH() / 2 + margin
	qo.computeLayoutProperty("Hierarchical Graph", root['viewLayout'], ds)


def layout_circle(qo, margin=5):
	root = qo.getRoot()
	ds = tlp.getDefaultPluginParameters("Circular (OGDF)", qo)
	if qo.numberOfNodes() > 1:
		[s, s1] = sorted((root["viewSize"][n] for n in qo.getNodes()))[-2:]
		ds["minDistCircle"] = s.getW() / 2 + s1.getW() / 2
		ds["minDistLevel"] = margin
		ds["minDistCC"] = 1
		ds["minDistSibling"] = 0
	qo.computeLayoutProperty("Circular (OGDF)", root['viewLayout'], ds)


def layout_force(qo, margin=5):
	root = qo.getRoot()
	ds = tlp.getDefaultPluginParameters("FM^3 (OGDF)", qo)
	ds["Unit edge length"] = margin
	qo.computeLayoutProperty("FM^3 (OGDF)", root['viewLayout'], ds)


def remove_overlaps(graph, margin=5):
	root = graph.getRoot()
	ds = tlp.getDefaultPluginParameters("Fast Overlap Removal", graph)
	ds["x border"] = margin
	ds["y border"] = margin
	graph.computeLayoutProperty("Fast Overlap Removal", root['viewLayout'], ds)


def pack_cc(graph):
	root = graph.getRoot()
	ds = tlp.getDefaultPluginParameters("Connected Component Packing", graph)
	graph.computeLayoutProperty("Connected Component Packing", root['viewLayout'], ds)


def layout(graph, margin=5):
	root = graph.getRoot()
	if graph == root:
		graph = tlp.newCloneSubGraph(graph)
		graph.setName("original graph")

	sub = graph.inducedSubGraph([n for n in graph.getNodes()])
	simples, cycles, mess = detect_components(sub)

	side = None
	for gr in simples:
		qo = gr.inducedSubGraph([n for n in gr.getNodes() if not root["ubiquitous"][n]])
		if qo.numberOfEdges() == 0:
			continue
		d = max((qo.deg(n) for n in qo.getNodes()))
		if d > 2:
			layout_hierarchically(qo, margin)
		else:
			if not side:
				side = get_side(graph)
			lo_a_line(qo, side)

	for gr in cycles:
		qo = gr.inducedSubGraph([n for n in gr.getNodes() if not root["ubiquitous"][n]])
		layout_circle(qo, margin)
		layout_ub_sps(gr)
#		remove_overlaps(gr, margin)

	for gr in mess:
		qo = gr.inducedSubGraph([n for n in gr.getNodes() if not root["ubiquitous"][n]])
		layout_force(qo, margin)
		remove_overlaps(qo, margin)
		layout_ub_sps(gr)

	graph.delAllSubGraphs(sub)

	layout_ub_sps(graph)
	pack_cc(graph)


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
	root = graph.getRoot()
	l = 0
	for n in graph.getNodes():
		s = root["viewSize"][n]
		l += s.getW() * s.getH() * 16
	return sqrt(l)


# expects to be called on a subgraph that has no ubiquitous nodes.
def lo_a_line(graph, side=None):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty('viewLayout')
	view_layout.setAllEdgeValue([])

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
		s = root["viewSize"][n]
		max_h = max(max_h, s.getH())
		x, y, max_h = get_coord(s, x, y, max_h)
		view_layout[n] = tlp.Coord(x, y)
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
		return -180
	elif -157.5 <= alpha < -112.5:
		return -135
	elif -112.5 <= alpha < -67.5:
		return -90
	elif -67.5 <= alpha < -22.5:
		return -45


def show_reversibility(graph):
	root = graph.getRoot()
	reversible = root.getBooleanProperty("reversible")
	view_tgt_anchor_shape = root.getIntegerProperty("viewTgtAnchorShape")
	view_src_anchor_shape = root.getIntegerProperty("viewSrcAnchorShape")

	for n in (n for n in graph.getNodes() if 'reaction' == root['type'][n] and reversible[n]):
			for e in graph.getInEdges(n):
				view_tgt_anchor_shape[e] = -1
				view_src_anchor_shape[e] = 50
			for e in graph.getOutEdges(n):
				view_tgt_anchor_shape[e] = 50
				view_src_anchor_shape[e] = -1


def layout_generalization_based(graph, do_not_open=None, bundle_edges=False):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty("viewLayout")
	view_meta_graph = root.getGraphProperty("viewMetaGraph")
	view_size = root.getSizeProperty("viewSize")

	nds = []
	mn2color = {}
	for n in graph.getNodes():
		if graph.isMetaNode(n):
			mn2color[n] = root["viewColor"][n]
			mg = view_meta_graph[n]
			ns = list(mg.getNodes())
			nds.extend(ns)
		else:
			nds.append(n)
	for n in nds:
		root["viewBorderWidth"][n] = 0.1 * view_size[n].width()
		root["viewBorderColor"][n] = white
	clone = graph.getSuperGraph().inducedSubGraph(nds)
	clone.setName(graph.getName() + "_full")

	if do_not_open:
		for n in do_not_open:
			mg = view_meta_graph[n]
			mg_lo_min = view_layout.getMin(mg)
			n_lo, n_sz = view_layout[n], view_size[n]
			view_layout.translate(tlp.Coord(n_lo.getX() - n_sz.width() / 2 - mg_lo_min.getX() + n_sz.width() * 0.05,
			                                n_lo.getY() - n_sz.height() / 2 - mg_lo_min.getY() + n_sz.height() * 0.05),
			                      mg.getNodes(), mg.getEdges())

	vl = {}

	meta_ns = {n for n in graph.getNodes() if graph.isMetaNode(n) and (not do_not_open or not n in do_not_open)}
	meta_sps = {n for n in meta_ns if 'species' == root["type"][n]}
	meta_rs = meta_ns - meta_sps

	depends_on = {}
	our_sps = set()
	for s in meta_sps:
		rs = set(graph.getInOutNodes(s)) & meta_rs
		sps = set()
		for r in rs:
			sps |= set(graph.getInOutNodes(r)) & meta_sps
		depends_on[s] = sps - {s}
		our_sps |= set(view_meta_graph[s].getNodes())

	n2k = {}
	while meta_sps:
		n = min(meta_sps, key=lambda s: len(depends_on[s] & meta_sps))
		meta_sps -= {n}
		mg = view_meta_graph[n]
		for s in mg.getNodes():
			rs = clone.getInOutNodes(s)
			sps = set()
			for r in rs:
				sps |= set(clone.getInOutNodes(r)) & our_sps
			sps -= {s}
			n2k[s] = (root["id"][n], clone.deg(s), root["id"][s])
			for ss in sps:
				if ss in n2k:
					n2k[s] = n2k[ss]
	for n in meta_rs:
		mg = view_meta_graph[n]
		for r in mg.getNodes():
			n2k[r] = sorted(n2k[it] for it in set(clone.getInOutNodes(r)) & our_sps)

	for n in meta_ns:
		lo = view_layout[n]
		s = view_size[n].getW()
		mg = view_meta_graph[n]

		# add a fake node to keep a common background for similar nodes
		nn = clone.addNode()
		root["viewSize"][nn] = root["viewSize"][n]
		root["viewShape"][nn] = root["viewShape"][n]
		root["viewBorderWidth"][nn] = 0
		root["viewBorderColor"][nn] = root["viewBorderColor"][n]
		co = root["viewLayout"][n]
		root["viewLayout"][nn] = tlp.Coord(co.getX(), co.getY(), 0)
		root["viewColor"][nn] = mn2color[n]
		root["type"][nn] = 'background'

		meta_neighbours = lambda nodes: sorted([t for t in nodes if graph.isMetaNode(t)], key=lambda t: -view_size[t].getW())
		o_n_1 = meta_neighbours(graph.getInNodes(n))
		o_n_2 = meta_neighbours(graph.getOutNodes(n))
		if not o_n_1:
			alpha = get_alpha(lo, view_layout[o_n_2[0]]) if o_n_2 else 0
		elif not o_n_2:
			alpha = get_alpha(view_layout[o_n_1[0]], lo)
		else:
			alpha = get_alpha(view_layout[o_n_1[0]], view_layout[o_n_2[0]])
		# if alpha < 0:
		# 	alpha = - alpha
		vl[mg] = lo.getX(), lo.getY(), alpha


		ns = sorted(mg.getNodes(), key=lambda it: n2k[it])
		s_m = tlp.Size(s / len(ns), s / len(ns))
		if 'reaction' == root["type"][n] and (alpha == 45 or alpha == 135 or alpha == -45 or alpha == -135):
			s *= sqrt(2)
		dy = s / len(ns)
		x0, y0 = lo.getX(), lo.getY() - s / 2 + dy / 2
		x, y = x0, y0
		for m in ns:
			root["viewSize"][m] = s_m
			root["viewLayout"][m] = tlp.Coord(x, y)
			root["viewLayout"][m] = tlp.Coord(x, y)
			root["viewSize"][m] = s_m
			y += dy

		for o_n in filter(lambda t: root["ubiquitous"][t], graph.getInOutNodes(n)):
			lo_n = view_layout[o_n]
			alpha = atan2(lo_n.getY()-lo.getY(), lo_n.getX()-lo.getX())
			x0, y0 = lo.getX() + s * 0.7 * cos(alpha), lo.getY() + s * 0.7 * sin(alpha)
			for m in ns:
				for e in clone.getInOutEdges(m):
					if o_n == clone.target(e) or o_n == clone.source(e):
						root["viewLayout"][e] = [tlp.Coord(x0, y0)]

	for mg, (x0, y0, alpha) in vl.iteritems():
		view_layout.translate(tlp.Coord(-x0, -y0), mg)
		view_layout.rotateZ(-alpha, mg)
		view_layout.translate(tlp.Coord(x0, y0), mg)
		# for m in mg.getNodes():
		# 	clone.getRoot()["viewLayout"][m] = mg.getRoot()["viewLayout"][m]

	if do_not_open:
		for n in do_not_open:
			# add a fake node to keep a common background for similar nodes
			nn = clone.addNode()
			root["viewSize"][nn] = root["viewSize"][n]
			root["viewShape"][nn] = root["viewShape"][n]
			root["viewBorderWidth"][nn] = 0
			root["viewBorderColor"][nn] = root["viewBorderColor"][n]
			co = root["viewLayout"][n]
			root["viewLayout"][nn] = tlp.Coord(co.getX(), co.getY(), 0)
			root["viewColor"][nn] = mn2color[n]
			root["type"][nn] = 'background'

	show_reversibility(clone)
	show_reversibility(graph)

	# if bundle_edges:
	# 	try:
	# 		clone.applyAlgorithm("Edge bundling")
	# 	except:
	# 		pass

	return clone


# def get_corners(graph):
# 	root = graph.getRoot()
# 	layout = root.getLayoutProperty("viewLayout")
# 	size = graph.getRoot().getSizeProperty("viewSize")
# 	m = lambda l, s: (l.getX() - s.getW() / 2, l.getY() - s.getH() / 2)
# 	M = lambda l, s: (l.getX() + s.getW() / 2, l.getY() + s.getH() / 2)
# 	mM = lambda n: (m(layout[n], size[n]), M(layout[n], size[n]))
# 	(m_x, m_y), (M_x, M_y) = mM(graph.getNodes().next())
# 	for n in graph.getNodes():
# 		(m_x_, m_y_), (M_x_, M_y_) = mM(n)
# 		if m_x_ < m_x: m_x = m_x_
# 		if m_y_ < m_y: m_y = m_y_
# 		if M_x_ > M_x: M_x = M_x_
# 		if M_y_ > M_y: M_y = M_y_
# 	return (m_x, m_y), (M_x, M_y)