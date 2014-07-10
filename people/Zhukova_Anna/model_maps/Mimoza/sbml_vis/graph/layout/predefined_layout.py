from sbml_vis.graph.color.color_keys import key2coord
from sbml_vis.graph.graph_properties import *


CONJUGATE_ACID_OF = 'is_conjugate_acid_of'
CONJUGATE_BASE_OF = 'is_conjugate_base_of'


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
	view_layout = root.getLayoutProperty(VIEW_LAYOUT)
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)

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
		coord = next((key2coord[key] for key in keys if key in key2coord), None)
		if coord:
			view_layout[n] = coord
		else:
			for key in keys:
				key2coord[key] = view_layout[n]
	#if before < len(key2coord) : print key2coord


def get_keys(n, graph, onto, primary=False):
	root = graph.getRoot()
	ancestor_chebi_id = root.getStringProperty(ANCESTOR_ANNOTATION)
	chebi_id = root.getStringProperty(ANNOTATION)
	name = root.getStringProperty(NAME)
	ubiquitous = root.getBooleanProperty(UBIQUITOUS)

	if TYPE_REACTION == graph[TYPE][n]:
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
	terms = {term} | onto.getEquivalentTerms(term, None, 0, {CONJUGATE_BASE_OF, CONJUGATE_ACID_OF})
	return sorted([t.getId() for t in terms])[0]