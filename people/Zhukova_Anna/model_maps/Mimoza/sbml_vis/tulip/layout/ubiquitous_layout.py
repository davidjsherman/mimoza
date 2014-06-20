from math import sqrt, radians, degrees, cos, sin, atan2
from tulip import tlp
from sbml_vis.tulip.graph_properties import UBIQUITOUS, VIEW_LAYOUT, VIEW_SIZE, TYPE_REACTION, TYPE, ID, COMPARTMENT, TYPE_SPECIES

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


def layout_ub_sps(graph, comp2node=None, comp2out=None):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty(VIEW_LAYOUT)
	view_size = root.getSizeProperty(VIEW_SIZE)

	ns = []
	for r in (n for n in graph.getNodes() if TYPE_REACTION == root[TYPE][n]):
		r_x, r_y = view_layout[r].getX(), view_layout[r].getY()
		r_radius = view_size[r].getW() * sqrt(2) / 2
		# c = min(view_size[r].getW() * 1.8, 3.5)  # edge-after-bent length
		for (get_participants, get_reaction_edges, get_other_side_participants, direction) in [
			(graph.getInNodes, graph.getOutEdges, graph.getOutNodes, 1),
			(graph.getOutNodes, graph.getInEdges, graph.getInNodes, -1)]:

			ubiquitous_participants = sorted((nd for nd in get_participants(r) if ub_or_single(nd, graph)),
			                                 key=lambda nd: root[ID][nd])
			ns.extend(ubiquitous_participants)
			ub_participants_len = len(ubiquitous_participants)
			if not ub_participants_len:
				continue
			if ub_participants_len % 2 == 1:
				ub_participants_len += 1
			size = max(root[VIEW_SIZE][nd].getW() for nd in ubiquitous_participants)
			edge_len = size * max(ub_participants_len / 2, 3)
			# edge_len = UBIQUITOUS_SPECIES_SIZE * max(ub_participants_len / 2, 3)

			specific_participants = filter(lambda nd: not ub_or_single(nd, graph), get_participants(r))
			just_one = len(ubiquitous_participants) == 1 and not specific_participants
			if specific_participants:
				specific_participant_example = specific_participants[0]
				s_x, s_y = view_layout[specific_participant_example].getX(), view_layout[specific_participant_example].getY()
				species_size = view_size[specific_participant_example].getW() / 2
				edge_len = (sqrt(pow(r_x - s_x, 2) + pow(s_y - r_y, 2)) - r_radius - species_size)
			else:
				specific_participants = filter(lambda n: not ub_or_single(n, graph), get_other_side_participants(r))
				if specific_participants:
					specific_participant_example = specific_participants[0]
					s_x, s_y = view_layout[specific_participant_example].getX(), view_layout[
						specific_participant_example].getY()
					s_x, s_y = r_x - (s_x - r_x), r_y - (s_y - r_y)
				else:
					# s_x, s_y = r_x + view_size[r].getW() + UBIQUITOUS_SPECIES_SIZE * ub_participants_len * direction, r_y
					s_x, s_y = r_x + view_size[r].getW() + size * ub_participants_len * direction, r_y

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
				if comp2node:
					dx, dy = ub_layout_shift(root, (x0, y0), (c * cos(gamma), c * sin(gamma)), root[COMPARTMENT][r], root[COMPARTMENT][ub], comp2node, comp2out)
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
	remove_overlaps(root.inducedSubGraph(ns))



def ub_layout_shift(root, (u_x, u_y), (margin_x, margin_y), cur_comp, other_comp, comp2node, comp2out):
	if cur_comp == other_comp:
		return 0, 0
	# _, _, (_, out_c_id) = c_id2info[c_id]
	if cur_comp in comp2out and other_comp == comp2out[cur_comp][2][1]:
		n = comp2node[cur_comp]
		n_x, n_y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
		n_w, n_h = root[VIEW_LAYOUT][n].getW() / 2, root[VIEW_LAYOUT][n].getH() / 2
		x_bottom, x_top = n_x - n_w - margin_x, n_x + n_w + margin_x
		x_bottom, x_top = u_x - x_bottom, x_top - u_x
		y_bottom, y_top = n_y - n_h - margin_y, n_y + n_h + margin_y
		y_bottom, y_top = u_y - y_bottom, y_top - u_y
		x_diff, y_diff = min(x_bottom, x_top), min(y_bottom, y_top)
		if x_diff > y_diff:
			x = -x_bottom if x_bottom < x_top else x_top
			return x, 0
		else:
			y = -y_bottom if y_bottom < y_top else y_top
			return 0, y
	else:
		n = comp2node[other_comp]
		n_x, n_y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
		n_w, n_h = root[VIEW_LAYOUT][n].getW() / 2, root[VIEW_LAYOUT][n].getH() / 2
		x_bottom, x_top = n_x - n_w + margin_x, n_x + n_w - margin_x
		y_bottom, y_top = n_y - n_h + margin_y, n_y + n_h - margin_y
		x, y = 0, 0
		if x_bottom > u_x:
			x = x_bottom - u_x
		elif x_top < u_x:
			x = x_top - u_x
		if y_bottom > u_y:
			y = y_bottom - u_y
		elif y_top < u_y:
			y = y_top - u_y
		return x, y


def bend_ubiquitous_edges(graph, nodes, node2graph):
	root = graph.getRoot()
	for r in (r for r in nodes if TYPE_REACTION == root[TYPE][r]):
		r_lo = root[VIEW_LAYOUT][r]
		r_w = root[VIEW_SIZE][r].getW()
		for s in (s for s in graph.getInOutNodes(r) if root[UBIQUITOUS][s] or not s in node2graph):
			s_lo = root[VIEW_LAYOUT][s]
			alpha = atan2(s_lo.getY() - r_lo.getY(), s_lo.getX() - r_lo.getX())
			x0, y0 = r_lo.getX() + r_w * 0.7 * cos(alpha), r_lo.getY() + r_w * 0.7 * sin(alpha)
			for m in node2graph[r].getNodes():
				for e in root.getInOutEdges(m):
					if s == root.target(e) or s == root.source(e):
						root[VIEW_LAYOUT][e] = [tlp.Coord(x0, y0)]