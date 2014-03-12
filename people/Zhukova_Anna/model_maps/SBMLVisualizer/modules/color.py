import colorsys
from tulip import tlp
from modules.graph_tools import TERM_ID, TYPE_REACTION, TYPE, ANCESTOR_ID, TYPE_SPECIES, ID, ANCESTOR_TERM_ID, \
	VIEW_COLOR, VIEW_BORDER_COLOR, ORGANELLES, CYTOPLASM, TYPE_COMPARTMENT, VIEW_META_GRAPH, NAME, UBIQUITOUS

__author__ = 'anna'


grey = tlp.Color(180, 180, 180)
transparent_grey = tlp.Color(200, 200, 200, 80)
light_red = tlp.Color(255, 100, 100)
light_blue = tlp.Color(100, 100, 255)
white = tlp.Color(255, 255, 255)
transparent = tlp.Color(0, 0, 0, 0)

orange = tlp.Color(253, 180, 98)
yellow = tlp.Color(255, 255, 179)
red = tlp.Color(251, 128, 114)
blue = tlp.Color(128, 177, 211)
green = tlp.Color(179, 222, 105)
violet = tlp.Color(190, 186, 218)
turquoise = tlp.Color(141, 211, 199)


def get_key(n, graph):
	root = graph.getRoot()
	type_ = root[TYPE][n]
	if TYPE_REACTION == type_:
		an_id = root[ANCESTOR_ID][n]
		if an_id:
			return an_id
		return root[ID][n]
	if TYPE_SPECIES == type_:
		an_ch = root[ANCESTOR_TERM_ID][n]
		if an_ch:
			return an_ch
		an_id = root[ANCESTOR_ID][n]
		if an_id:
			return an_id
		ch = root[TERM_ID][n]
		if ch:
			return ch
		return root[ID][n]
	return None


def color(graph):
	root = graph.getRoot()
	view_color = root.getColorProperty(VIEW_COLOR)
	view_border_color = root.getColorProperty(VIEW_BORDER_COLOR)

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
	key2border_color = dict(zip(organelles + [cyto], colors[1:]))

	view_border_color.setAllNodeValue(white)

	for n in graph.getNodes():
		type_ = root[TYPE][n]
		comp = root[TYPE_COMPARTMENT][n]
		ns = root[VIEW_META_GRAPH][n].getNodes() if root.isMetaNode(n) else [n]
		for nn in ns:
			found = False
			for m in root.getInOutNodes(nn):
				comp_m = root[TYPE_COMPARTMENT][m]
				if comp != comp_m:
					if comp_m in key2border_color:
						view_border_color[n] = key2border_color[comp_m]
					else:
						view_border_color[n] = colors[0]
					found = True
					break
			if found:
				break

		if TYPE_COMPARTMENT == type_:
			view_color[n] = key2border_color[root[NAME][n]] if root[NAME][n] in key2border_color else transparent_grey
			continue
		a = 255
		if TYPE_REACTION == type_:
			r, g, b = key2color[get_key(n, graph)]
			if graph.isMetaNode(n):
				a = 100
			view_color[n] = tlp.Color(r, g, b, a)
			for e in graph.getInOutEdges(n):
				if root[UBIQUITOUS][graph.target(e)] or root[UBIQUITOUS][graph.source(e)]:
					view_color[e] = grey
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
	view_border_color = root.getColorProperty(VIEW_BORDER_COLOR)
	view_border_color.setAllNodeValue(white)

	for n in root.getNodes():
		type_ = root[TYPE][n]
		if TYPE_COMPARTMENT == type_:
			view_color[n] = yellow
		elif TYPE_REACTION == type_:
			is_transport = len({root[TYPE_COMPARTMENT][m] for m in root.getInOutNodes(n)}) > 1
			if root.isMetaNode(n):
				view_color[n] = turquoise if is_transport else violet
			else:
				view_color[n] = green if is_transport else blue
			for e in root.getInOutEdges(n):
				if root[UBIQUITOUS][root.target(e)] or root[UBIQUITOUS][root.source(e)]:
					view_color[e] = grey
				else:
					view_color[e] = view_color[n]
		elif TYPE_SPECIES == type_:
			if root[UBIQUITOUS][n]:
				view_color[n] = grey
			else:
				if root.isMetaNode(n):
					view_color[n] = orange
					comp = root[TYPE_COMPARTMENT][n]
					found = False
					for nn in root[VIEW_META_GRAPH][n].getNodes():
						for m in root.getInOutNodes(nn):
							comp_m = root[TYPE_COMPARTMENT][m]
							if comp != comp_m:
								view_border_color[n] = violet
								found = True
								break
						if found:
							break
				else:
					view_color[n] = red