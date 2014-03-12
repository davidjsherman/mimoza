
TERM_ID = 'term_id'

VIEW_BORDER_COLOR = "viewBorderColor"

VIEW_COLOR = "viewColor"

UBIQUITOUS = 'ubiquitous'

NAME = 'name'

VIEW_META_GRAPH = 'viewMetaGraph'

TYPE_COMPARTMENT = 'compartment'

CYTOPLASM = "cytoplasm"

ORGANELLES = "organelles"

TYPE_SPECIES = 'species'

TYPE_REACTION = 'reaction'

TYPE_BG = 'background'

TYPE = 'type'

ID = 'id'

ANCESTOR_TERM_ID = 'ancestor_term_id'

ANCESTOR_ID = 'ancestor_id'

COMPARTMENT = "compartment"

EXTRACELLULAR = 'extracellular'

SQUARE_SHAPE = 18

STOICHIOMETRY = 'stoichiometry'

VIEW_LABEL = "viewLabel"

GENE_ASSOCIATION = "geneAssociation"

VIEW_SIZE = "viewSize"

ANCESTOR_NAME = "ancestor_name"

CLONE = "clone"

VIEW_SHAPE = "viewShape"

VIEW_SELECTION = "viewSelection"

VIEW_LAYOUT = "viewLayout"

VIEW_BORDER_WIDTH = "viewBorderWidth"

REVERSIBLE = "reversible"

REAL_COMPARTMENT = "real_compartment"


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
