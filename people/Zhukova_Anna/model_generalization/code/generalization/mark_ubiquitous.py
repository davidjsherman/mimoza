from utils.reaction_filters import getReactionParticipants

__author__ = 'anna'

UBIQUITOUS_THRESHOLD = 10

# most common ones, like water, H+, oxygen, NAD, etc.
COMMON_UB_IDS = {'chebi:37568', 'chebi:57783', 'chebi:17625', 'chebi:37563', 'chebi:17552', 'chebi:17361',
                 'chebi:16311', 'chebi:16192', 'chebi:15846', 'chebi:61429', 'chebi:16234', 'chebi:16174',
                 'chebi:58210', 'chebi:16171', 'chebi:36080', 'chebi:15713', 'chebi:16238', 'chebi:43474',
                 'chebi:15378', 'chebi:15379', 'chebi:58115', 'chebi:29375', 'chebi:16695', 'chebi:58342',
                 'chebi:15346', 'chebi:37565', 'chebi:16526', 'chebi:17544', 'chebi:17013', 'chebi:61404',
                 'chebi:30616', 'chebi:18009', 'chebi:58307', 'chebi:58223', 'chebi:18361', 'chebi:28862',
                 'chebi:15918', 'chebi:246422', 'chebi:28850', 'chebi:16240', 'chebi:58245', 'chebi:16908',
                 'chebi:13534', 'chebi:456216', 'chebi:456215', 'chebi:15351', 'chebi:30089', 'chebi:15422',
                 'chebi:57299', 'chebi:unknown'}


## The function returns a set of identifiers of ubiquitous species participating in given reactions.
# The species in the model are divided into two groups: ubiquitous ones and the others.
# Ubiquitous species are those participating in more than {@link #threshold threshold number} of reactions.
# @param reactions A collection of {@link #libsbml.Reaction Reaction} objects.
# @param threshold (Optional) A minimal number of reactions a species should participate in to become a ubiquitous one.
# The default value is {@link #UBIQUITOUS_THRESHOLD UBIQUITOUS_THRESHOLD}.
# @return A set of ubiquitous species identifiers.
def getUbiquitousSpeciesSet(reactions, species_id2chebi, ontology, threshold=UBIQUITOUS_THRESHOLD):
    chebi2vote = {}
    for reaction in reactions:
        participants = getReactionParticipants(reaction)
        for element in participants:
            # if we do not have a ChEBI annotation for it,
            # it will be considered ubiquitous anyway
            if not element in species_id2chebi:
                continue
            chebi = species_id2chebi[element]
            if chebi in chebi2vote:
                chebi2vote[chebi] += 1
            else:
                chebi2vote[chebi] = 1

    ubiquitous_chebi = set()
    for element, vote in chebi2vote.iteritems():
        if vote > threshold:
            ubiquitous_chebi.add(element)

    ubiquitous_chebi |= {ontology.getTerm(it) for it in COMMON_UB_IDS}

    ubiquitous_chebi_new = set()
    for u_term in ubiquitous_chebi:
        if u_term:
            ubiquitous_chebi_new.add(u_term)
            ubiquitous_chebi_new |= ontology.getEqualTerms(u_term)

    return ubiquitous_chebi_new