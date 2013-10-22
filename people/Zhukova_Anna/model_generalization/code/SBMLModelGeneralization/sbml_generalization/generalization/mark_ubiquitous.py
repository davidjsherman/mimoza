from reaction_filters import getReactionParticipants

COFACTOR_CHEBI_ID = 'chebi:23357'

__author__ = 'anna'

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
                 'chebi:13389', 'chebi:13392', 'chebi:28971', 'chebi:17984'}


## The function returns a set of identifiers of ubiquitous species participating in given reactions.
# The species in the model are divided into two groups: ubiquitous ones and the others.
# Ubiquitous species are those participating in more than {@link #threshold threshold number} of reactions.
# @param reactions A collection of {@link #libsbml.Reaction Reaction} objects.
# @param threshold (Optional) A minimal number of reactions a species should participate in to become a ubiquitous one.
# The default value is {@link #UBIQUITOUS_THRESHOLD UBIQUITOUS_THRESHOLD}.
# @return A set of ubiquitous species identifiers.
def getUbiquitousSpeciesSet(model, species_id2chebi_id, ontology, threshold=UBIQUITOUS_THRESHOLD):
    reactions = model.getListOfReactions()
    chebi2vote = {}
    for reaction in reactions:
        participants = getReactionParticipants(reaction)
        for element in participants:
            # if we do not have a ChEBI annotation for it,
            # it will be considered ubiquitous anyway
            if not element in species_id2chebi_id:
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
        u_term = ontology.getTerm(u_term_id)
        if u_term:
            ubiquitous_chebi_new.add(u_term_id)
            ubiquitous_chebi_new |= {it.getId() for it in ontology.getEquivalentTerms(u_term)}

    return ubiquitous_chebi_new


def getCofactors(onto):
    cofactors = set()
    sub_cofactors = onto.getTerm(COFACTOR_CHEBI_ID).getChildren(False)

    def is_cofactor(t_id):
        if COFACTOR_CHEBI_ID == t_id:
            return True
        return onto.getTerm(t_id) in sub_cofactors

    for it in onto.getRelationshipParticipants('has_role'):
        subj, rel, obj = it
        if rel == 'has_role' and is_cofactor(obj):
            subj_term = onto.getTerm(subj)
            children = {t.getId() for t in onto.getAnyChildren(subj_term, False, set(), relationships={
                'is_conjugate_base_of', 'is_conjugate_acid_of'})}
            equals = {t.getId() for t in onto.getEquivalentTerms(subj_term, relationships={
                'is_conjugate_base_of', 'is_conjugate_acid_of'})}
            cofactors |= {subj} | children | equals
    return cofactors
