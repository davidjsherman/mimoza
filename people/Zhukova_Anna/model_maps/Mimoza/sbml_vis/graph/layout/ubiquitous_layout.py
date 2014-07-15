from math import sqrt, radians, degrees, cos, sin, atan2
from tulip import tlp

from sbml_vis.graph.graph_properties import UBIQUITOUS, VIEW_LAYOUT, VIEW_SIZE, TYPE_REACTION, TYPE, ID, TYPE_SPECIES, \
	TYPE_COMPARTMENT, VIEW_META_GRAPH


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


def layout_outer_reactions(graph, filter_nd=lambda nd: True):
	root = graph.getRoot()

	def single(r):
		for s in (s for s in graph.getInOutNodes(r) if TYPE_SPECIES == root[TYPE][s]):
			if root.deg(s) > 1:
				return False
		return True

	for c in (c for c in graph.getNodes() if TYPE_COMPARTMENT == root[TYPE][c]):
		c_w, c_h = root[VIEW_SIZE][c].getW() / 2, root[VIEW_SIZE][c].getH() / 2
		c_x, c_y = root[VIEW_LAYOUT][c].getX(), root[VIEW_LAYOUT][c].getY()
		c_bottom_x, c_bottom_y = c_x - c_w, c_y - c_h
		c_top_x, c_top_y = c_x + c_w, c_y + c_h
		rs = [r for r in graph.getInOutNodes(c) if TYPE_REACTION == root[TYPE][r] and single(r) and filter_nd(r)]
		for r in rs:
			r_w, r_h = root[VIEW_SIZE][r].getW() * 3, root[VIEW_SIZE][r].getH() * 3
			ss = [s for s in root.getInOutNodes(r) if root[VIEW_META_GRAPH][c].isElement(s)]
			ss_not_ub = [s for s in ss if not ub_or_single(s, root[VIEW_META_GRAPH][c])]
			if ss_not_ub:
				ss = ss_not_ub
			s_x, s_y = sum(root[VIEW_LAYOUT][s].getX() for s in ss) / len(ss), sum(
				root[VIEW_LAYOUT][s].getY() for s in ss) / len(ss)
			x = c_bottom_x if s_x < c_w else c_top_x
			y = c_bottom_y if s_y < c_h else c_top_y

			if abs(c_bottom_x + s_x - x) < abs(c_bottom_y + s_y - y):
				r_x = c_bottom_x + s_x
				r_y = y - r_h if y == c_bottom_y else y + r_h
			else:
				r_y = c_bottom_y + s_y
				r_x = x - r_w if x == c_bottom_x else x + r_w
			root[VIEW_LAYOUT][r] = tlp.Coord(r_x, r_y)
		rs_graph = root.inducedSubGraph(rs)
		remove_overlaps(rs_graph)
		root.delAllSubGraphs(rs_graph)
		for r in rs:
			fit_into_compartment(r, c, root)


def fit_into_compartment(n, c, root):
	c_w, c_h = root[VIEW_SIZE][c].getW() / 2, root[VIEW_SIZE][c].getH() / 2
	c_x, c_y = root[VIEW_LAYOUT][c].getX(), root[VIEW_LAYOUT][c].getY()
	c_bottom_x, c_bottom_y = c_x - c_w, c_y - c_h
	c_top_x, c_top_y = c_x + c_w, c_y + c_h

	n_x, n_y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
	n_w, n_h = root[VIEW_SIZE][n].getW() / 2, root[VIEW_SIZE][n].getH() / 2
	n_x, n_y = min(max(n_x, c_bottom_x + n_w), c_top_x - n_w), min(max(n_y, c_bottom_y + n_h), c_top_y - n_h)
	root[VIEW_LAYOUT][n] = tlp.Coord(n_x, n_y)


def fit_out_of_compartment(n, c, root):
	c_w, c_h = root[VIEW_SIZE][c].getW() / 2, root[VIEW_SIZE][c].getH() / 2
	c_x, c_y = root[VIEW_LAYOUT][c].getX(), root[VIEW_LAYOUT][c].getY()
	c_bottom_x, c_bottom_y = c_x - c_w, c_y - c_h
	c_top_x, c_top_y = c_x + c_w, c_y + c_h

	n_x, n_y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
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


def bend_ubiquitous_edges(graph, nodes):
	root = graph.getRoot()
	for r in (r for r in nodes if TYPE_REACTION == root[TYPE][r]):
		r_lo = root[VIEW_LAYOUT][r]
		r_w = root[VIEW_SIZE][r].getW()
		for s in (s for s in graph.getInOutNodes(r) if root[UBIQUITOUS][s] or not graph.isMetaNode(s)):
			s_lo = root[VIEW_LAYOUT][s]
			alpha = atan2(s_lo.getY() - r_lo.getY(), s_lo.getX() - r_lo.getX())
			x0, y0 = r_lo.getX() + r_w * 0.7 * cos(alpha), r_lo.getY() + r_w * 0.7 * sin(alpha)
			for m in root[VIEW_META_GRAPH][r].getNodes():
				for e in root.getInOutEdges(m):
					if s == root.target(e) or s == root.source(e):
						root[VIEW_LAYOUT][e] = [tlp.Coord(x0, y0)]


def layout_ub_reaction(r_graph, r):
	root = r_graph.getRoot()
	view_layout = root[VIEW_LAYOUT]
	view_size = root[VIEW_SIZE]

	r_x, r_y = view_layout[r].getX(), view_layout[r].getY()
	r_radius = view_size[r].getW() * sqrt(2) / 2
	for (participants, direction) in [(r_graph.getInNodes(r), 1), (r_graph.getOutNodes(r), -1)]:
		participants = sorted(participants, key=lambda nd: root[ID][nd])
		participants_len = len(participants)
		if not participants_len:
			continue
		if participants_len % 2 == 1:
			participants_len += 1
		max_participant_w = max(root[VIEW_SIZE][nd].getW() for nd in participants)

		edge_len = r_radius + max_participant_w * (participants_len / 2)

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
			# it is the only edge as ubiquitous species are duplicated
			e = r_graph.getInOutEdges(ub).next()
			view_layout[e] = [tlp.Coord(x0, y0)]
			if r_graph.isMetaEdge(e):
				for inner_e in root[VIEW_META_GRAPH][e]:
					view_layout[inner_e] = [tlp.Coord(x0, y0)]

			end_x, end_y = x0 + from_edge_bend_till_end_current * direction * cos(angle), y0 + from_edge_bend_till_end_current * direction * sin(
				angle)
			view_layout[ub] = tlp.Coord(end_x, end_y)

			if degrees(angle) * degrees(angle + towards_edge * d_angle) < 0:
				angle = -angle_top
				from_edge_bend_till_end_current = min(max_participant_w / 2 + r_radius, from_edge_bend_till_end)
				towards_edge = 1
			else:
				angle += towards_edge * d_angle
				from_edge_bend_till_end_current += d_edge