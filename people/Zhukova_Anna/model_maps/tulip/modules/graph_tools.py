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
