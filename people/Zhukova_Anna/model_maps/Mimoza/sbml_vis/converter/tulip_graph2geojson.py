from collections import defaultdict
from tulip import tlp

import geojson

from sbml_vis.graph.cluster.factoring import factor_nodes, comp_to_meta_node, merge_ubs_for_similar_reactions
from sbml_vis.converter.tlp2geojson import e2feature, n2feature
from sbml_vis.graph.graph_properties import ID, COMPARTMENT_ID, \
	TYPE_COMPARTMENT, TYPE, TYPE_REACTION, STOICHIOMETRY, RELATED_COMPARTMENT_IDS, TYPE_SPECIES, ANCESTOR_ID, TRANSPORT, \
	CLONE_ID, NAME
from sbml_vis.graph.layout.generalized_layout import rotate_generalized_ns, align_generalized_ns
from sbml_vis.graph.layout.ubiquitous_layout import bend_ubiquitous_edges, bend_edges
from sbml_vis.graph.layout.layout_utils import open_meta_ns, layout
from sbml_generalization.utils.logger import log


DIMENSION = 512

CELL_GO_ID = 'go:0005623'
CELL = 'cell'

__author__ = 'anna'


def get_scales_by_metagraph(mg):
	bb = tlp.computeBoundingBox(mg)
	c_x, c_y = bb.center()[0], bb.center()[1]
	bb_w, bb_h = bb.width() / 2, bb.height() / 2
	min_x, min_y, max_x, max_y = c_x - bb_w, c_y - bb_h, c_x + bb_w, c_y + bb_h
	w, h = max_x - min_x, max_y - min_y
	if w > h:
		max_y += (w - h) / 2
	elif h > w:
		min_x -= (h - w) / 2
	scale_coefficient = DIMENSION / max(w, h)

	def scale(x, y):
		x, y = (x - min_x) * scale_coefficient, (max_y - y) * scale_coefficient
		return [float(x), float(y)]

	return scale, scale_coefficient


def get_scale_coefficients(root, c_ids):
	c_id2scales = {}
	for c_id in c_ids:
		ns = [n for n in root.getNodes() if c_id == root[ID][n]
		      or c_id in root[RELATED_COMPARTMENT_IDS][n] and not root[ANCESTOR_ID][n]]
		mg = root.inducedSubGraph(ns)
		c_id2scales[c_id] = get_scales_by_metagraph(mg)
		root.delAllSubGraphs(mg)
	# ns = {n} | {m for m in meta_graph.getInOutNodes(n)}
	# rs = [r for r in ns if root[TYPE][r] == TYPE_REACTION]
	# for r in rs:
	# 	ns |= set(meta_graph.getInOutNodes(r))
	#
	# mg = meta_graph.inducedSubGraph(ns)
	# # or has_neighbours_in_compartment(n, c_id, meta_graph)])
	# scale, scale_coefficient = get_scales_by_metagraph(mg)
	#
	# meta_graph.delAllSubGraphs(mg)
	return c_id2scales


def update_level2features(feature, c_id2level2features, z, c_id):
	if not c_id in c_id2level2features:
		c_id2level2features[c_id] = defaultdict(list)
	c_id2level2features[c_id][z].append(feature)


def meta_graph2features(c_id2info, meta_graph, r2rs_ps):
	root = meta_graph.getRoot()

	c_id2scales = get_scale_coefficients(root, c_id2info.iterkeys())
	c_id2level2features = {}
	get_level = lambda c_id: c_id2info[c_id][2][0]
	get_id = lambda n: "%s_%d" % (root[ID][n], root[CLONE_ID][n])
	processed = set()
	stage = 0
	while True:
		bend_edges(meta_graph)

		# Let's call "our" compartment the one to which feature list
		# we are about to add the feature
		for e in meta_graph.getEdges():
			s, t = meta_graph.source(e), meta_graph.target(e)
			e_id = "%s-%s" % (get_id(s), get_id(t))
			if e_id in processed:
				continue
			processed.add(e_id)
			s_c_id, t_c_id = root[COMPARTMENT_ID][s], root[COMPARTMENT_ID][t]

			t_type, s_type = root[TYPE][t], root[TYPE][s]
			# 1. if the edge is inside our compartment
			if s_c_id == t_c_id:
				scale, _ = c_id2scales[s_c_id]
				# 1.1. if it's a generalized edge
				if meta_graph.isMetaEdge(e):
					# 1.1.1. between an inner compartment and something
					if t_type == TYPE_COMPARTMENT or s_type == TYPE_COMPARTMENT:
						f = e2feature(meta_graph, e, scale, True)
						# 1.1.1.a. between two inner compartments
						if t_type == s_type:
							for z in [1, 2]:
								update_level2features(f, c_id2level2features, z, s_c_id)
						# 1.1.1.b. between an inner compartment and a generalized reaction/species
						elif meta_graph.isMetaNode(s) and meta_graph.isMetaNode(t):
							update_level2features(f, c_id2level2features, 1, s_c_id)
						# 1.1.1.c. between an inner compartment and a reaction/species
						# that was generalized on the previous zoom level
						elif root[ANCESTOR_ID][s] or root[ANCESTOR_ID][t]:
							update_level2features(f, c_id2level2features, 2, s_c_id)
						# 1.1.1.d. between an inner compartment and a non-generalizable reaction/species
						else:
							for z in [1, 2]:
								update_level2features(f, c_id2level2features, z, s_c_id)
					# 1.1.2. between a reaction and a species
					else:
						f = e2feature(meta_graph, e, scale, root[TRANSPORT][s] or root[TRANSPORT][t])
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
					f = e2feature(meta_graph, e, scale, root[TRANSPORT][s] or root[TRANSPORT][t])
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
				scale, _ = c_id2scales[comp_id]
				f = e2feature(meta_graph, e, scale, True)
				update_level2features(f, c_id2level2features, 0, comp_id)
			# 4. between some reaction and some species,
			# at least one of which is outside our compartment
			else:
				# the reaction
				r = s if TYPE_REACTION == s_type else t
				related_c_ids = set(root[RELATED_COMPARTMENT_IDS][r])
				if s_c_id != t_c_id:
					related_c_ids.add(root[COMPARTMENT_ID][r])
				max_level = max(get_level(s_c_id), get_level(t_c_id))
				# todo: problem here
				# only those (our) compartments for which this edge is not completely inside them will need it
				related_c_ids = [c_id for c_id in related_c_ids if get_level(c_id) >= max_level]
				for c_id in related_c_ids:
					scale, _ = c_id2scales[c_id]
					f = e2feature(meta_graph, e, scale, True)
					# 4.1. it's a generalized edge
					if meta_graph.isMetaEdge(e):
						# 4.1.a. both the reaction and the species are outside our compartment
						if t_c_id != c_id and s_c_id != c_id:
							for z in [0, 1]:
								update_level2features(f, c_id2level2features, z, c_id)
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
						for z in [0, 1, 2] if get_level(c_id) > max_level else [1, 2]:
							update_level2features(f, c_id2level2features, z, c_id)

		for n in meta_graph.getNodes():
			n_id = get_id(n)
			if n_id in processed:
				continue
			processed.add(n_id)

			n_type = root[TYPE][n]
			c_id = root[COMPARTMENT_ID][n]
			if c_id:
				scale, scale_coefficient = c_id2scales[c_id]
			# 1. if it's a compartment
			if n_type == TYPE_COMPARTMENT:
				# 1.a. if it's not the most outside compartment,
				# then it's parent needs its feature
				if c_id:
					f, _ = n2feature(meta_graph, n, scale, c_id2info, scale_coefficient, r2rs_ps, False)
					for z in [1, 2]:
						update_level2features(f, c_id2level2features, z, c_id)
				# add its feature and its background to its own collection
				c_id = root[ID][n]
				scale, scale_coefficient = c_id2scales[c_id]
				f, bg = n2feature(meta_graph, n, scale, c_id2info, scale_coefficient, r2rs_ps, False)
				update_level2features(f, c_id2level2features, 0, c_id)
				for z in [1, 2]:
					update_level2features(bg, c_id2level2features, z, c_id)
			# 2. it's a reaction or a species
			elif n_type in [TYPE_REACTION, TYPE_SPECIES]:
				c_level = get_level(c_id)
				# only those (our) compartments for which this element is outside of them will need it
				related_c_ids = [comp_id for comp_id in root[RELATED_COMPARTMENT_IDS][n] if get_level(comp_id) >= c_level]
				# 2.1. it's generalized
				if meta_graph.isMetaNode(n):
					f, bg = n2feature(meta_graph, n, scale, c_id2info, scale_coefficient, r2rs_ps, root[TRANSPORT][n])
					# add features to it's own compartment
					update_level2features(f, c_id2level2features, 1, c_id)
					update_level2features(bg, c_id2level2features, 2, c_id)
					# add features to the compartments for that it's outside
					for c_id in related_c_ids:
						scale, scale_coefficient = c_id2scales[c_id]
						f, bg = n2feature(meta_graph, n, scale, c_id2info, scale_coefficient, r2rs_ps, True)
						for z in [0, 1]:
							update_level2features(f, c_id2level2features, z, c_id)
						update_level2features(bg, c_id2level2features, 2, c_id)
				# 2.1. it's simple
				else:
					f, _ = n2feature(meta_graph, n, scale, c_id2info, scale_coefficient, r2rs_ps, root[TRANSPORT][n])
					# add features to it's own compartment
					# (level depends on whether it was generalized on the previous zoom or not)
					for z in [2] if root[ANCESTOR_ID][n] else [1, 2]:
						update_level2features(f, c_id2level2features, z, c_id)
					# add features to the compartments for that it's outside
					# (level depends on whether it was generalized on the previous zoom or not)
					for c_id in related_c_ids:
						scale, scale_coefficient = c_id2scales[c_id]
						f, _ = n2feature(meta_graph, n, scale, c_id2info, scale_coefficient, r2rs_ps, True)
						for z in [2] if root[ANCESTOR_ID][n] else [0, 1, 2]:
							update_level2features(f, c_id2level2features, z, c_id)

		if not next((n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n)), None):
			break

		if stage == 0:
			metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n) and TYPE_COMPARTMENT == root[TYPE][n]]
			bend_ubiquitous_edges(meta_graph, metas)
			open_meta_ns(meta_graph, metas)
			stage = 1
		elif stage == 1:
			factor_nodes(meta_graph)
			stage = 2
		elif stage == 2:
			metas = [n for n in meta_graph.getNodes() if meta_graph.isMetaNode(n) and TYPE_COMPARTMENT != root[TYPE][n]]
			align_generalized_ns(meta_graph)
			rotate_generalized_ns(meta_graph)
			bend_ubiquitous_edges(meta_graph, metas)
			open_meta_ns(meta_graph, metas)
			stage = 0
	return c_id2level2features


def graph2geojson(c_id2info, graph, verbose):
	root = graph.getRoot()

	log(verbose, 'generalized species/reactions -> metanodes')
	merge_ubs_for_similar_reactions(root)

	r2rs_ps = {}
	for r in (r for r in root.getNodes() if TYPE_REACTION == root[TYPE][r]):
		rs = [(root[STOICHIOMETRY][e], root.source(e)) for e in root.getInEdges(r)]
		ps = [(root[STOICHIOMETRY][e], root.target(e)) for e in root.getOutEdges(r)]
		r2rs_ps[r] = rs, ps

	for r in (r for r in root.getNodes() if TYPE_REACTION == root[TYPE][r]):
		root[RELATED_COMPARTMENT_IDS][r] = list(
			{root[COMPARTMENT_ID][n] for n in root.getInOutNodes(r)} - {root[COMPARTMENT_ID][r]})
	for s in (s for s in root.getNodes() if TYPE_SPECIES == root[TYPE][s]):
		result = set()
		for r in root.getInOutNodes(s):
			result |= set(root[RELATED_COMPARTMENT_IDS][r]) | {root[COMPARTMENT_ID][r]}
		root[RELATED_COMPARTMENT_IDS][s] = list(result - {root[COMPARTMENT_ID][s]})

	meta_graph = graph.inducedSubGraph([n for n in graph.getNodes()])

	log(verbose, 'compartments -> metanodes')
	process_compartments(c_id2info, meta_graph)

	log(verbose, 'tlp nodes -> geojson features')
	c_id2level2features = meta_graph2features(c_id2info, meta_graph, r2rs_ps)

	geometry = geojson.Polygon([[0, DIMENSION], [0, 0], [DIMENSION, 0], [DIMENSION, DIMENSION]])
	get_l2fs = lambda l2fs: {lev: geojson.FeatureCollection(features, geometry=geometry) for (lev, features) in
	                         l2fs.iteritems()}
	return {c_id: get_l2fs(l2fs) for (c_id, l2fs) in c_id2level2features.iteritems()}


def process_compartments(c_id2info, meta_graph):
	root = meta_graph.getRoot()
	current_zoom_level = max({info[2][0] for info in c_id2info.itervalues()})
	while current_zoom_level >= 0:
		for c_id in c_id2info.iterkeys():
			(name, go, (l, out_c_id)) = c_id2info[c_id]
			if current_zoom_level == l:
				ns = [n for n in meta_graph.getNodes() if root[COMPARTMENT_ID][n] == c_id]
				factor_nodes(meta_graph, ns)
				comp_to_meta_node(meta_graph, c_id, (go, name), out_c_id)
		current_zoom_level -= 1
		layout(meta_graph)