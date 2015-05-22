ID = 'id'
TERM = 'term'
T = 't'
NAME = 'name'

ALL_COMPARTMENTS = 'all_comp_view'

ANCESTOR_ID = 'anc_id'
ANCESTOR_TERM = 'anc_term'
ANCESTOR_NAME = "anc_name"

COMPARTMENT_ID = "c_id"
COMPARTMENT_NAME = "c_name"
RELATED_COMPARTMENT_IDS = "rel_c_ids"

DIRECTION = 'direction'

VIEW_COLOR = "viewColor"

VIEW_SHAPE = "viewShape"
VIEW_LAYOUT = "viewLayout"
VIEW_SIZE = "viewSize"

UBIQUITOUS = 'ub'

STOICHIOMETRY = 'stoich'
REVERSIBLE = "rev"
TRANSPORT = "tr"
INNER = "inner"

VIEW_META_GRAPH = 'viewMetaGraph'

FAKE = "fake"

CLONE_ID = "clone_id"

COLOR = "color"

HEIGHT = "h"
WIDTH = "w"

PRODUCTS = 'ps'
REACTANTS = 'rs'
FORMULA = "f"

CYTOPLASM = "cytoplasm"
ORGANELLES = "organelles"
EXTRACELLULAR = 'extracellular'

START = "start"
END = "end"

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
TYPE_2_BG_TYPE = {TYPE_SPECIES: TYPE_BG_SPECIES, TYPE_REACTION: TYPE_BG_REACTION, TYPE_COMPARTMENT: TYPE_BG_COMPARTMENT}

CIRCLE_SHAPE = 14
SQUARE_SHAPE = 18

REACTION_SHAPE = SQUARE_SHAPE
SPECIES_SHAPE = CIRCLE_SHAPE
COMPARTMENT_SHAPE = SQUARE_SHAPE