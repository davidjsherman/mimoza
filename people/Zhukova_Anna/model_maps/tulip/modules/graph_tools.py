from tulip import *

def findSubGraphByName(root, name):
	def checkCollection(collection, name):
		new_collection = []
		for element in collection:
			if element:
				if name == element.getName(): return element
				subs = list(element.getSubGraphs())
				if subs: new_collection.extend(subs)
		return checkCollection(new_collection, name) if new_collection else None

	return checkCollection(list(root.getSubGraphs()), name)
	
	
def comp_to_meta_node(meta_graph, comp, out_comp):	
	ns = filter(lambda n: meta_graph["compartment"][n] == comp, meta_graph.getNodes())
	meta_node = meta_graph.createMetaNode(ns, False)
	comp_graph = meta_graph["viewMetaGraph"][meta_node]
	comp_graph.setName("_" + comp)
	meta_graph["viewSize"][meta_node] = getSize(comp_graph)
	meta_graph["viewLabel"][meta_node] = comp
	meta_graph["name"][meta_node] = comp
	meta_graph["compartment"][meta_node] = out_comp
	meta_graph["type"][meta_node] = compartment
	meta_graph["viewShape"][meta_node] = 18
	meta_graph["viewColor"][meta_node] = tlp.Color(200,200,200,80)
	
	
def getSize(gr):
	try:
		ds = tlp.getDefaultPluginParameters("SBMLLayout", gr)
		tlp.applyAlgorithm(gr, ds, "SBMLLayout")
	except:
		pass
	bb = tlp.computeBoundingBox(gr)
	return tlp.Size(bb.width(), bb.height())
	# tlp.Size(bbNew.width(), bbNew.height())
#	w, h = 0, 0
#	for n in gr.getNodes():
#		s = gr["viewSize"][n]
#		w += s.getW()
#		h += s.getH()
#	return tlp.Size(w, h)
