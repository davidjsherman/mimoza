from utils.misc import add2map
from utils.reaction_filters import getReactionParticipants

__author__ = 'anna'

UBIQUITOUS_THRESHOLD = 10

# most common ones, like water, H+, oxygen, NAD, etc.
COMMON_UB_IDS = {'chebi:15346', 'chebi:15378', 'chebi:15379', 'chebi:16526', 'chebi:16240', 'chebi:18009',
                 'chebi:16908', 'chebi:30616', 'chebi:57783', 'chebi:15846', 'chebi:456215', 'chebi:15351',
                 'chebi:18361', 'chebi:29375'}


## The function returns a set of identifiers of ubiquitous species participating in given reactions.
# The species in the model are divided into two groups: ubiquitous ones and the others.
# Ubiquitous species are those participating in more than {@link #threshold threshold number} of reactions.
# @param reactions A collection of {@link #libsbml.Reaction Reaction} objects.
# @param threshold (Optional) A minimal number of reactions a species should participate in to become a ubiquitous one.
# The default value is {@link #UBIQUITOUS_THRESHOLD UBIQUITOUS_THRESHOLD}.
# @return A set of ubiquitous species identifiers.
def getUbiquitousSpeciesSet(reactions, all_species_id2chebi_id, ontology, threshold):
    chebi_id2vote = {}
    for reaction in reactions:
        participants = getReactionParticipants(reaction)
        for element in participants:
            # if we do not have a ChEBI annotation for it,
            # it will be considered ubiquitous anyway
            if not element in all_species_id2chebi_id:
                continue
            chebi_id = all_species_id2chebi_id[element]
            if chebi_id in chebi_id2vote:
                chebi_id2vote[chebi_id] += 1
            else:
                chebi_id2vote[chebi_id] = 1

    ubiquitous_chebi_ids = set()
    # vote2el = {}
    for element, vote in chebi_id2vote.iteritems():
        if vote > threshold:
            ubiquitous_chebi_ids.add(element)
    # #     add2map(vote2el, vote, element)
    # # total = len(chebi_id2vote.keys())
    # # max_ub_number = total * threshold
    # # for vote in sorted(vote2el.keys(), key=lambda v: -v):
    # #     els = vote2el[vote]
    # #     if len(ubiquitous_chebi_ids) + len(els) > max_ub_number:
    # #         break
    # #     ubiquitous_chebi_ids |= els

    ubiquitous_chebi_ids |= COMMON_UB_IDS

    ubiquitous_chebi_ids_new = set()
    for u_id in ubiquitous_chebi_ids:
        u_term = ontology.getTerm(u_id)
        if not u_term:
            continue
        ubiquitous_chebi_ids_new.add(u_id)
        ubiquitous_chebi_ids_new |= {t.getId() for t in ontology.getEqualTerms(u_term)}

    return ubiquitous_chebi_ids_new