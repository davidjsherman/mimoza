from collections import defaultdict
from math import sqrt, radians, degrees, cos, sin, atan2
from tulip import tlp
from sbml_vis.tulip.graph_properties import UBIQUITOUS, VIEW_LAYOUT, VIEW_SIZE, TYPE_REACTION, TYPE, ID, COMPARTMENT, \
	TYPE_SPECIES, TYPE_COMPARTMENT, NAME, VIEW_META_GRAPH

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


def layout_ub_sps(graph, comp2node=None, comp2outs=None, filter_nd=lambda r: True):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty(VIEW_LAYOUT)
	view_size = root.getSizeProperty(VIEW_SIZE)

	comp2ns = defaultdict(list)
	for r in (n for n in graph.getNodes() if TYPE_REACTION == root[TYPE][n] and filter_nd(n)):
		r_x, r_y = view_layout[r].getX(), view_layout[r].getY()
		r_radius = view_size[r].getW() * sqrt(2) / 2
		r_comp_id = root[COMPARTMENT][r]
		# c = min(view_size[r].getW() * 1.8, 3.5)  # edge-after-bent length
		# todo: if it's actually a compartment, then
		# extract the species from it
		get_all = lambda rn, get_participants: {s for s in get_participants(rn) if TYPE_SPECIES == root[TYPE][s]}
		# print root[NAME][r]
		for (get_participants, get_reaction_edges, get_other_side_participants, direction) in [
			(graph.getInNodes, graph.getOutEdges, graph.getOutNodes, 1),
			(graph.getOutNodes, graph.getInEdges, graph.getInNodes, -1)]:

			ubiquitous_participants = sorted((nd for nd in get_all(r, get_participants) if ub_or_single(nd, root)),
			                                 key=lambda nd: root[ID][nd])
			# print "   ", [root[NAME][ub] for ub in ubiquitous_participants]
			if comp2node:
				for ub in ubiquitous_participants:
					comp2ns[root[COMPARTMENT][ub]].append(ub)
			ub_participants_len = len(ubiquitous_participants)
			if not ub_participants_len:
				continue
			if ub_participants_len % 2 == 1:
				ub_participants_len += 1
			size = max(root[VIEW_SIZE][nd].getW() for nd in ubiquitous_participants)
			edge_len = size * max(ub_participants_len / 2, 3)
			# edge_len = UBIQUITOUS_SPECIES_SIZE * max(ub_participants_len / 2, 3)

			specific_participants = filter(lambda nd: not ub_or_single(nd, root), get_all(r, get_participants))
			just_one = len(ubiquitous_participants) == 1 and not specific_participants
			if specific_participants:
				specific_participant_example = specific_participants[0]
				s_x, s_y = view_layout[specific_participant_example].getX(), view_layout[
					specific_participant_example].getY()
				species_size = view_size[specific_participant_example].getW() / 2
				edge_len = (sqrt(pow(r_x - s_x, 2) + pow(s_y - r_y, 2)) - r_radius - species_size)
			else:
				specific_participants = filter(lambda n: not ub_or_single(n, root), get_all(r, get_other_side_participants))
				if specific_participants:
					specific_participant_example = specific_participants[0]
					s_x, s_y = view_layout[specific_participant_example].getX(), view_layout[
						specific_participant_example].getY()
					s_x, s_y = r_x - (s_x - r_x), r_y - (s_y - r_y)
				else:
					s_x, s_y = r_x + view_size[r].getW() + size * ub_participants_len * direction, r_y
					if comp2node:
						comp_ids = {root[COMPARTMENT][s] for s in ubiquitous_participants} - {r_comp_id}
						comp_nd = next((comp2node[c_id] for c_id in comp_ids if c_id in comp2node), None)
						if comp_nd:
							s_x, s_y = view_layout[comp_nd].getX(), view_layout[comp_nd].getY()

			# beta is the max angle between the ubiquitous and the specific edges
			gap = 0 if just_one else 2 * min(100, max(60, ub_participants_len * 20))
			beta0 = radians(gap / 2)
			beta = beta0
			d_beta = radians(gap / (ub_participants_len - 1))

			# distance from reaction to the edge bent
			# bent = min(UBIQUITOUS_SPECIES_SIZE / 2, edge_len / 2)
			bent = min(size / 2, edge_len / 2)
			s0 = r_radius + bent
			s = s0
			# ds = min(2 * (edge_len - bent - UBIQUITOUS_SPECIES_SIZE / 2) / ub_participants_len, UBIQUITOUS_SPECIES_SIZE)
			ds = min(2 * (edge_len - bent - size / 2) / ub_participants_len, size)
			# s += ds * ub_participants_len / 2

			# angle between the horizontal line and the reaction-specific-species edge
			alpha = atan2(s_y - r_y, s_x - r_x)

			dc = 0
			towards_edge = -1
			for ub in ubiquitous_participants:
				# it is the only edge as ubiquitous species are duplicated
				e = get_reaction_edges(ub).next()
				x0, y0 = r_x + s * cos(alpha), r_y + s * sin(alpha)
				view_layout[e] = [tlp.Coord(x0, y0)]

				gamma = alpha + beta
				# edge-after-bent length
				# c = min(edge_len - s0 + dc + r_radius - UBIQUITOUS_SPECIES_SIZE, 2 * UBIQUITOUS_SPECIES_SIZE)
				c = min(edge_len - s0 + dc + r_radius - size, 2 * size)
				if comp2node and root[COMPARTMENT][ub] != r_comp_id:
					dx, dy = ub_layout_shift(root, (x0, y0), (c * cos(gamma), c * sin(gamma)), r_comp_id,
					                         root[COMPARTMENT][ub], comp2node, comp2outs)
					x0 += dx
					y0 += dy

				s_x, s_y = x0 + c * cos(gamma), y0 + c * sin(gamma)
				view_layout[ub] = tlp.Coord(s_x, s_y)
				# if degrees(beta) > 0:
				# s += ds
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
				# s -= ds
	# for c_id, ns in comp2ns.iteritems():
	# 	gr = root.inducedSubGraph(ns)
	# 	remove_overlaps(gr)
	# 	root.delAllSubGraphs(gr)
	# 	if c_id in comp2node:
	# 		for n in ns:
	# 			fit_into_compartment(n, comp2node[c_id], root)
	# 	for inner_c_id in (inner_c_id for inner_c_id in comp2outs.iterkeys() if
	# 	                   c_id in comp2outs[inner_c_id] and inner_c_id in comp2node):
	# 		for n in ns:
	# 			fit_out_of_compartment(n, comp2node[inner_c_id], root)


def ub_layout_shift(root, (u_x, u_y), (margin_x, margin_y), r_comp, ub_comp, comp2node, comp2outs):
	if r_comp == ub_comp:
		return 0, 0
	if r_comp in comp2outs and ub_comp in comp2outs[r_comp]:
		comp_n = comp2node[r_comp]
		n_x, n_y = root[VIEW_LAYOUT][comp_n].getX(), root[VIEW_LAYOUT][comp_n].getY()
		n_w, n_h = root[VIEW_LAYOUT][comp_n].getW() / 2, root[VIEW_LAYOUT][comp_n].getH() / 2
		x_bottom, x_top = n_x - n_w - margin_x, n_x + n_w + margin_x
		d_x_bottom, d_x_top = abs(u_x - x_bottom), abs(x_top - u_x)
		y_bottom, y_top = n_y - n_h - margin_y, n_y + n_h + margin_y
		d_y_bottom, d_y_top = abs(u_y - y_bottom), abs(y_top - u_y)
		x_diff, y_diff = min(d_x_bottom, d_x_top), min(d_y_bottom, d_y_top)
		if x_diff > y_diff:
			x = (x_bottom if d_x_bottom < d_x_top else x_top) - u_x
			return x, 0
		else:
			y = (y_bottom if d_y_bottom < d_y_top else y_top) - u_y
			return 0, y
	# todo: should it be inside-comp-relative position instead for ub?
	# elif ub_comp in comp2node:
	# 	comp_n = comp2node[ub_comp]
	# 	n_x, n_y = root[VIEW_LAYOUT][comp_n].getX(), root[VIEW_LAYOUT][comp_n].getY()
	# 	n_w, n_h = root[VIEW_LAYOUT][comp_n].getW() / 2, root[VIEW_LAYOUT][comp_n].getH() / 2
	# 	x_bottom, x_top = n_x - n_w + margin_x, n_x + n_w - margin_x
	# 	y_bottom, y_top = n_y - n_h + margin_y, n_y + n_h - margin_y
	# 	x, y = 0, 0
	# 	if x_bottom > u_x:
	# 		x = x_bottom - u_x
	# 	elif x_top < u_x:
	# 		x = x_top - u_x
	# 	if y_bottom > u_y:
	# 		y = y_bottom - u_y
	# 	elif y_top < u_y:
	# 		y = y_top - u_y
	# 	return x, y
	return 0, 0


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