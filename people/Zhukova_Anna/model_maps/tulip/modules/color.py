import colorsys
from tulip import tlp

__author__ = 'anna'


grey = tlp.Color(180, 180, 180)
transparent_grey = tlp.Color(200, 200, 200, 80)
light_red = tlp.Color(255, 100, 100)
light_blue = tlp.Color(100, 100, 255)
white = tlp.Color(255, 255, 255)
transparent = tlp.Color(0, 0, 0, 0)


def get_key(n, graph):
	root = graph.getRoot()
	type_ = root['type'][n]
	if 'reaction' == type_:
		an_id = root['ancestor_id'][n]
		if an_id:
			return an_id
		return root['id'][n]
	if 'species' == type_:
		an_ch = root['ancestor_chebi_id'][n]
		if an_ch:
			return an_ch
		an_id = root['ancestor_id'][n]
		if an_id:
			return an_id
		ch = root['chebi_id'][n]
		if ch:
			return ch
		return root['id'][n]
	return None


def color(graph):
	root = graph.getRoot()
	view_color = root.getColorProperty("viewColor")
	view_border_color = root.getColorProperty("viewBorderColor")

	keys = {get_key(n, graph) for n in graph.getNodes() if root['type'][n] == 'reaction'}
	i = len(keys)

	colors = [colorsys.hsv_to_rgb(x * 1.0 / i, 0.5, 0.8) for x in xrange(i)]
	colors = [(int(255 * r), int(255 * g), int(255 * b)) for (r, g, b) in colors]
	key2color = dict(zip(keys, colors))

	keys = {get_key(n, graph) for n in graph.getNodes() if root['type'][n] == 'species'}
	i = len(keys)

	colors = [colorsys.hsv_to_rgb(x * 1.0 / i, 0.5, 0.8) for x in xrange(i)]
	colors = [(int(255 * r), int(255 * g), int(255 * b)) for (r, g, b) in colors]

	key2color.update(dict(zip(keys, colors)))

	root = graph.getRoot()
	organelles = root.getAttribute("organelles").split(";")
	cyto = root.getAttribute("cytoplasm")
	i = len(organelles) + 2
	colors = [colorsys.hsv_to_rgb(x * 1.0 / i, 0.5, 0.8) for x in xrange(i)]
	colors = [tlp.Color(int(255 * r), int(255 * g), int(255 * b)) for (r, g, b) in colors]
	key2border_color = dict(zip(organelles + [cyto], colors[1:]))

	view_border_color.setAllNodeValue(white)

	for n in graph.getNodes():
		type_ = root['type'][n]
		comp = root['compartment'][n]
		ns = root['viewMetaGraph'][n].getNodes() if root.isMetaNode(n) else [n]
		for nn in ns:
			found = False
			for m in root.getInOutNodes(nn):
				comp_m = root['compartment'][m]
				if comp != comp_m:
					if comp_m in key2border_color:
						view_border_color[n] = key2border_color[comp_m]
					else:
						view_border_color[n] = colors[0]
					found = True
					break
			if found:
				break

		if 'compartment' == type_:
			view_color[n] = key2border_color[root['name'][n]] if root['name'][n] in key2border_color else transparent_grey
			continue
		a = 255
		if 'reaction' == type_:
			r, g, b = key2color[get_key(n, graph)]
			if graph.isMetaNode(n):
				a = 100
			view_color[n] = tlp.Color(r, g, b, a)
			for e in graph.getInOutEdges(n):
				if root['ubiquitous'][graph.target(e)] or root['ubiquitous'][graph.source(e)]:
					view_color[e] = grey
				else:
					view_color[e] = tlp.Color(r, g, b, 100 if graph.isMetaEdge(e) else 255)
		if 'species' == type_:
			if root['ubiquitous'][n]:
				r, g, b = 180, 180, 180
			else:
				r, g, b = key2color[get_key(n, graph)]
				if graph.isMetaNode(n):
					a = 100
			view_color[n] = tlp.Color(r, g, b, a)
