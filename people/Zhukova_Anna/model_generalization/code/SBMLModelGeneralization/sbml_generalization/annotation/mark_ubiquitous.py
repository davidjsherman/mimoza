from sbml_generalization.sbml.reaction_filters import get_participants

__author__ = 'anna'

HAS_ROLE_RELATIONSHIP = 'has_role'

COFACTOR_CHEBI_ID = 'chebi:23357'

UBIQUITOUS_THRESHOLD = 14

# most common ones:
#
# 'IDP', 'dTTP(4-)', 'hydrogencarbonate', 'superoxide', 'water', 'hydron', 'dioxygen', 'CTP(4-)', 'iron(2+)', 'GDP',
# 'NADPH', 'ATP(3-)', 'ATP(4-)', 'coenzyme A(4-)', 'dCTP', 'ADP', 'dAMP(2-)', 'NAD(+)', 'dGMP', 'CMP', 'ATP',
# 'singlet dioxygen', 'UDP(3-)', 'acetyl-CoA(4-)', 'hydroxide', 'dADP', 'FMN(3-)', 'dTDP', 'phosphate', 'dTTP', 'UTP',
# 'ITP', 'FAD', 'NAD(P)H', 'NAD(P)(+)', 'hydrogenphosphate', 'protein', 'GDP(3-)', 'dUTP', 'NAD(P)', 'GMP(2-)', 'FADH2',
# 'UMP', 'NADPH(4-)', 'acyl-CoA(4-)', 'phosphate ion', 'coenzyme A', 'dATP', 'dUMP(2-)', 'GTP(4-)', 'carbon dioxide',
# 'acyl-CoA', 'IDP(3-)', 'dCDP', 'dATP(4-)', 'dGTP', 'CTP', 'GTP', 'ITP(4-)', 'NADP(+)', 'FADH2(2-)', 'dGTP(4-)',
# 'FAD(3-)', 'UDP', 'diphosphate(4-)', 'dGDP', 'oxygen atom', 'dCMP', 'dTMP', 'CDP', 'dUDP',
# 'acetyl-[acyl-carrier protein]', 'AMP', 'hydrogen peroxide', '((18)O)water', 'NADH', 'NAD(1-)', 'ADP(3-)',
# 'AMP(2-)', 'acetyl-CoA', 'NADH(2-)', 'ACP', 'ACP'
#
COMMON_UB_IDS = {'chebi:37568', 'chebi:15422', 'chebi:57783', 'chebi:17625', 'chebi:58115', 'chebi:37565',
                 'chebi:16192', 'chebi:15846', 'chebi:25805', 'chebi:26020', 'chebi:13390', 'chebi:13392',
                 'chebi:43474', 'chebi:25524', 'chebi:37563', 'chebi:16695', 'chebi:30616', 'chebi:58223',
                 'chebi:35780', 'chebi:58342', 'chebi:58189', 'chebi:16908', 'chebi:57540', 'chebi:456216',
                 'chebi:456215', 'chebi:57945', 'chebi:16474', 'chebi:18421', 'chebi:16761', 'chebi:17361',
                 'chebi:26689', 'chebi:29033', 'chebi:18075', 'chebi:18077', 'chebi:15713', 'chebi:17877',
                 'chebi:17544', 'chebi:17677', 'chebi:58210', 'chebi:61429', 'chebi:18361', 'chebi:246422',
                 'chebi:16240', 'chebi:58245', 'chebi:17808', 'chebi:15377', 'chebi:15378', 'chebi:15379',
                 'chebi:17552', 'chebi:16311', 'chebi:16497', 'chebi:15346', 'chebi:17239', 'chebi:57692',
                 'chebi:17013', 'chebi:61404', 'chebi:61402', 'chebi:57299', 'chebi:58307', 'chebi:17659',
                 'chebi:28862', 'chebi:28850', 'chebi:17093', 'chebi:16027', 'chebi:33813', 'chebi:57287',
                 'chebi:57288', 'chebi:16234', 'chebi:16039', 'chebi:16238', 'chebi:36080', 'chebi:16284',
                 'chebi:16526', 'chebi:17984', 'chebi:58280', 'chebi:28846', 'chebi:16174', 'chebi:15996',
                 'chebi:18009', 'chebi:15918', 'chebi:15351', 'chebi:18359', 'chebi:13534', 'chebi:24636'} \
                | {'chebi:15422', 'chebi:15846', 'chebi:15378', 'chebi:16908', 'chebi:16027', 'chebi:16474',
                   'chebi:16761', 'chebi:17361', 'chebi:15713', 'chebi:17877', 'chebi:15366', 'chebi:17544',
                   'chebi:17677', 'chebi:16240', 'chebi:15377', 'chebi:15379', 'chebi:17552', 'chebi:16311',
                   'chebi:15346', 'chebi:17659', 'chebi:28862', 'chebi:16238', 'chebi:16526', 'chebi:17984',
                   'chebi:16174', 'chebi:18009', 'chebi:15351', 'chebi:16039', 'chebi:18421', 'chebi:29033',
                   'chebi:18075', 'chebi:18077', 'chebi:17808', 'chebi:18359', 'chebi:16497', 'chebi:16284',
                   'chebi:28846', 'chebi:15996', 'chebi:17239', 'chebi:37565', 'chebi:18245', 'chebi:57287',
                   'chebi:73342', 'chebi:33813', 'chebi:57783', 'chebi:57945', 'chebi:29375', 'chebi:82680',
                   'chebi:58280', 'chebi:30616', 'chebi:61402', 'chebi:58189', 'chebi:57288', 'chebi:57692',
                   'chebi:58307', 'chebi:28971', 'chebi:17093', 'chebi:456215', 'chebi:13534', 'chebi:73627',
                   'chebi:17330', 'chebi:58107', 'chebi:29325'}

CONJUGATE_ACID_BASE_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of'}
EQUIVALENT_TERM_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of', 'is_tautomer_of'}


def get_ubiquitous_species_set(model, species_id2chebi_id, ontology, threshold=UBIQUITOUS_THRESHOLD):
    """
    The function returns a set of identifiers of ubiquitous species belonging to the given model.
    The species in the model are divided into two groups: ubiquitous ones and the others.
    Ubiquitous species are those participating in more than {@link #threshold threshold number} of reactions.

    :param model: a {@link #libsbml.Model Model} object.
    :param species_id2chebi_id: a mapping between species identifiers (string) and their ChEBI identifiers (string).
    :param ontology: ChEBI ontology.
    :param threshold: (Optional) A minimal number of reactions a species should participate in to become a ubiquitous one.
    The default value is {@link #UBIQUITOUS_THRESHOLD UBIQUITOUS_THRESHOLD}.
    :return: A set of ubiquitous species identifiers.
    """
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
            ubiquitous_chebi_new |= {it.get_id() for it in
                                     ontology.get_equivalents(u_term, relationships=EQUIVALENT_TERM_RELATIONSHIPS)}

    return ubiquitous_chebi_new


def get_cofactors(onto):
    cofactors = set()
    sub_cofactors = onto.get_term(COFACTOR_CHEBI_ID).get_descendants(False)

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
