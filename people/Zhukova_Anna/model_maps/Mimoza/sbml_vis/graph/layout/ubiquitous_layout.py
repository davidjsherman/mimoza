from math import sqrt, radians, degrees, cos, sin, atan2
from tulip import tlp
from sbml_vis.graph.resize import get_n_size

from sbml_vis.graph.graph_properties import UBIQUITOUS, VIEW_LAYOUT, VIEW_SIZE, TYPE_REACTION, TYPE, ID, TYPE_SPECIES, \
	TYPE_COMPARTMENT, VIEW_META_GRAPH, NAME, FAKE, STOICHIOMETRY, COMPARTMENT_ID, VIEW_SHAPE, TERM, MAX_ZOOM, \
	MIN_ZOOM, TRANSPORT, REVERSIBLE, CIRCLE_SHAPE


OVERLAP_REMOVAL = "Fast Overlap Removal"

__author__ = 'anna'


def remove_overlaps(graph, margin=1):
	root = graph.getRoot()
	ds = tlp.getDefaultPluginParameters(OVERLAP_REMOVAL, graph)
	ds["x border"] = margin
	ds["y border"] = margin
	graph.computeLayoutProperty(OVERLAP_REMOVAL, root[VIEW_LAYOUT], ds)


def ub_or_single(nd, graph):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	return (ubiquitous[nd] or 1 == graph.deg(nd)) and TYPE_SPECIES == root[TYPE][nd]


def layout_outer_elements(graph):
	root = graph.getRoot()

	comps = [c for c in graph.getNodes() if TYPE_COMPARTMENT == root[TYPE][c]]
	for c in comps:
		c_w, c_h = root[VIEW_SIZE][c].getW() / 2, root[VIEW_SIZE][c].getH() / 2
		c_x, c_y = root[VIEW_LAYOUT][c].getX(), root[VIEW_LAYOUT][c].getY()
		c_bottom_x, c_bottom_y = c_x - c_w, c_y - c_h
		c_top_x, c_top_y = c_x + c_w, c_y + c_h
		rs = [r for r in graph.getInOutNodes(c) if graph.deg(r) == 1]
		comp_mg = root[VIEW_META_GRAPH][c]
		for r in rs:
			r_w, r_h = root[VIEW_SIZE][r].getW() * 3, root[VIEW_SIZE][r].getH() * 3
			ss = [s for s in root.getInOutNodes(r) if comp_mg.isElement(s)]
			if not ss and root.isMetaNode(r):
				for rr in root[VIEW_META_GRAPH][r].getNodes():
					ss.extend([s for s in root.getInOutNodes(rr) if comp_mg.isElement(s)])
			ss_not_ub = [s for s in ss if not ub_or_single(s, comp_mg)]
			if ss_not_ub:
				ss = ss_not_ub
			m_x = min(root[VIEW_LAYOUT][s].getX() - root[VIEW_SIZE][s].getW() / 2 for s in comp_mg.getNodes())
			m_y = min(root[VIEW_LAYOUT][s].getY() - root[VIEW_SIZE][s].getH() / 2 for s in comp_mg.getNodes())
			s_x, s_y = sum(root[VIEW_LAYOUT][s].getX() - m_x for s in ss) / len(ss), sum(
				root[VIEW_LAYOUT][s].getY() - m_y for s in ss) / len(ss)
			x = c_bottom_x - r_w if s_x < c_w else c_top_x + r_h
			y = c_bottom_y - r_h if s_y < c_h else c_top_y + r_h

			if abs(c_bottom_x + s_x - x) > abs(c_bottom_y + s_y - y):
				r_x = c_bottom_x + s_x
				r_y = y
			else:
				r_y = c_bottom_y + s_y
				r_x = x
			root[VIEW_LAYOUT][r] = tlp.Coord(r_x, r_y)
		rs_graph = root.inducedSubGraph(rs)
		remove_overlaps(rs_graph)
		root.delAllSubGraphs(rs_graph)


def open_compartment(c, graph):
	root = graph.getRoot()
	prop2value = {prop: root[prop][c] for prop in
	              [NAME, COMPARTMENT_ID, TYPE, VIEW_SHAPE, ID, TERM, VIEW_SIZE, MAX_ZOOM, MIN_ZOOM]}
	graph.openMetaNode(c)
	return prop2value


def close_compartment(comp_mg, graph, prop2value):
	root = graph.getRoot()

	new_c = graph.createMetaNode(comp_mg, False)
	for prop, value in prop2value.iteritems():
		root[prop][new_c] = value
	for meta_e in root.getInOutEdges(new_c):
		sample_e = next(e for e in root[VIEW_META_GRAPH][meta_e])
		root[UBIQUITOUS][meta_e] = root[UBIQUITOUS][sample_e]
		root[STOICHIOMETRY][meta_e] = root[STOICHIOMETRY][sample_e]
	return new_c


def layout_inner_elements(graph):
	root = graph.getRoot()

	comps = [c for c in graph.getNodes() if TYPE_COMPARTMENT == root[TYPE][c]]
	for c in comps:
		c_w, c_h = root[VIEW_SIZE][c].getW() / 2, root[VIEW_SIZE][c].getH() / 2
		c_x, c_y = root[VIEW_LAYOUT][c].getX(), root[VIEW_LAYOUT][c].getY()
		c_bottom_x, c_bottom_y = c_x - c_w, c_y - c_h
		c_top_x, c_top_y = c_x + c_w, c_y + c_h
		comp_mg = root[VIEW_META_GRAPH][c]
		prop2value = open_compartment(c, graph)

		create_fake_rs(comp_mg)

		def get_neighbour_nodes(r):
			result = [s for s in root.getInOutNodes(r) if graph.isElement(s)]
			if root[FAKE][r]:
				for inner_r in root[VIEW_META_GRAPH][r].getNodes():
					result.extend([s for s in root.getInOutNodes(inner_r) if graph.isElement(s)])
			return result

		rs = [r for r in comp_mg.getNodes() if comp_mg.deg(r) == 0]
		for r in rs:
			r_w, r_h = root[VIEW_SIZE][r].getW() * 3, root[VIEW_SIZE][r].getH() * 3
			ss = get_neighbour_nodes(r)
			if not ss:
				continue
			ss_not_ub = [s for s in ss if not ub_or_single(s, graph)]
			if ss_not_ub:
				ss = ss_not_ub
			s_x, s_y = sum(root[VIEW_LAYOUT][s].getX() for s in ss) / len(ss), sum(
				root[VIEW_LAYOUT][s].getY() for s in ss) / len(ss)

			if min(abs(s_x - c_bottom_x), abs(s_x - c_top_x)) > min(abs(s_y - c_bottom_y), abs(s_y - c_top_y)):
				r_x = s_x
				r_y = c_bottom_y - r_h if abs(s_y - c_bottom_y) < abs(s_y - c_top_y) else c_top_y + r_h
			else:
				r_y = s_y
				r_x = c_bottom_x - r_w if abs(s_x - c_bottom_x) < abs(s_x - c_top_x) else c_top_x + r_w
			root[VIEW_LAYOUT][r] = tlp.Coord(r_x, r_y)
		rs_graph = root.inducedSubGraph(rs)
		remove_overlaps(rs_graph)
		root.delAllSubGraphs(rs_graph)

		for r in rs:
			fit_into_rectangle(c_h, c_w, c_x, c_y, r, root)

		# rotate_fake_ns(comp_mg)
		open_meta_ns(comp_mg, (r for r in comp_mg.getNodes() if root[FAKE][r]))

		close_compartment(comp_mg, graph, prop2value)


def fit_into_rectangle(c_h, c_w, c_x, c_y, n, root):
	c_bottom_x, c_bottom_y = c_x - c_w, c_y - c_h
	c_top_x, c_top_y = c_x + c_w, c_y + c_h
	old_x, old_y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
	n_x, n_y = old_x, old_y
	n_w, n_h = root[VIEW_SIZE][n].getW() / 2, root[VIEW_SIZE][n].getH() / 2
	n_x, n_y = min(max(n_x, c_bottom_x + n_w), c_top_x - n_w), min(max(n_y, c_bottom_y + n_h), c_top_y - n_h)
	root[VIEW_LAYOUT][n] = tlp.Coord(n_x, n_y)
	shift_edges(n, root)


def shift_edges(n, root):
	nodes = [n]
	mg = None
	if root[FAKE][n]:
		mg = root[VIEW_META_GRAPH][n]
		nodes.extend(list(mg.getNodes()))
	for nd in nodes:
		for e in (e for e in root.getInOutEdges(nd) if not mg or not mg.isElement(e)):
			root[VIEW_LAYOUT][e] = []


def fit_out_of_compartment(n, c, root):
	c_w, c_h = root[VIEW_SIZE][c].getW() / 2, root[VIEW_SIZE][c].getH() / 2
	c_x, c_y = root[VIEW_LAYOUT][c].getX(), root[VIEW_LAYOUT][c].getY()
	c_bottom_x, c_bottom_y = c_x - c_w, c_y - c_h
	c_top_x, c_top_y = c_x + c_w, c_y + c_h

	old_x, old_y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
	n_x, n_y = old_x, old_y
	n_w, n_h = root[VIEW_SIZE][n].getW() / 2, root[VIEW_SIZE][n].getH() / 2

	c_bottom_x -= n_w
	c_top_x += n_w
	c_bottom_y -= n_h
	c_top_y += n_h
	if c_bottom_x < n_x < c_top_x and c_bottom_y < n_y < c_top_y:
		if min(n_x - c_bottom_x, c_top_x - n_x) < min(n_y - c_bottom_y, c_top_y - n_y):
			n_x = c_bottom_x if n_x - c_bottom_x < c_top_x - n_x else c_top_x
		else:
			n_y = c_bottom_y if n_y - c_bottom_y < c_top_y - n_y else c_top_y
	root[VIEW_LAYOUT][n] = tlp.Coord(n_x, n_y)
	shift_edges(n, root)


def get_reaction_r(r, root):
	return sqrt(pow(root[VIEW_SIZE][r].getW(), 2) + pow(root[VIEW_SIZE][r].getH(), 2)) / 2


def bend_ubiquitous_edges(graph, nodes):
	root = graph.getRoot()
	for r in (r for r in nodes if TYPE_REACTION == root[TYPE][r]):
		r_lo = root[VIEW_LAYOUT][r]
		r_r = get_reaction_r(r, root) * 1.5
		for s in (s for s in graph.getInOutNodes(r) if root[UBIQUITOUS][s] or not graph.isMetaNode(s)):
			s_lo = root[VIEW_LAYOUT][s]
			alpha = atan2(s_lo.getY() - r_lo.getY(), s_lo.getX() - r_lo.getX())
			x0, y0 = r_lo.getX() + r_r * cos(alpha), r_lo.getY() + r_r * sin(alpha)
			for m in root[VIEW_META_GRAPH][r].getNodes():
				for e in root.getInOutEdges(m):
					if s == root.target(e) or s == root.source(e):
						root[VIEW_LAYOUT][e] = [tlp.Coord(x0, y0)]


def bend_edges(graph):
	root = graph.getRoot()
	for r in (r for r in graph.getNodes() if TYPE_REACTION == root[TYPE][r]):
		r_x, r_y = root[VIEW_LAYOUT][r].getX(), root[VIEW_LAYOUT][r].getY()
		r_r = get_reaction_r(r, root) * 2
		reactants, products = list(graph.getInNodes(r)), list(graph.getOutNodes(r))

		def get_bend_coord(species):
			sample_species = next((s for s in species if not ub_or_single(s, graph)), None)
			if sample_species:
				s_x, s_y = root[VIEW_LAYOUT][sample_species].getX(), root[VIEW_LAYOUT][sample_species].getY()
			else:
				cs_x, cs_y = [root[VIEW_LAYOUT][s].getX() for s in species], \
				             [root[VIEW_LAYOUT][s].getY() for s in species]
				s_x, s_y = (min(cs_x) + max(cs_x)) / 2, (min(cs_y) + max(cs_y)) / 2
			r_species_angle = atan2(s_y - r_y, s_x - r_x)
			return tlp.Coord(r_x + r_r * cos(r_species_angle), r_y + r_r * sin(r_species_angle)), sample_species

		if len(products) > 1:
			product_lo, sample_product = get_bend_coord(products)
			for e in graph.getOutEdges(r):
				# if graph.target(e) != sample_product:
					root[VIEW_LAYOUT][e] = [product_lo] + root[VIEW_LAYOUT][e]

		if len(reactants) > 1:
			reactant_lo, sample_reactant = get_bend_coord(reactants)
			for e in graph.getInEdges(r):
				# if graph.source(e) != sample_reactant:
					root[VIEW_LAYOUT][e] = root[VIEW_LAYOUT][e] + [reactant_lo]


def layout_ub_reaction(r_graph, r):
	root = r_graph.getRoot()
	view_layout = root[VIEW_LAYOUT]
	view_size = root[VIEW_SIZE]

	nodes_of_interest = set(r_graph.getNodes())
	if r in nodes_of_interest:
		r_x, r_y = view_layout[r].getX(), view_layout[r].getY()
		r_radius = view_size[r].getW() * sqrt(2) / 2
		for (participants, direction) in [(root.getInNodes(r), 1), (root.getOutNodes(r), -1)]:
			participants = sorted(set(participants) & nodes_of_interest, key=lambda nd: root[ID][nd])
			participants_len = len(participants)
			if not participants_len:
				continue
			if participants_len % 2 == 1:
				participants_len += 1
			max_participant_w = max(root[VIEW_SIZE][nd].getW() for nd in participants)

			edge_len = r_radius + max_participant_w * (participants_len / 2) * 0.7

			angle_from_top_to_bottom = 2 * min(100, max(60, participants_len * 20))
			d_angle = radians(angle_from_top_to_bottom / (participants_len - 1))
			angle_top = radians(angle_from_top_to_bottom / 2)
			angle = angle_top

			from_r_centre_till_edge_bend = r_radius + max_participant_w / 2
			# edge-after-bend length
			from_edge_bend_till_end = edge_len - from_r_centre_till_edge_bend
			from_edge_bend_till_end_current = min(max_participant_w / 2 + r_radius, from_edge_bend_till_end)
			d_edge = (from_edge_bend_till_end - from_edge_bend_till_end_current) / (participants_len / 2)

			towards_edge = -1
			x0, y0 = r_x + (r_radius + from_r_centre_till_edge_bend) * direction, r_y
			for ub in participants:
				e = next(r_graph.getInOutEdges(ub), None)
				if not e:
					continue
				# it is the only edge as ubiquitous species are duplicated
				# view_layout[e] = [tlp.Coord(x0, y0)]
				if r_graph.isMetaEdge(e):
					for inner_e in root[VIEW_META_GRAPH][e]:
						view_layout[inner_e] = [tlp.Coord(x0, y0)]

				end_x, end_y = x0 + from_edge_bend_till_end_current * direction * cos(
					angle), y0 + from_edge_bend_till_end_current * direction * sin(
					angle)
				view_layout[ub] = tlp.Coord(end_x, end_y)

				if degrees(angle) * degrees(angle + towards_edge * d_angle) < 0:
					angle = -angle_top
					from_edge_bend_till_end_current = min(max_participant_w / 2 + r_radius, from_edge_bend_till_end)
					towards_edge = 1
				else:
					angle += towards_edge * d_angle
					from_edge_bend_till_end_current += d_edge
	else:
		x, y = 0, 0
		for m in sorted(nodes_of_interest, key=lambda nd: (root.isElement(root.existEdge(nd, r, True)), root[ID][nd])):
			m_h = root[VIEW_SIZE][m].getH() / 2
			y += m_h
			root[VIEW_LAYOUT][m] = tlp.Coord(x, y)
			y += m_h


def create_fake_rs(meta_graph):
	root = meta_graph.getRoot()
	r_ns = [r for r in root.getNodes() if TYPE_REACTION == root[TYPE][r]]
	for r in r_ns:
		r_n = r_to_meta_node(meta_graph, r)
		if r_n:
			mg = root[VIEW_META_GRAPH][r_n]
			root[MAX_ZOOM][r_n] = max(root[MAX_ZOOM][n] for n in mg.getNodes())
			root[MIN_ZOOM][r_n] = min(root[MIN_ZOOM][n] for n in mg.getNodes())


def r_to_meta_node(meta_graph, r):
	root = meta_graph.getRoot()

	ubs = []
	for s in root.getInOutNodes(r):
		if ub_or_single(s, root) and meta_graph.isElement(s):
			ubs.append(s)

	if meta_graph.isElement(r):
		ubs.append(r)

	if len(ubs) <= 1:
		return None

	r_n = meta_graph.createMetaNode(ubs, False)
	r_graph = root[VIEW_META_GRAPH][r_n]
	# layout_hierarchically(r_graph)
	layout_ub_reaction(r_graph, r)

	for prop in [NAME, ID, TYPE, TERM, TRANSPORT, REVERSIBLE]:
		root[prop][r_n] = root[prop][r]

	root[COMPARTMENT_ID][r_n] = root[COMPARTMENT_ID][ubs[0]]

	root[FAKE][r_n] = True
	root[VIEW_SHAPE][r_n] = CIRCLE_SHAPE

	root[VIEW_SIZE][r_n] = get_n_size(meta_graph, r_n)

	return r_n


def open_meta_ns(meta_graph, ns):
	root = meta_graph.getRoot()
	for n in sorted(ns, key=lambda mn: -root[VIEW_META_GRAPH][mn].getId()):
		inner_ns = root[VIEW_META_GRAPH][n].getNodes()
		meta_graph.openMetaNode(n)
		for inner_n in inner_ns:
			root[VIEW_SIZE][inner_n] = get_n_size(meta_graph, inner_n)