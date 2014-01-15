import colorsys
from tulip import tlp

__author__ = 'anna'


grey = tlp.Color(180, 180, 180)
transparent_grey = tlp.Color(200, 200, 200, 80)
light_red = tlp.Color(255, 100, 100)
light_blue = tlp.Color(100, 100, 255)
white = tlp.Color(255, 255, 255)
transparent = tlp.Color(0, 0, 0, 0)


def getKey(n, graph):
	type_ = graph['type'][n]
	if 'reaction' == type_:
		an_id = graph['ancestor_id'][n]
		if an_id:
			return an_id
		return graph['id'][n]
	if 'species' == type_:
		an_ch = graph['ancestor_chebi_id'][n]
		if an_ch:
			return an_ch
		an_id = graph['ancestor_id'][n]
		if an_id:
			return an_id
		ch = graph['chebi_id'][n]
		if ch:
			return ch
		return graph['id'][n]
	return None


def color(graph):
	viewColor =  graph.getColorProperty("viewColor")
	viewBorderColor =  graph.getColorProperty("viewBorderColor")

	keys = {getKey(n, graph) for n in graph.getNodes() if graph['type'][n] == 'reaction'}
	i = len(keys)

	colors = [colorsys.hsv_to_rgb(x * 1.0 / i, 0.5, 0.8) for x in xrange(i)]
	colors = [(int(255 * r), int(255 * g), int(255 * b)) for (r, g, b) in colors]
	key2color = dict(zip(keys, colors))

	keys = {getKey(n, graph) for n in graph.getNodes() if graph['type'][n] == 'species'}
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


	viewBorderColor.setAllNodeValue(white)

	for n in graph.getNodes():
		type_ = graph['type'][n]
		comp = graph['compartment'][n]
		ns = root['viewMetaGraph'][n].getNodes() if root.isMetaNode(n) else [n]
		for nn in ns:
			found = False
			for m in root.getInOutNodes(nn):
				comp_m = graph['compartment'][m]
				if comp != comp_m:
					if comp_m in key2border_color:
						viewBorderColor[n] = key2border_color[comp_m]
					else:
						viewBorderColor[n] = colors[0]
					found = True
					break
			if found: break

		if 'compartment' == type_:
			viewColor[n] = transparent_grey
			continue
		a = 255
		if 'reaction' == type_:
			r, g, b = key2color[getKey(n, graph)]
			if graph.isMetaNode(n):
				a = 100
			viewColor[n] = tlp.Color(r, g, b, a)
			for e in graph.getInOutEdges(n):
				if graph['ubiquitous'][graph.target(e)] or graph['ubiquitous'][graph.source(e)]:
					viewColor[e] = grey
				else:
					viewColor[e] = tlp.Color(r, g, b, 100 if graph.isMetaEdge(e) else 255)
		if 'species' == type_:
			if graph['ubiquitous'][n]:
				r, g, b = 180, 180, 180
			else:
				r, g, b = key2color[getKey(n, graph)]
				if graph.isMetaNode(n):
					a = 100
			viewColor[n] = tlp.Color(r, g, b, a)
