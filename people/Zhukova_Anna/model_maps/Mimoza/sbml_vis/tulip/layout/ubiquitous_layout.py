from math import sqrt, radians, degrees, cos, sin, atan2
from tulip import tlp
from sbml_vis.tulip.graph_properties import UBIQUITOUS, VIEW_LAYOUT, VIEW_SIZE, TYPE_REACTION, TYPE, ID

__author__ = 'anna'


def ub_or_single(nd, graph):
	root = graph.getRoot()
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)
	return ubiquitous[nd] or 1 == graph.deg(nd)


def layout_ub_sps(graph):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty(VIEW_LAYOUT)
	view_size = root.getSizeProperty(VIEW_SIZE)

	for r in (n for n in graph.getNodes() if TYPE_REACTION == root[TYPE][n]):
		x1, y1 = view_layout[r].getX(), view_layout[r].getY()
		r_radius = view_size[r].getW() * sqrt(2) / 2
		# c = min(view_size[r].getW() * 1.8, 3.5)  # edge-after-bent length
		for (get_participants, get_reaction_edges, get_other_side_participants, direction) in [
			(graph.getInNodes, graph.getOutEdges, graph.getOutNodes, 1),
			(graph.getOutNodes, graph.getInEdges, graph.getInNodes, -1)]:

			ubiquitous_participants = sorted((nd for nd in get_participants(r) if ub_or_single(nd, graph)), key=lambda nd: root[ID][nd])
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
				x2, y2 = view_layout[specific_participant_example].getX(), view_layout[specific_participant_example].getY()
				species_size = view_size[specific_participant_example].getW() / 2
				edge_len = (sqrt(pow(x1 - x2, 2) + pow(y2 - y1, 2)) - r_radius - species_size)
			else:
				specific_participants = filter(lambda n: not ub_or_single(n, graph), get_other_side_participants(r))
				if specific_participants:
					specific_participant_example = specific_participants[0]
					x3, y3 = view_layout[specific_participant_example].getX(), view_layout[specific_participant_example].getY()
					x2, y2 = x1 - (x3 - x1), y1 - (y3 - y1)
				else:
					# x2, y2 = x1 + view_size[r].getW() + UBIQUITOUS_SPECIES_SIZE * ub_participants_len * direction, y1
					x2, y2 = x1 + view_size[r].getW() + size * ub_participants_len * direction, y1

			# beta is the max angle between the ubiquitous and the specific edges
			gap = 0 if just_one else 2 * min(100, max(60, ub_participants_len * 20))
			beta0 = radians(gap / 2)
			beta = beta0
			d_beta = radians(gap/(ub_participants_len - 1))

			# distance from reaction to the edge bent
			# bent = min(UBIQUITOUS_SPECIES_SIZE / 2, edge_len / 2)
			bent = min(size / 2, edge_len / 2)
			s0 = r_radius + bent
			s = s0
			# ds = min(2 * (edge_len - bent - UBIQUITOUS_SPECIES_SIZE / 2) / ub_participants_len, UBIQUITOUS_SPECIES_SIZE)
			ds = min(2 * (edge_len - bent - size / 2) / ub_participants_len, size)
			# s += ds * ub_participants_len / 2

			# angle between the horizontal line and the reaction-specific-species edge
			alpha = atan2(y2 - y1, x2 - x1)

			dc = 0
			towards_edge = -1
			for ub in ubiquitous_participants:
				# it is the only edge as ubiquitous species are duplicated
				e = get_reaction_edges(ub).next()
				x0, y0 = x1 + s * cos(alpha), y1 + s * sin(alpha)
				view_layout[e] = [tlp.Coord(x0, y0)]

				gamma = alpha + beta
				# edge-after-bent length
				# c = min(edge_len - s0 + dc + r_radius - UBIQUITOUS_SPECIES_SIZE, 2 * UBIQUITOUS_SPECIES_SIZE)
				c = min(edge_len - s0 + dc + r_radius - size, 2 * size)

				x3, y3 = x0 + c * cos(gamma), y0 + c * sin(gamma)
				view_layout[ub] = tlp.Coord(x3, y3)
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


def bend_ubiquitous_edges(graph, nodes, node2graph):
	root = graph.getRoot()
	for r in (r for r in nodes if TYPE_REACTION == root[TYPE][r]):
		lo = root[VIEW_LAYOUT][r]
		s = root[VIEW_SIZE][r].getW()
		for o_n in filter(lambda t: root[UBIQUITOUS][t] or not t in node2graph, graph.getInOutNodes(r)):
			lo_n = root[VIEW_LAYOUT][o_n]
			alpha = atan2(lo_n.getY() - lo.getY(), lo_n.getX() - lo.getX())
			x0, y0 = lo.getX() + s * 0.7 * cos(alpha), lo.getY() + s * 0.7 * sin(alpha)
			for m in node2graph[r].getNodes():
				for e in root.getInOutEdges(m):
					if o_n == root.target(e) or o_n == root.source(e):
						root[VIEW_LAYOUT][e] = [tlp.Coord(x0, y0)]