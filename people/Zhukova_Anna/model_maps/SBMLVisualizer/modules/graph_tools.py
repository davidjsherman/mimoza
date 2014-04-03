ID = 'id'
ANNOTATION = 'annotation'
NAME = 'name'

ANCESTOR_ID = 'ancestor_id'
ANCESTOR_ANNOTATION = 'ancestor_annotation'
ANCESTOR_NAME = "ancestor_name"

COMPARTMENT = "compartment"
REAL_COMPARTMENT = "real_compartment"

VIEW_COLOR = "viewColor"

VIEW_SHAPE = "viewShape"
VIEW_LAYOUT = "viewLayout"
VIEW_SIZE = "viewSize"

UBIQUITOUS = 'ubiquitous'

STOICHIOMETRY = 'stoichiometry'
REVERSIBLE = "reversible"
TRANSPORT = "transport"

VIEW_META_GRAPH = 'viewMetaGraph'

CYTOPLASM = "cytoplasm"
ORGANELLES = "organelles"
EXTRACELLULAR = 'extracellular'

TYPE = 'type'
TYPE_SPECIES = 1
TYPE_REACTION = 2
TYPE_COMPARTMENT = 3
TYPE_ENTITY = [TYPE_SPECIES, TYPE_REACTION, TYPE_COMPARTMENT]
TYPE_BG_SPECIES = 4
TYPE_BG_REACTION = 5
TYPE_BG_COMPARTMENT = 6
TYPE_BG = [TYPE_BG_REACTION, TYPE_BG_SPECIES, TYPE_BG_COMPARTMENT]
TYPE_EDGE = 0

SQUARE_SHAPE = 18
ROUND_SHAPE = 14


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
