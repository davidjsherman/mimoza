import colorsys

from tulip import tlp
from sbml_vis.graph.graph_properties import *


__author__ = 'anna'


GRAY = tlp.Color(180, 180, 180) # B4B4B4
TRANSPARENT_GRAY = tlp.Color(200, 200, 200, 80)
LIGHT_RED = tlp.Color(255, 100, 100)
LIGHT_BLUE = tlp.Color(100, 100, 255)
WHITE = tlp.Color(255, 255, 255)
TRANSPARENT = tlp.Color(0, 0, 0, 0)

ORANGE = tlp.Color(253, 180, 98) # FDB462
YELLOW = tlp.Color(255, 255, 179) # FFFFB3
RED = tlp.Color(251, 128, 114) # FB8072
BLUE = tlp.Color(128, 177, 211) # 80B1D3
GREEN = tlp.Color(179, 222, 105) # B3DE69
VIOLET = tlp.Color(190, 186, 218) # BEBADA
TURQUOISE = tlp.Color(141, 211, 199) # 8DD3C7


def get_key(n, graph):
	root = graph.getRoot()
	type_ = root[TYPE][n]
	if TYPE_REACTION == type_:
		an_id = root[ANCESTOR_ID][n]
		if an_id:
			return an_id
		return root[ID][n]
	if TYPE_SPECIES == type_:
		an_ch = root[ANCESTOR_ANNOTATION][n]
		if an_ch:
			return an_ch
		an_id = root[ANCESTOR_ID][n]
		if an_id:
			return an_id
		ch = root[ANNOTATION][n]
		if ch:
			return ch
		return root[ID][n]
	return None


def color(graph):
	root = graph.getRoot()
	view_color = root.getColorProperty(VIEW_COLOR)

	keys = {get_key(n, graph) for n in graph.getNodes() if root[TYPE][n] == TYPE_REACTION}
	i = len(keys)

	colors = [colorsys.hsv_to_rgb(x * 1.0 / i, 0.5, 0.8) for x in xrange(i)]
	colors = [(int(255 * r), int(255 * g), int(255 * b)) for (r, g, b) in colors]
	key2color = dict(zip(keys, colors))

	keys = {get_key(n, graph) for n in graph.getNodes() if root[TYPE][n] == TYPE_SPECIES}
	i = len(keys)

	colors = [colorsys.hsv_to_rgb(x * 1.0 / i, 0.5, 0.8) for x in xrange(i)]
	colors = [(int(255 * r), int(255 * g), int(255 * b)) for (r, g, b) in colors]

	key2color.update(dict(zip(keys, colors)))

	root = graph.getRoot()
	organelles = root.getAttribute(ORGANELLES).split(";")
	cyto = root.getAttribute(CYTOPLASM)
	i = len(organelles) + 2
	colors = [colorsys.hsv_to_rgb(x * 1.0 / i, 0.5, 0.8) for x in xrange(i)]
	colors = [tlp.Color(int(255 * r), int(255 * g), int(255 * b)) for (r, g, b) in colors]
	key2comp_color = dict(zip(organelles + [cyto], colors[1:]))


	for n in graph.getNodes():
		type_ = root[TYPE][n]

		if TYPE_COMPARTMENT == type_:
			view_color[n] = key2comp_color[root[NAME][n]] if root[NAME][n] in key2comp_color else TRANSPARENT_GRAY
			continue
		a = 255
		if TYPE_REACTION == type_:
			r, g, b = key2color[get_key(n, graph)]
			if graph.isMetaNode(n):
				a = 100
			view_color[n] = tlp.Color(r, g, b, a)
			for e in graph.getInOutEdges(n):
				if root[UBIQUITOUS][graph.target(e)] or root[UBIQUITOUS][graph.source(e)]:
					view_color[e] = GRAY
				else:
					view_color[e] = tlp.Color(r, g, b, 100 if graph.isMetaEdge(e) else 255)
		if TYPE_SPECIES == type_:
			if root[UBIQUITOUS][n]:
				r, g, b = 180, 180, 180
			else:
				r, g, b = key2color[get_key(n, graph)]
				if graph.isMetaNode(n):
					a = 100
			view_color[n] = tlp.Color(r, g, b, a)


def simple_color(graph):
	root = graph.getRoot()
	view_color = root.getColorProperty(VIEW_COLOR)

	for n in root.getNodes():
		type_ = root[TYPE][n]
		if TYPE_COMPARTMENT == type_:
			view_color[n] = YELLOW
		elif TYPE_REACTION == type_:
			is_transport = root[TRANSPORT][n]
			if root.isMetaNode(n):
				view_color[n] = TURQUOISE if is_transport else VIOLET
			else:
				view_color[n] = GREEN if is_transport else BLUE
			for e in root.getInOutEdges(n):
				if root[UBIQUITOUS][root.target(e)] or root[UBIQUITOUS][root.source(e)]:
					view_color[e] = GRAY
				else:
					view_color[e] = view_color[n]
		elif TYPE_SPECIES == type_:
			if root[UBIQUITOUS][n]:
				view_color[n] = GRAY
			else:
				if root.isMetaNode(n):
					view_color[n] = ORANGE
				else:
					view_color[n] = RED