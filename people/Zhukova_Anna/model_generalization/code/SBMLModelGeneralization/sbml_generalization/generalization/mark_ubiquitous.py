from reaction_filters import get_participants

__author__ = 'anna'

HAS_ROLE_RELATIONSHIP = 'has_role'

COFACTOR_CHEBI_ID = 'chebi:23357'

UBIQUITOUS_THRESHOLD = 14

# most common ones, like water, H+, oxygen, NAD, etc.
COMMON_UB_IDS = {'chebi:37568', 'chebi:57783', 'chebi:17625', 'chebi:37563', 'chebi:17552', 'chebi:17361',
                 'chebi:16311', 'chebi:16192', 'chebi:15846', 'chebi:61429', 'chebi:16234', 'chebi:16174',
                 'chebi:58210', 'chebi:16171', 'chebi:36080', 'chebi:15713', 'chebi:16238', 'chebi:43474',
                 'chebi:15378', 'chebi:15379', 'chebi:58115', 'chebi:29375', 'chebi:16695', 'chebi:58342',
                 'chebi:15346', 'chebi:37565', 'chebi:16526', 'chebi:17544', 'chebi:17013', 'chebi:61404',
                 'chebi:30616', 'chebi:18009', 'chebi:58307', 'chebi:58223', 'chebi:18361', 'chebi:28862',
                 'chebi:15918', 'chebi:246422', 'chebi:28850', 'chebi:16240', 'chebi:58245', 'chebi:16908',
                 'chebi:13534', 'chebi:456216', 'chebi:456215', 'chebi:15351', 'chebi:30089', 'chebi:15422',
                 'chebi:57299', 'chebi:25805', 'chebi:26689', 'chebi:13390', 'chebi:57540', 'chebi:25524',
                 'chebi:13389', 'chebi:13392', 'chebi:28971', 'chebi:17984', 'chebi:29888', 'chebi:26020',
                 'chebi:73342', 'chebi:35780', 'chebi:26078'}

CONJUGATE_ACID_BASE_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of'}


## The function returns a set of identifiers of ubiquitous species participating in given reactions.
# The species in the model are divided into two groups: ubiquitous ones and the others.
# Ubiquitous species are those participating in more than {@link #threshold threshold number} of reactions.
# @param reactions A collection of {@link #libsbml.Reaction Reaction} objects.
# @param threshold (Optional) A minimal number of reactions a species should participate in to become a ubiquitous one.
# The default value is {@link #UBIQUITOUS_THRESHOLD UBIQUITOUS_THRESHOLD}.
# @return A set of ubiquitous species identifiers.
def get_ubiquitous_species_set(model, species_id2chebi_id, ontology, threshold=UBIQUITOUS_THRESHOLD):
	reactions = model.getListOfReactions()
	chebi2vote = {}
	for reaction in reactions:
		participants = get_participants(reaction)
		for element in participants:
			# if we do not have a ChEBI annotation for it,
			# it will be considered ubiquitous anyway
			if element not in species_id2chebi_id:
				continue
			chebi_id = species_id2chebi_id[element]
			compartment = model.getSpecies(element).getCompartment()
			key = chebi_id, compartment
			if key in chebi2vote:
				chebi2vote[key] += 1
			else:
				chebi2vote[key] = 1

	ubiquitous_chebi = set()
	for element, vote in chebi2vote.iteritems():
		if vote > threshold:
			ubiquitous_chebi.add(element[0])

	ubiquitous_chebi |= COMMON_UB_IDS

	ubiquitous_chebi_new = set()
	for u_term_id in ubiquitous_chebi:
		u_term = ontology.get_term(u_term_id)
		if u_term:
			ubiquitous_chebi_new.add(u_term_id)
			ubiquitous_chebi_new |= {it.get_id() for it in ontology.get_equivalents(u_term)}

	return ubiquitous_chebi_new


def get_cofactors(onto):
	cofactors = set()
	sub_cofactors = onto.get_term(COFACTOR_CHEBI_ID).get_ancestors(False)

	def is_cofactor(t_id):
		if COFACTOR_CHEBI_ID == t_id:
			return True
		return onto.get_term(t_id) in sub_cofactors

	for it in onto.get_relationship_participants(HAS_ROLE_RELATIONSHIP):
		subj, rel, obj = it
		if rel == HAS_ROLE_RELATIONSHIP and is_cofactor(obj):
			subj_term = onto.get_term(subj)
			children = {t.get_id() for t in
			            onto.get_generalized_descendants(subj_term, False, set(), CONJUGATE_ACID_BASE_RELATIONSHIPS)}
			equals = {t.get_id() for t in onto.get_equivalents(subj_term, CONJUGATE_ACID_BASE_RELATIONSHIPS)}
			cofactors |= {subj} | children | equals
	return cofactors
