def find_subgraph_by_name(root, name):
	def check_collection(collection, name):
		new_collection = []
		for element in collection:
			if element:
				if name == element.getName():
					return element
				subs = list(element.getSubGraphs())
				if subs:
					new_collection.extend(subs)
		return check_collection(new_collection, name) if new_collection else None

	return check_collection(list(root.getSubGraphs()), name)
