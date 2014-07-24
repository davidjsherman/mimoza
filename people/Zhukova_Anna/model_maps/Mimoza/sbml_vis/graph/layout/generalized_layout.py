from math import degrees, atan2, sqrt
from tulip import tlp

from sbml_vis.graph.layout.ubiquitous_layout import ub_or_single
from sbml_vis.graph.graph_properties import TYPE_SPECIES, TYPE, TYPE_REACTION, ID, VIEW_SIZE, VIEW_LAYOUT, VIEW_META_GRAPH, \
	COMPARTMENT_ID


__author__ = 'anna'


def get_alpha(lo, o_lo):
	alpha = degrees(atan2(lo.getY() - o_lo.getY(), o_lo.getX() - lo.getX()))
	return normalize_alpha(alpha)


def normalize_alpha(alpha):
	alpha += 22.5
	return alpha - (alpha % 45)


def align_generalized_ns(graph):
	root = graph.getRoot()

	meta_ns = {n for n in graph.getNodes() if graph.isMetaNode(n)}
	meta_sps = {n for n in meta_ns if TYPE_SPECIES == root[TYPE][n]}
	meta_rs = {n for n in meta_ns - meta_sps if TYPE_REACTION == root[TYPE][n]}

	depends_on = {}
	our_sps, our_rs = set(), set()
	for s in meta_sps:
		rs = set(graph.getInOutNodes(s)) & meta_rs
		sps = set()
		for r in rs:
			sps |= set(graph.getInOutNodes(r)) & meta_sps
		depends_on[s] = sps - {s}
		our_sps |= set(root[VIEW_META_GRAPH][s].getNodes())
	for r in meta_rs:
		our_rs |= set(root[VIEW_META_GRAPH][r].getNodes())

	node2key = {}
	while meta_sps:
		n = min(meta_sps, key=lambda s: len(depends_on[s] & meta_sps))
		meta_sps -= {n}
		for s in root[VIEW_META_GRAPH][n].getNodes():
			rs = set(root.getInOutNodes(s)) & our_rs
			sps = set()
			for r in rs:
				sps |= set(root.getInOutNodes(r)) & our_sps
			sps -= {s}
			node2key[s] = (root[ID][n], root.deg(s), root[ID][s])
			for ss in sps:
				if ss in node2key:
					node2key[s] = node2key[ss]
	for n in meta_rs:
		for r in root[VIEW_META_GRAPH][n].getNodes():
			node2key[r] = sorted(node2key[it] for it in set(root.getInOutNodes(r)) & our_sps)

	for n in meta_ns:
		ns = sorted(root[VIEW_META_GRAPH][n].getNodes(),
		            key=lambda it: node2key[it] if it in node2key else (root[ID][it], 0, ''))  # root[ID][it])
		s = root[VIEW_SIZE][n].getH()
		x0, y0 = s / 2, 0
		x, y = x0, y0
		for m in ns:
			m_h = root[VIEW_SIZE][m].getH() / 2
			y += m_h
			root[VIEW_LAYOUT][m] = tlp.Coord(x, y)
			y += m_h


def rotate_generalized_ns(graph):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty(VIEW_LAYOUT)
	for n in (n for n in graph.getNodes() if graph.isMetaNode(n)):
		lo = view_layout[n]
		meta_neighbours = lambda nodes: sorted((t for t in nodes if root.isMetaNode(t)),
		                                       key=lambda t: -root[VIEW_META_GRAPH][t].numberOfNodes())
		o_n_1 = meta_neighbours(graph.getInNodes(n))
		o_n_2 = meta_neighbours(graph.getOutNodes(n))
		if not o_n_1:
			alpha = get_alpha(lo, view_layout[o_n_2[0]]) if o_n_2 else 0
		elif not o_n_2:
			alpha = get_alpha(view_layout[o_n_1[0]], lo)
		else:
			alpha = get_alpha(view_layout[o_n_1[0]], view_layout[o_n_2[0]])

		mg = root[VIEW_META_GRAPH][n]

		# the diagonal length is larger than the side for squares
		if abs(alpha % 90) == 45 and TYPE_SPECIES != root[TYPE][n]:
			n_h = root[VIEW_SIZE][n].getH() / 2
			view_layout.translate(tlp.Coord(0, n_h * (1 - sqrt(2))), mg)
			view_layout.scale(tlp.Coord(0, sqrt(2)), mg)

		view_layout.rotateZ(-alpha, mg)

		# as Tulip considers everything to be a square when opening meta nodes,
		# and spreads the nodes along the diagonal,
		# we'd rather pretend that our node was slightly smaller
		if TYPE_SPECIES == root[TYPE][n] and abs(alpha % 90) != 0:
			r = root[VIEW_SIZE][n].getW() / sqrt(2)
			root[VIEW_SIZE][n] = tlp.Size(r, r)

		o_n_1.extend(o_n_2)
		for m in o_n_1:
			beta = get_alpha(view_layout[m], view_layout[n])
			if beta % 180 == 0:
				view_layout.rotateZ(-5, mg)


def rotate_ub_ns(graph):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty(VIEW_LAYOUT)
	for r in (r for r in graph.getNodes() if TYPE_REACTION == root[TYPE][r]):
		r_x, r_y = view_layout[r].getX(), view_layout[r].getY()

		c_id = root[COMPARTMENT_ID][r]
		reactants, products = set(s for s in graph.getInNodes(r) if root[COMPARTMENT_ID][s] == c_id), \
		                      set(s for s in graph.getOutNodes(r) if root[COMPARTMENT_ID][s] == c_id)
		ub_reactants, ub_products = {s for s in reactants if ub_or_single(s, root)}, \
		                            {s for s in products if ub_or_single(s, root)}
		order = lambda s: (-root[VIEW_META_GRAPH][s].numberOfNodes() if graph.isMetaNode(s) else 1, -graph.deg(s))
		sp_reactants, sp_products = sorted(reactants - ub_reactants, key=order), \
		                            sorted(products - ub_products, key=order)

		reactant_angle, product_angle = 0, 0
		if sp_reactants:
			sample_reactant = sp_reactants[0]
			s_x, s_y = view_layout[sample_reactant].getX(), view_layout[sample_reactant].getY()
			reactant_angle = degrees(atan2(s_y - r_y, s_x - r_x))
			if not sp_products:
				product_angle = reactant_angle + 180
		if sp_products:
			sample_product = sp_products[0]
			s_x, s_y = view_layout[sample_product].getX(), view_layout[sample_product].getY()
			product_angle = degrees(atan2(s_y - r_y, s_x - r_x))
			if not sp_reactants:
				reactant_angle = product_angle + 180

		if not (reactant_angle is None) and ub_reactants:
			cs_x, cs_y = [root[VIEW_LAYOUT][s].getX() for s in ub_reactants], \
			             [root[VIEW_LAYOUT][s].getY() for s in ub_reactants]
			s_x, s_y = (min(cs_x) + max(cs_x)) / 2, (min(cs_y) + max(cs_y)) / 2
			reactant_angle -= degrees(atan2(s_y - r_y, s_x - r_x))

			mg = graph.inducedSubGraph(ub_reactants)
			view_layout.translate(tlp.Coord(-r_x, -r_y))
			view_layout.rotateZ(reactant_angle, mg)
			view_layout.translate(tlp.Coord(r_x, r_y))
			graph.delAllSubGraphs(mg)

		if not (product_angle is None) and ub_products:
			cs_x, cs_y = [root[VIEW_LAYOUT][s].getX() for s in ub_products],\
			             [root[VIEW_LAYOUT][s].getY() for s in ub_products]
			s_x, s_y = (min(cs_x) + max(cs_x)) / 2, (min(cs_y) + max(cs_y)) / 2
			product_angle -= degrees(atan2(s_y - r_y, s_x - r_x))

			mg = graph.inducedSubGraph(ub_products)
			view_layout.translate(tlp.Coord(-r_x, -r_y))
			view_layout.rotateZ(product_angle, mg)
			view_layout.translate(tlp.Coord(r_x, r_y))
			graph.delAllSubGraphs(mg)