from collections import defaultdict
from tulip import tlp

import geojson
from sbml_vis.graph.layout.predefined_layout import apply_node_coordinates

from sbml_vis.graph.color.color import color, color_edges
from sbml_vis.graph.cluster.factoring import factor_nodes, comp_to_meta_node, merge_ubs_for_similar_reactions
from sbml_vis.converter.tlp2geojson import e2feature, n2feature
from sbml_vis.graph.graph_properties import ID, COMPARTMENT_ID, \
	TYPE_COMPARTMENT, TYPE, TYPE_REACTION, STOICHIOMETRY, RELATED_COMPARTMENT_IDS, TYPE_SPECIES, ANCESTOR_ID, TRANSPORT, \
	CLONE_ID, WIDTH, HEIGHT, VIEW_LAYOUT, VIEW_SIZE, UBIQUITOUS
from sbml_vis.graph.layout.generalized_layout import rotate_generalized_ns, align_generalized_ns
from sbml_vis.graph.layout.ubiquitous_layout import bend_ubiquitous_edges, bend_edges, layout_inner_elements, \
	get_comp_borders, bend_edges_around_compartments, layout, open_meta_ns
from sbml_generalization.utils.logger import log


DIMENSION = 512

__author__ = 'anna'


def update_level2features(feature, c_id2level2features, z, c_id):
	if c_id not in c_id2level2features:
		c_id2level2features[c_id] = defaultdict(list)
	c_id2level2features[c_id][z].append(feature)


def export_edges(c_id2level2features, c_id2outs, meta_graph, processed):
	root = meta_graph.getRoot()

	get_id = lambda n: "%s_%s" % (root[ID][n], root[CLONE_ID][n])

	# Let's call "our" compartment the one to which feature list
	# we are about to add the feature
	for e in meta_graph.getEdges():
		s, t = meta_graph.source(e), meta_graph.target(e)
		e_id = "-".join(sorted([get_id(s), get_id(t)]))
		if e_id in processed:
			continue
		processed.add(e_id)

		s_c_id, t_c_id = root[COMPARTMENT_ID][s], root[COMPARTMENT_ID][t]

		t_type, s_type = root[TYPE][t], root[TYPE][s]

		# if t_type == TYPE_REACTION and s_type == TYPE_SPECIES:
		# 	r, m = t, s
		# elif s_type == TYPE_REACTION and t_type == TYPE_SPECIES:
		# 	r, m = s, t
		# else:
		# 	r, m = None, None
		# if r and m:
		# 	e_lo = root[VIEW_LAYOUT][e]
		# 	if e_lo:
		# 		w = get_e_size(root, e).getW()
		# 		e2layout[(root[ID][r], root[ID][m])] = [[[it[0], it[1]] for it in e_lo], w]

		# 1. if the edge is inside our compartment
		if s_c_id == t_c_id:
			# 1.1. if it's a generalized edge
			if meta_graph.isMetaEdge(e):
				# 1.1.1. between an inner compartment and something
				if t_type == TYPE_COMPARTMENT or s_type == TYPE_COMPARTMENT:
					other_nd, other_type = (s, s_type) if TYPE_COMPARTMENT == t_type else (t, t_type)
					other_related_c_ids = [comp_id for comp_id in root[RELATED_COMPARTMENT_IDS][other_nd] if
					                       comp_id in c_id2outs[s_c_id]]
					# 1.1.1.a. between two inner compartments
					if t_type == s_type:
						f = e2feature(meta_graph, e, True, True)
						for z in [1, 2]:
							update_level2features(f, c_id2level2features, z, s_c_id)
					# 1.1.1.b. between an inner compartment and a generalized reaction/species
					elif meta_graph.isMetaNode(s) and meta_graph.isMetaNode(t):
						f = e2feature(meta_graph, e, True, TYPE_SPECIES == other_type or not other_related_c_ids)
						update_level2features(f, c_id2level2features, 1, s_c_id)
					# 1.1.1.c. between an inner compartment and a reaction/species
					# that was generalized on the previous zoom level
					elif root[ANCESTOR_ID][s] or root[ANCESTOR_ID][t]:
						f = e2feature(meta_graph, e, True, TYPE_SPECIES == other_type or not other_related_c_ids)
						update_level2features(f, c_id2level2features, 2, s_c_id)
					# 1.1.1.d. between an inner compartment and a non-generalizable reaction/species
					else:
						f = e2feature(meta_graph, e, True, TYPE_SPECIES == other_type or not other_related_c_ids)
						for z in [1, 2]:
							update_level2features(f, c_id2level2features, z, s_c_id)
				# 1.1.2. between a reaction and a species
				else:
					# let's check that if one of the species/reaction pair is simple but generalizable,
					# then the other one is also simple
					# (if one is generalized and the other is not it's an intermediate state not to be exported)
					if (root[ANCESTOR_ID][s] or root[ANCESTOR_ID][t]) and (
						meta_graph.isMetaNode(s) or meta_graph.isMetaNode(t)):
						continue
					r = s if TYPE_REACTION == s_type else t
					other_related_c_ids = [comp_id for comp_id in root[RELATED_COMPARTMENT_IDS][r] if
					                       comp_id in c_id2outs[s_c_id]]
					f = e2feature(meta_graph, e, root[TRANSPORT][r], not other_related_c_ids)
					# 1.1.2.a. between a generalized reaction/species and some reaction/species
					if meta_graph.isMetaNode(s) or meta_graph.isMetaNode(t):
						update_level2features(f, c_id2level2features, 1, s_c_id)
					# 1.1.2.b. between a reaction/species that was generalized on the previous zoom level
					# and something
					elif root[ANCESTOR_ID][s] or root[ANCESTOR_ID][t]:
						update_level2features(f, c_id2level2features, 2, s_c_id)
					# 1.1.2.c. between a non-generalizable reaction and a non-generalizable species
					else:
						for z in [1, 2]:
							update_level2features(f, c_id2level2features, z, s_c_id)
			# 1.2. it's a simple edge
			else:
				r = s if TYPE_REACTION == s_type else t
				other_related_c_ids = [comp_id for comp_id in root[RELATED_COMPARTMENT_IDS][r] if
				                       comp_id in c_id2outs[s_c_id]]
				f = e2feature(meta_graph, e, root[TRANSPORT][r], not other_related_c_ids)
				# 1.2.1. between a reaction/species that was generalized on the previous zoom level
				# and something
				if root[ANCESTOR_ID][s] or root[ANCESTOR_ID][t]:
					update_level2features(f, c_id2level2features, 2, s_c_id)
				# 1.2.2. it's a simple edge
				# between a non-generalizable reaction and a non-generalizable species
				else:
					for z in [1, 2]:
						update_level2features(f, c_id2level2features, z, s_c_id)
		# 2. the edge is between two compartments that are not inside the same compartment
		# (if they are then we've already processed them during the step 1.1.1.a.)
		# => no our compartment would need it
		if TYPE_COMPARTMENT == s_type == t_type:
			continue
		comp_id = root[ID][s] if TYPE_COMPARTMENT == s_type else (root[ID][t] if TYPE_COMPARTMENT == t_type else None)
		# 3. between our closed compartment and something outside
		if comp_id:
			pass
		# # Let's check that this "something outside" is not inside
		# other_c_id = t_c_id if comp_id == root[ID][s] else s_c_id
		# if other_c_id == comp_id or comp_id in c_id2outs[other_c_id]:
		# continue
		#
		# # then this something outside shouldn't be an opened generalizable reaction/species
		# # (not for our compartment's feature list)
		# element = s if TYPE_COMPARTMENT != s_type else t
		# if root[ANCESTOR_ID][element]:
		# 	continue
		# f = e2feature(meta_graph, e, True, False)
		# update_level2features(f, c_id2level2features, 0, comp_id)

		# 4. between some reaction and some species,
		# at least one of which is outside of our compartment
		else:
			# let's check that if one of the species/reaction pair is simple but generalizable,
			# then the other one is also simple
			# (if one is generalized and the other is not it's an intermediate state not to be exported)
			if (root[ANCESTOR_ID][s] or root[ANCESTOR_ID][t]) and (
				meta_graph.isMetaNode(s) or meta_graph.isMetaNode(t)):
				continue
			# the reaction
			r = s if TYPE_REACTION == s_type else t
			related_c_ids = set(root[RELATED_COMPARTMENT_IDS][r])
			if s_c_id != t_c_id:
				related_c_ids.add(root[COMPARTMENT_ID][r])
			# only those (our) compartments for which this edge is not completely inside them will need it
			related_c_ids = [c_id for c_id in related_c_ids
			                 if not ((c_id == s_c_id or c_id in c_id2outs[s_c_id])
			                         and (c_id == t_c_id or c_id in c_id2outs[t_c_id]))]
			for c_id in related_c_ids:
				f = e2feature(meta_graph, e, True, False)
				# 4.1. it's a generalized edge
				if meta_graph.isMetaEdge(e):
					# 4.1.a. both the reaction and the species are outside our compartment
					if t_c_id != c_id and s_c_id != c_id:
						update_level2features(f, c_id2level2features, 1, c_id)
					# 4.1.b. only one of them is outside
					# (its ancestor on the previous zoom level was
					# an edge between our compartment and this outside element)
					else:
						update_level2features(f, c_id2level2features, 1, c_id)
				# 4.2. it's a simple edge but at least one of our reaction-species pair
				# was generalized on the previous zoom level
				elif root[ANCESTOR_ID][s] or root[ANCESTOR_ID][t]:
					update_level2features(f, c_id2level2features, 2, c_id)
				# 4.3. it's a simple edge between a non-generalizable reaction and a non-generalizable species
				else:
					for z in [1, 2] if (c_id != s_c_id and c_id != t_c_id) else [1, 2]:
						update_level2features(f, c_id2level2features, z, c_id)


def export_nodes(c_id2info, c_id2outs, c_id2level2features, meta_graph, processed, r2rs_ps, n2layout):
	root = meta_graph.getRoot()

	get_id = lambda n: "%s_%s" % (root[ID][n], root[CLONE_ID][n])

	for n in meta_graph.getNodes():
		n_id = get_id(n)
		if n_id in processed:
			continue
		processed.add(n_id)

		x, y = root[VIEW_LAYOUT][n].getX(), root[VIEW_LAYOUT][n].getY()
		w, h = root[VIEW_SIZE][n].getW(), root[VIEW_SIZE][n].getH()
		if root[UBIQUITOUS][n]:
			if not root[ID][n] in n2layout:
				n2layout[root[ID][n]] = {}
			for clone_id in root[CLONE_ID][n].split(","):
				n2layout[root[ID][n]][clone_id] = [(x, y), (w, h)]
		else:
			n2layout[root[ID][n]] = [(x, y), (w, h)]

		n_type = root[TYPE][n]
		c_id = root[COMPARTMENT_ID][n]
		# 1. if it's a compartment
		if n_type == TYPE_COMPARTMENT:
			# 1.a. if it's not the most outside compartment,
			# then it's parent needs its feature
			if c_id:
				f, _ = n2feature(meta_graph, n, c_id2info, r2rs_ps, False, False)
				for z in [1, 2]:
					update_level2features(f, c_id2level2features, z, c_id)
			# add its feature and its background to its own collection
			c_id = root[ID][n]
			_, bg = n2feature(meta_graph, n, c_id2info, r2rs_ps, False, False)
			# update_level2features(f, c_id2level2features, 0, c_id)
			for z in [1, 2]:
				update_level2features(bg, c_id2level2features, z, c_id)
		# 2. it's a reaction or a species
		elif n_type in [TYPE_REACTION, TYPE_SPECIES]:
			# only those (our) compartments for which this element is outside of them will need it
			related_c_ids = [comp_id for comp_id in root[RELATED_COMPARTMENT_IDS][n] if not comp_id in c_id2outs[c_id]]
			other_related_c_ids = [comp_id for comp_id in root[RELATED_COMPARTMENT_IDS][n] if
			                       comp_id in c_id2outs[c_id]]
			# 2.1. it's generalized
			is_transport = root[TRANSPORT][n] if TYPE_REACTION == n_type \
				else next(
				(1 for it in root.getInOutNodes(n) if TYPE_COMPARTMENT == root[TYPE][it] or root[TRANSPORT][it]), None)
			if meta_graph.isMetaNode(n):
				f, bg = n2feature(meta_graph, n, c_id2info, r2rs_ps, is_transport,
				                  not other_related_c_ids)
				# add features to it's own compartment
				update_level2features(f, c_id2level2features, 1, c_id)
				update_level2features(bg, c_id2level2features, 2, c_id)
				# add features to the compartments for that it's outside
				for c_id in related_c_ids:
					f, bg = n2feature(meta_graph, n, c_id2info, r2rs_ps, True, False)
					update_level2features(f, c_id2level2features, 1, c_id)
					update_level2features(bg, c_id2level2features, 2, c_id)
			# 2.1. it's simple
			else:
				f, _ = n2feature(meta_graph, n, c_id2info, r2rs_ps, is_transport, not other_related_c_ids)
				# add features to it's own compartment
				# (level depends on whether it was generalized on the previous zoom or not)
				for z in [2] if root[ANCESTOR_ID][n] else [1, 2]:
					update_level2features(f, c_id2level2features, z, c_id)
				# add features to the compartments for that it's outside
				# (level depends on whether it was generalized on the previous zoom or not)
				for c_id in related_c_ids:
					f, _ = n2feature(meta_graph, n, c_id2info, r2rs_ps, True, False)
					for z in [2] if root[ANCESTOR_ID][n] else [1, 2]:
						update_level2features(f, c_id2level2features, z, c_id)


def export_elements(c_id2info, c_id2outs, c_id2level2features, meta_graph, processed, r2rs_ps, n2layout):
	export_edges(c_id2level2features, c_id2outs, meta_graph, processed)
	export_nodes(c_id2info, c_id2outs, c_id2level2features, meta_graph, processed, r2rs_ps, n2layout)


def meta_graph2features(c_id2info, c_id2outs, meta_graph, r2rs_ps, n2xy=None):
	root = meta_graph.getRoot()

	c_id2level2features = {}
	processed = set()
	c_id2c_borders = {}
	get_id = lambda n: "%s_%s" % (root[ID][n], root[CLONE_ID][n])
	get_e_id = lambda e: "-".join(sorted([get_id(meta_graph.source(e)), get_id(meta_graph.target(e))]))
	bb = tlp.computeBoundingBox(meta_graph)
	n2layout, (d_w, d_h) = {}, (bb.width(), bb.height())

	while True:
		for c_id, sizes in c_id2c_borders.iteritems():
			layout_inner_elements(meta_graph, c_id, sizes)

		bend_edges_around_compartments(meta_graph, (e for e in meta_graph.getEdges() if not get_e_id(e) in processed))
		bend_edges(meta_graph)
		# bend_species_edges(meta_graph)
		color_edges(meta_graph)
		export_elements(c_id2info, c_id2outs, c_id2level2features, meta_graph, processed, r2rs_ps, n2layout)

		metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n) and TYPE_COMPARTMENT == root[TYPE][n]]
		if not metas:
			c_id2c_borders = {}
			metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)]
			if not metas:
				break
			align_generalized_ns(meta_graph)
			rotate_generalized_ns(meta_graph)
			bend_ubiquitous_edges(meta_graph, metas)
		else:
			c_id2c_borders = {root[ID][c]: get_comp_borders(c, root) for c in metas}
		open_meta_ns(meta_graph, metas)
		if n2xy:
			apply_node_coordinates(meta_graph, n2xy)

	for c_id in c_id2info.iterkeys():
		(name, go, (l, out_c_id)) = c_id2info[c_id]
		comp_n = comp_to_meta_node(meta_graph, c_id, (go, name), out_c_id, False, None, n2xy)
		bend_edges(meta_graph)
		color_edges(meta_graph)
		export_edges(c_id2level2features, c_id2outs, meta_graph, processed)
		metas = factor_nodes(meta_graph)
		bend_ubiquitous_edges(meta_graph, metas)
		bend_edges(meta_graph)
		metas.append(comp_n)
		color_edges(meta_graph)
		export_edges(c_id2level2features, c_id2outs, meta_graph, processed)
		open_meta_ns(meta_graph, metas)

	return c_id2level2features, (n2layout, (d_w, d_h))


def get_reaction2reactants_products(root):
	r2rs_ps = {}
	for r in (r for r in root.getNodes() if TYPE_REACTION == root[TYPE][r]):
		rs = [(root[STOICHIOMETRY][e], root.source(e)) for e in root.getInEdges(r)]
		ps = [(root[STOICHIOMETRY][e], root.target(e)) for e in root.getOutEdges(r)]
		r2rs_ps[r] = rs, ps
	return r2rs_ps


def calculate_related_compartments(root):
	for r in (r for r in root.getNodes() if TYPE_REACTION == root[TYPE][r]):
		root[RELATED_COMPARTMENT_IDS][r] = list(
			{root[COMPARTMENT_ID][n] for n in root.getInOutNodes(r)} - {root[COMPARTMENT_ID][r]})
	for s in (s for s in root.getNodes() if TYPE_SPECIES == root[TYPE][s]):
		result = set()
		for r in root.getInOutNodes(s):
			result |= set(root[RELATED_COMPARTMENT_IDS][r]) | {root[COMPARTMENT_ID][r]}
		root[RELATED_COMPARTMENT_IDS][s] = list(result - {root[COMPARTMENT_ID][s]})


def graph2geojson(c_id2info, c_id2outs, graph, verbose, onto=None, n2xy=None):
	root = graph.getRoot()

	log(verbose, 'generalized species/reactions -> metanodes')
	merge_ubs_for_similar_reactions(root)

	r2rs_ps = get_reaction2reactants_products(root)

	calculate_related_compartments(root)

	meta_graph = graph.inducedSubGraph([n for n in graph.getNodes()])

	log(verbose, 'compartments -> metanodes')
	process_compartments(c_id2info, meta_graph, onto, n2xy)

	color(root)
	color_edges(root)

	log(verbose, 'tlp nodes -> geojson features')
	c_id2level2features, (n2lo, (d_w, d_h)) = meta_graph2features(c_id2info, c_id2outs, meta_graph, r2rs_ps, n2xy)

	geometry = geojson.Polygon([[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]])
	rescale(c_id2level2features)
	get_l2fs = lambda l2fs: {lev: geojson.FeatureCollection(features, geometry=geometry) for (lev, features) in
	                         l2fs.iteritems()}
	return {c_id: get_l2fs(l2fs) for (c_id, l2fs) in c_id2level2features.iteritems()}, (n2lo, (d_w, d_h))


def rescale(c_id2level2features):
	for c_id, lev2fs in c_id2level2features.iteritems():
		if 1 in lev2fs:
			fs = lev2fs[1]
			min_x, min_y, max_x, max_y = None, None, None, None
			for f in fs:
				if type(f.geometry) == geojson.Point:
					[x, y] = f.geometry.coordinates
					w = f.properties[WIDTH]
					h = f.properties[HEIGHT] if HEIGHT in f.properties else f.properties[WIDTH]
					if min_x is None or min_x > x - w:
						min_x = x - w
					if min_y is None or min_y > y - h:
						min_y = y - h
					if max_x is None or max_x < x + w:
						max_x = x + w
					if max_y is None or max_y < y + h:
						max_y = y + h
			scale_coefficient = float(DIMENSION / max(max_x - min_x, max_y - min_y))
			if scale_coefficient == 1.0:
				continue

			processed = set()
			for fs in lev2fs.itervalues():
				for f in fs:
					if f in processed:
						continue
					else:
						processed.add(f)
					if type(f.geometry) == geojson.Point:
						f.geometry.coordinates[0] *= scale_coefficient
						f.geometry.coordinates[1] *= scale_coefficient
					elif type(f.geometry) == geojson.MultiPoint:
						for coord in f.geometry.coordinates:
							coord[0] *= scale_coefficient
							coord[1] *= scale_coefficient
					f.properties[WIDTH] *= scale_coefficient
					if HEIGHT in f.properties:
						f.properties[HEIGHT] *= scale_coefficient


def process_compartments(c_id2info, meta_graph, onto=None, n2xy=None):
	# root = meta_graph.getRoot()
	factor_nodes(meta_graph)

	current_zoom_level = max({info[2][0] for info in c_id2info.itervalues()})
	while current_zoom_level >= 0:
		for c_id in c_id2info.iterkeys():
			(name, go, (l, out_c_id)) = c_id2info[c_id]
			if current_zoom_level == l:
				# ns = [n for n in meta_graph.getNodes() if root[COMPARTMENT_ID][n] == c_id]
				# factor_nodes(meta_graph, ns)
				comp_to_meta_node(meta_graph, c_id, (go, name), out_c_id, True, onto, n2xy)
		current_zoom_level -= 1
		if n2xy:
			apply_node_coordinates(meta_graph, n2xy)
		else:
			layout(meta_graph, 1, onto)