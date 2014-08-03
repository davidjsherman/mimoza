from math import sqrt, radians, degrees, cos, sin, atan2
from tulip import tlp

from sbml_vis.graph.resize import get_n_size, UBIQUITOUS_SPECIES_SIZE, REACTION_SIZE
from sbml_vis.graph.graph_properties import UBIQUITOUS, VIEW_LAYOUT, VIEW_SIZE, TYPE_REACTION, TYPE, ID, TYPE_SPECIES, \
	TYPE_COMPARTMENT, VIEW_META_GRAPH, NAME, FAKE, COMPARTMENT_ID, VIEW_SHAPE, TERM,\
	TRANSPORT, REVERSIBLE, CIRCLE_SHAPE


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
		c_bottom_x, c_bottom_y, c_top_x, c_top_y = get_comp_borders(c, root)
		c_w, c_h = (c_top_x - c_bottom_x) / 2, (c_top_y - c_bottom_y) / 2
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


def get_comp_borders(c, root):
	c_w, c_h = root[VIEW_SIZE][c].getW() / 2, root[VIEW_SIZE][c].getH() / 2
	c_x, c_y = root[VIEW_LAYOUT][c].getX(), root[VIEW_LAYOUT][c].getY()
	return c_x - c_w, c_y - c_h, c_x + c_w, c_y + c_h


def layout_inner_elements(graph, c_id, (c_bottom_x, c_bottom_y, c_top_x, c_top_y)):
	root = graph.getRoot()

	neighbours_outside_comp = lambda r: [n for n in graph.getInOutNodes(r) if root[COMPARTMENT_ID][n] != c_id]
	neighbours_inside_comp = lambda r: [n for n in graph.getInOutNodes(r) if root[COMPARTMENT_ID][n] == c_id]

	rs = [r for r in graph.getNodes() if root[TYPE][r] == TYPE_REACTION
	      and not next((n for n in neighbours_inside_comp(r) if not ub_or_single(n, root)), None)
	      and (c_id != root[COMPARTMENT_ID][r] or neighbours_outside_comp(r))]
	create_fake_rs(graph, c_id, rs, False)

	rs = [r for r in graph.getNodes() if root[COMPARTMENT_ID][r] == c_id and not neighbours_inside_comp(r)
	      and neighbours_outside_comp(r)]

	coords = set()
	for r in rs:
		r_w, r_h = root[VIEW_SIZE][r].getW(), root[VIEW_SIZE][r].getH()
		ss = neighbours_outside_comp(r)
		ss_not_ub = [s for s in ss if not ub_or_single(s, graph)]
		if ss_not_ub:
			ss = ss_not_ub
		s_x, s_y = sum(root[VIEW_LAYOUT][s].getX() for s in ss) / len(ss), sum(
			root[VIEW_LAYOUT][s].getY() for s in ss) / len(ss)

		inside_y = c_bottom_y + r_h <= s_y <= c_top_y - r_h
		inside_x = c_bottom_x + r_w <= s_x <= c_top_x - r_w

		if inside_x:
			r_x = s_x
			i = 1
			while True:
				r_y = c_bottom_y + i * r_h if abs(s_y - c_bottom_y) < abs(s_y - c_top_y) else c_top_y - i * r_h
				if (r_x, r_y) in coords:
					i += 1
				else:
					coords.add((r_x, r_y))
					break
		elif inside_y:
			r_y = s_y
			i = 1
			while True:
				r_x = c_bottom_x + i * r_w if abs(s_x - c_bottom_x) < abs(s_x - c_top_x) else c_top_x - i * r_w
				if (r_x, r_y) in coords:
					i += 1
				else:
					coords.add((r_x, r_y))
					break
		else:
			i = 1
			while True:
				r_x = max(c_bottom_x + i * r_w, min(s_x, c_top_x - i * r_w))
				r_y = max(c_bottom_y + i * r_h, min(s_y, c_top_y - i * r_h))
				if (r_x, r_y) in coords:
					i += 1
				else:
					coords.add((r_x, r_y))
					break

		root[VIEW_LAYOUT][r] = tlp.Coord(r_x, r_y)

	open_meta_ns(graph, (r for r in graph.getNodes() if root[FAKE][r]))
	root[VIEW_LAYOUT].setAllEdgeValue([])


def get_reaction_r(r, root):
	return sqrt(pow(root[VIEW_SIZE][r].getW(), 2) + pow(root[VIEW_SIZE][r].getH(), 2)) / 2


def bend_ubiquitous_edges(graph, nodes):
	root = graph.getRoot()
	for r in (r for r in nodes if TYPE_REACTION == root[TYPE][r]):
		r_x, r_y = root[VIEW_LAYOUT][r].getX(), root[VIEW_LAYOUT][r].getY()
		# r_r = get_reaction_r(r, root) + UBIQUITOUS_SPECIES_SIZE
		r_r = REACTION_SIZE * sqrt(2) / 2 + UBIQUITOUS_SPECIES_SIZE
		for s in (s for s in graph.getInOutNodes(r) if root[UBIQUITOUS][s] or not graph.isMetaNode(s)):
			s_x, s_y = root[VIEW_LAYOUT][s].getX(), root[VIEW_LAYOUT][s].getY()
			alpha = atan2(s_y - r_y, s_x - r_x)
			x0, y0 = r_x + r_r * cos(alpha), r_y + r_r * sin(alpha)
			for m in root[VIEW_META_GRAPH][r].getNodes():
				for e in root.getInOutEdges(m):
					if s == root.target(e) or s == root.source(e):
						root[VIEW_LAYOUT][e] = [tlp.Coord(x0, y0)]


def bend_edges(graph):
	root = graph.getRoot()
	for r in (r for r in graph.getNodes() if TYPE_REACTION == root[TYPE][r]):
		r_x, r_y = root[VIEW_LAYOUT][r].getX(), root[VIEW_LAYOUT][r].getY()
		r_r = get_reaction_r(r, root) + UBIQUITOUS_SPECIES_SIZE / 2
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
			return tlp.Coord(r_x + r_r * cos(r_species_angle), r_y + r_r * sin(r_species_angle))

		if len(products) > 1:
			product_lo = get_bend_coord(products)
			for e in graph.getOutEdges(r):
				root[VIEW_LAYOUT][e] = [product_lo] + root[VIEW_LAYOUT][e]

		if len(reactants) > 1:
			reactant_lo = get_bend_coord(reactants)
			for e in graph.getInEdges(r):
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
			even_num_of_participants = participants_len % 2 == 1
			if even_num_of_participants:
				participants_len += 1

			angle_from_top_to_bottom = 2 * min(90, max(40, participants_len * 20))
			d_angle = radians(angle_from_top_to_bottom / (participants_len - 1))
			angle_top = radians(angle_from_top_to_bottom / 2)
			towards_edge = -1

			angle = angle_top

			for ub in participants:
				edge = (r_radius + root[VIEW_SIZE][ub].getW() * 1.5) * direction
				end_x = r_x + edge * cos(angle)
				end_y = r_y + edge * sin(angle)
				view_layout[ub] = tlp.Coord(end_x, end_y)

				if degrees(angle) * degrees(angle + towards_edge * d_angle) < 0:
					angle = -angle_top
					towards_edge = 1
					if even_num_of_participants:
						angle += towards_edge * d_angle
				else:
					angle += towards_edge * d_angle
	else:
		x, y = 0, 0
		for m in sorted(nodes_of_interest, key=lambda nd: (root.isElement(root.existEdge(nd, r, True)), root[ID][nd])):
			m_h = root[VIEW_SIZE][m].getH() / 2
			y += m_h
			root[VIEW_LAYOUT][m] = tlp.Coord(x, y)
			y += m_h


def create_fake_rs(meta_graph, c_id=None, r_ns=None, do_lo=True):
	root = meta_graph.getRoot()
	if r_ns is None:
		r_ns = [r for r in root.getNodes() if TYPE_REACTION == root[TYPE][r]]
	for r in r_ns:
		r_to_meta_node(meta_graph, r, c_id, do_lo)


def r_to_meta_node(meta_graph, r, c_id, do_lo):
	root = meta_graph.getRoot()

	ubs = []
	for s in root.getInOutNodes(r):
		if ub_or_single(s, root) and meta_graph.isElement(s) and (not c_id or root[COMPARTMENT_ID][s] == c_id):
			ubs.append(s)

	if meta_graph.isElement(r) and (not c_id or root[COMPARTMENT_ID][r] == c_id):
		ubs.append(r)

	if len(ubs) <= 1:
		return None

	r_n = meta_graph.createMetaNode(ubs, False)
	r_graph = root[VIEW_META_GRAPH][r_n]
	# layout_hierarchically(r_graph)
	if do_lo:
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