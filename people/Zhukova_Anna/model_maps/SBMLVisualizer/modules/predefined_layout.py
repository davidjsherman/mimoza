import tulipgui
from tulip import tlp
from color_keys import key2coord



# def getKey2Layout(graph):
# 	root = graph.getRoot()
# 	view_layout = root.getLayoutProperty("viewLayout")
# 	ubiquitous = root.getBooleanProperty("ubiquitous")
#
# 	key2l = {}
# 	for n in graph.getNodes():
# 		if ubiquitous[n]:
# 			r = graph.getInOutNodes(n).next()
# 			k = get_keys(n, graph, True)[0]
# 			keys = ["{0}+{1}".format(k,l) for l in getKeys(r, graph, True)]
# 		else:
# 			keys = get_keys(n, graph, True)
# 		for k in keys:
# 			key2l[k] = view_layout[n]
#
# 	print key2l


def apply_layout(graph, onto):
	root = graph.getRoot()
	view_layout = root.getLayoutProperty("viewLayout")
	ubiquitous = root.getBooleanProperty("ubiquitous")

	# before = len(key2coord)
	for n in graph.getNodes():
		if ubiquitous[n]:
			if not graph.deg(n):
				continue
			r = graph.getInOutNodes(n).next()
			k = get_keys(n, graph, onto, True)[0]
			keys = ["{0}+{1}".format(k, l) for l in get_keys(r, graph, onto, True)]
		else:
			keys = get_keys(n, graph, onto, True)
		if not keys:
			continue
		found = False
		for key in keys:
			if key in key2coord:
				coord = key2coord[key]
				view_layout[n] = tlp.Coord(coord[0], coord[1])
				found = True
				break
		if not found:
			for key in keys:
				key2coord[key] = view_layout[n]
	#if before < len(key2coord) : print key2coord


def get_keys(n, graph, onto, primary=False):
	root = graph.getRoot()
	ancestor_chebi_id = root.getStringProperty("ancestor_chebi_id")
	chebi_id = root.getStringProperty("chebi_id")
	name = root.getStringProperty("name")
	ubiquitous = root.getBooleanProperty("ubiquitous")

	if 'reaction' == graph["type"][n]:
		transform = lambda nds: "r_" + "_".join(sorted([get_keys(it, graph, onto, primary)[0] for it in nds]))
		return [transform(graph.getInOutNodes(n)), transform(filter(lambda nd: not ubiquitous[nd], graph.getInOutNodes(n)))]
	else:
		key = None
		if not primary:
			key = ancestor_chebi_id[n]
		if not key:
			key = chebi_id[n]
		if not key:
			return [name[n]]
		t = onto.getTerm(key)
		if t:
			key = get_primary_id(t, onto)
		return [key]


def get_primary_id(term, onto):
	terms = {term} | onto.getEquivalentTerms(term, None, 0, {'is_conjugate_base_of', 'is_conjugate_acid_of'})
	return sorted([t.getId() for t in terms])[0]