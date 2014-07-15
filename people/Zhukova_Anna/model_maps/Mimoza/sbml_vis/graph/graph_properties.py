ID = 'id'
ANNOTATION = 'annotation'
NAME = 'name'

ANCESTOR_ID = 'ancestor_id'
ANCESTOR_ANNOTATION = 'ancestor_annotation'
ANCESTOR_NAME = "ancestor_name"

COMPARTMENT = "compartment"

VIEW_COLOR = "viewColor"

VIEW_SHAPE = "viewShape"
VIEW_LAYOUT = "viewLayout"
VIEW_SIZE = "viewSize"

UBIQUITOUS = 'ubiquitous'

STOICHIOMETRY = 'stoichiometry'
REVERSIBLE = "reversible"
TRANSPORT = "transport"

VIEW_META_GRAPH = 'viewMetaGraph'

MAX_ZOOM = "max_zoom"
MIN_ZOOM = "min_zoom"

FAKE = "fake"

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
TYPE_2_BG_TYPE = {TYPE_SPECIES: TYPE_BG_SPECIES, TYPE_REACTION: TYPE_BG_REACTION, TYPE_COMPARTMENT: TYPE_BG_COMPARTMENT}

CIRCLE_SHAPE = 14
SQUARE_SHAPE = 18

REACTION_SHAPE = SQUARE_SHAPE
SPECIES_SHAPE = CIRCLE_SHAPE
COMPARTMENT_SHAPE = SQUARE_SHAPE