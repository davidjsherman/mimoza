from generalization.mark_ubiquitous import getUbiquitousSpeciesSet
from utils.annotate_with_chebi import get_species_to_chebi
from utils.logger import log
from utils.misc import add_to_map, invert_map
from utils.obo_ontology import Term, subOntology
from generalization.reaction_filters import getReactants, getProducts, filterReactionByNotTransport
from generalization.sbml_helper import remove_is_a_reactions, save_as_chain_shortened_sbml

__author__ = 'anna'

EQUIVALENT_TERM_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of', 'is_tautomer_of'}


def getReactions2Factor(reactions, term_id2clu, s_id2term_id):
    vk2r = {}
    for r in reactions:
        key = getVerticalKey(r, term_id2clu, s_id2term_id)
        add_to_map(vk2r, key, r)
    return vk2r.values()


def getVerticalKey(r, term_id2clu, s_id2term_id):
    ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes \
        = getKeyElements(r, term_id2clu, s_id2term_id)
    if r.getReversible() and needToReverse(
            (ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes,)):
        return ubiquitous_products, ubiquitous_reactants, specific_product_classes, specific_reactant_classes
    return ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes


def needToReverse((ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes, )):
    return (ubiquitous_reactants > ubiquitous_products) or (
        not ubiquitous_reactants and not ubiquitous_products and specific_reactant_classes > specific_product_classes)


def getKeyElements(r, term_id2clu, s_id2term_id):
    reactants, products = getReactants(r), getProducts(r)
    chebi_transform = lambda s_ids: {s_id2term_id[s_id] if (s_id in s_id2term_id) else s_id for s_id in s_ids}
    reactants, products = chebi_transform(reactants), chebi_transform(products)

    def classify(term_ids):
        specific, ubiquitous = [], []
        for t in term_ids:
            if t in term_id2clu:
                specific.append(term_id2clu[t])
            else:
                ubiquitous.append(t)
        transform = lambda collection: tuple(sorted(collection))
        return transform(specific), transform(ubiquitous)

    specific_reactant_classes, ubiquitous_reactants = classify(reactants)
    specific_product_classes, ubiquitous_products = classify(products)
    return ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes


def alignedToVKey(r, term_id2clu, s_id2term_id):
    if not r.getReversible():
        return True
    return not needToReverse(getKeyElements(r, term_id2clu, s_id2term_id))


def getReaction2cluster(reactions, term_id2clu, s_id2term_id):
    rs_clusters = getReactions2Factor(reactions, term_id2clu, s_id2term_id)
    r2clu, i = {}, 0
    for rs in rs_clusters:
        for r in rs:
            r2clu[r] = i
        i += 1
    return r2clu


def getRReactionsByTerm(t_id, reactions, term_id2s_ids):
    return filter(lambda r: len(term_id2s_ids[t_id] & getReactants(r)) > 0, reactions)


def getPReactionsByTerm(t_id, reactions, term_id2s_ids):
    return filter(lambda r: len(term_id2s_ids[t_id] & getProducts(r)) > 0, reactions)


def getReactionsByTerm(t_id, reactions, term_id2s_ids):
    return filter(lambda r: len(term_id2s_ids[t_id] & (getReactants(r) | getProducts(r))) > 0, reactions)


def getRReactionsBySpecies(s_id, reactions):
    return filter(lambda r: s_id in getReactants(r), reactions)


def getPReactionsBySpecies(s_id, reactions):
    return filter(lambda r: s_id in getProducts(r), reactions)


def getReactionsBySpecies(s_id, reactions):
    return filter(lambda r: s_id in (getReactants(r) | getProducts(r)), reactions)


def mergeBasedOnNeighbours(lst):
    new_lst = []
    for neighbours, terms in lst:
        neighbours = set(neighbours)
        to_remove = []
        for (new_neighbours, new_terms) in new_lst:
            if neighbours & new_neighbours:
                neighbours |= new_neighbours
                terms |= new_terms
                to_remove.append((new_neighbours, new_terms))
        new_lst = filter(lambda it: not it in to_remove, new_lst)
        new_lst.append((neighbours, terms))
    return new_lst


def maximize(reactions, term_id2clu, species_id2term_id):
    clu2term_ids = invert_map(term_id2clu)
    term_id2s_ids = invert_map(species_id2term_id)

    r2clu = getReaction2cluster(reactions, term_id2clu, species_id2term_id)

    for (clu, term_ids) in clu2term_ids.iteritems():
        if len(term_ids) <= 1:
            continue
        neighbours2term_ids = {}
        for t_id in term_ids:
            # reactions this t_id participated in
            transform_r = lambda r: ("in", r2clu[r]) if alignedToVKey(r, term_id2clu, species_id2term_id) else (
                "out", r2clu[r])
            transform_p = lambda r: ("out", r2clu[r]) if alignedToVKey(r, term_id2clu, species_id2term_id) else (
                "in", r2clu[r])
            neighbours = {transform_r(r) for r in getRReactionsByTerm(t_id, reactions, term_id2s_ids)} | \
                         {transform_p(r) for r in getPReactionsByTerm(t_id, reactions, term_id2s_ids)}
            key = tuple(sorted(neighbours))
            add_to_map(neighbours2term_ids, key, t_id)
        new_lst = mergeBasedOnNeighbours(neighbours2term_ids.iteritems())
        if len(new_lst) > 1:
            i = 0
            for neighbours, term_ids in new_lst:
                n_clu = clu + (i,)
                i += 1
                for t in term_ids:
                    term_id2clu[t] = n_clu
    return term_id2clu


def computeEq0(interesting_term_ids):
    clu = (0,)
    return {term_id: clu for term_id in interesting_term_ids}


def getConflicts(reactions, term_ids, species_id2term_id):
    r2term_ids = {}
    term2s_ids = invert_map(species_id2term_id)
    for t_id in term_ids:
        for r in getReactionsByTerm(t_id, reactions, term2s_ids):
            add_to_map(r2term_ids, r, t_id)
    return filter(lambda terms: len(terms) > 1, r2term_ids.values())


def fixStoich(reactions, term_id2clu, species_id2term_id, onto):
    clu2term_ids = invert_map(term_id2clu)
    for clu, term_ids in clu2term_ids.iteritems():
        if len(term_ids) <= 1:
            continue
        conflicts = getConflicts(reactions, term_ids, species_id2term_id)
        if not conflicts:
            continue
            # print [onto.getTerm(t).getName() for t in term_ids]
        # print " >> ", [{onto.getTerm(n).getName() for n in ns} for ns in conflicts]
        t_sets = partition(term_ids, onto, conflicts)
        i = 0
        for ts in t_sets:
            # print "---> ", [onto.getTerm(t).getName() for t in ts]
            i += 1
            n_clu = clu + (i,)
            for t in ts:
                term_id2clu[t] = n_clu
    return term_id2clu


def getParentOptions(term_ids, onto):
    options = onto.commonPts({onto.getTerm(t) for t in term_ids})
    if not options:
        options = onto.getRoots()
    result = set()
    for t in options:
        result |= onto.getAnyChildren(t, False, set()) | onto.getEquivalentTerms(t) | {t}
    return result


def getPsiSet(onto, term_ids, conflicts):
    def good(t_set, conflicts):
        if not t_set:
            return False
        if len(t_set) == 1:
            return True
        good = True
        for c_ts in conflicts:
            if len(t_set & c_ts) > 1:
                good = False
                break
        return good

    get_covered_terms = lambda t: {t.getId() for t in
                                   (onto.getAnyChildren(t, False, set()) | {t} | onto.getEquivalentTerms(t))} & term_ids

    # the least common ancestors, or roots if there are none
    Ts = onto.commonPts({onto.getTerm(t) for t in term_ids})
    if not Ts:
        Ts = onto.getRoots()

    # sets defined by the least common ancestors
    basics, psi, set2score = [], set(), {}
    for T in Ts:
        element = get_covered_terms(T)
        basics.append(element)
        element = tuple(sorted(element))
        level = onto.getLevel(T)
        set2score[element] = (3, sum(level)/len(level), sum(level)/len(level))
        psi.add(element)

    # sets defined by the least common ancestors' children
    for T in Ts:
        options = onto.getAnyChildren(T, False, set())
        for t in options:
            t_set = get_covered_terms(t)
            if len(t_set) == 0:
                continue
            element = tuple(sorted(t_set))
            psi.add(element)
            level = onto.getLevel(t)
            set2score[element] = (3, sum(level)/len(level), sum(level)/len(level))

            # compliment sets of those defined by the least common ancestors' children
            for basic in basics:
                compl_set = basic - t_set
                if len(compl_set) > 0:
                    c_element = tuple(sorted(compl_set))
                    if c_element in psi:
                        continue
                    psi.add(c_element)
                    set2score[c_element] = avg_tup(set2score[element])
                    # if len(psi) > 50:
                    #     psi = {tuple(t) for t in filter(lambda it: good(set(it), conflicts), psi)}

    # for t in terms:
    #     element = (t,)
    #     psi.add(element)
    #     level = onto.getLevel(t)
    #     set2score[element] = 1#(3, max(level), min(level))

    # the differences between sets already in Psi
    to_add = set()
    ps = list(psi)
    i = 0
    for s in psi:
        i += 1
        for ss in ps[i:]:
            sss = tuple(sorted(set(s) - set(ss)))
            if sss and not sss in psi:
                to_add.add(sss)
                set2score[sss] = avg_tup(set2score[s])
            sss = tuple(sorted(set(ss) - set(s)))
            if sss and not sss in psi:
                to_add.add(sss)
                set2score[sss] = avg_tup(set2score[ss])
    psi |= to_add

    return filter(lambda s: good(set(s), conflicts), psi), set2score


def avg_tup(u):
    i0, j0, k0 = u
    return i0 - 1, j0, k0


def partition(term_ids, onto, conflicts):
    psi, set2score = getPsiSet(onto, term_ids, conflicts)
    # for s, score in set2score.iteritems():
    #     print [t.getName() for t in s], " ", score
    parts = list(reversed(greedy(term_ids, psi, set2score)))
    i = 1
    for part in parts:
        for o_part in parts[i:]:
            if o_part & part:
                part -= o_part
        i += 1
    return parts


def greedy(terms, psi, set2score):
    phi = []
    # for s in sorted(psi, key=lambda it:-len(it)):
    #     if len(s) > 1:
    #         print "?", [it.getName() for it in s]
    terms = set(terms)
    while terms and psi:
        s = max(psi, key=lambda it: (len(set(it) & terms), set2score[it]))
        # print set2score[s], " ", len(set(s) & terms)
        phi.append(s)
        terms -= set(s)
        psi.remove(s)
    return [set(it) for it in phi]


# def cluster2term(term_ids, onto):
#     # print "ROOTS ", [t.getName() for t in onto.getRoots()]
#     options = onto.commonPts({onto.getTerm(t) for t in term_ids})
#     if not options:
#         options = onto.getRoots()
#     return options.pop()


# def computeRepresentatives(term2clu, clu2term, onto):
#     clu2t, t2clu = {}, {}
#     for clu, terms in clu2term.iteritems():
#         T = cluster2term(terms, onto)
#         clu2t[clu] = T
#         add2map(t2clu, T, clu)
#     Ts = list(t2clu.keys())
#     i = 0
#     tr = lambda it: onto.getAnyChildren(it, False, set()) | onto.getEqualTerms(it, None, 0, set())
#     t2not = {}
#     for t in Ts:
#         kids = tr(t)
#         i += 1
#         for o_t in Ts[i:]:
#             if tr(o_t) & kids:
#                 if o_t in kids:
#                     add2map(t2not, t, o_t)
#                 else:
#                     add2map(t2not, o_t, t)
#     for clu, terms in clu2term.iteritems():
#         T = clu2t[clu]
#         name = T.getName()
#         if T in t2not:
#             name = name + ", but not " + ", nor ".join([t.getName() for t in t2not[T]])
#         for t in terms:
#             term2clu[t] = (name, list(T.getAllIds()))
#     return term2clu


def update(term_id2clu, onto):
    clu2term_ids = invert_map(term_id2clu)
    used = set()
    i = 0
    for clu, term_ids in clu2term_ids.iteritems():
        terms = {onto.getTerm(t) for t in term_ids}
        options = set(onto.commonPts(terms)) - used
        if options:
            T = options.pop()
        else:
            T = Term(t_id="chebi:unknown_{0}".format(i), name=' or '.join([t.getName() for t in terms]))
            onto.addTerm(T)
            i += 1
        used.add(T)
        for t in term_ids:
            term_id2clu[t] = T.getId()
    return term_id2clu


def filterClu2Terms(term2clu):
    clu2term = invert_map(term2clu)
    for clu, terms in clu2term.iteritems():
        if len(terms) <= 1:
            del term2clu[terms.pop()]


def printClusters(term_id2clu, onto):
    clu2term_id = invert_map(term_id2clu)
    print "   quotient species sets:"
    for clu, term_ids in clu2term_id.iteritems():
        if len(term_ids) == 1:
            continue
        print "     (", len(term_ids), ") ", [onto.getTerm(it).getName() for it in term_ids]
        print


def printFinalClusters(term_id2clu, onto):
    clu2term = invert_map(term_id2clu)
    print "result quotient species sets:"
    blueprint = []
    for clu in sorted(clu2term.keys(), key=lambda k: -len(clu2term[k])):
        term_ids = clu2term[clu]
        if len(term_ids) == 1:
            continue
        blueprint.append(len(term_ids))
        print "   ", onto.getTerm(clu).getName(), " (", len(term_ids), ") <-> ", [onto.getTerm(it).getName() for it in
                                                                                  term_ids]
    print "   ", sorted(blueprint)


def fixIncompatibilities(reactions, onto, species_id2chebi_id, interesting_term_ids, verbose):
    log(verbose, "  computing eq 0...")
    term_id2clu = computeEq0(interesting_term_ids)
    # printClusters(term_id2clu, onto)
    log(verbose, "  maximizing...")
    term_id2clu = maximize(reactions, term_id2clu, species_id2chebi_id)
    filterClu2Terms(term_id2clu)
    # printClusters(term_id2clu, onto)
    log(verbose, "  preserving stoichiometry...")
    term_id2clu = fixStoich(reactions, term_id2clu, species_id2chebi_id, onto)
    filterClu2Terms(term_id2clu)
    # printClusters(term_id2clu, onto)
    log(verbose, "  maximizing...")
    term_id2clu = maximize(reactions, term_id2clu, species_id2chebi_id)
    filterClu2Terms(term_id2clu)
    # printClusters(term_id2clu, onto)
    # term_id2clu = computeRepresentatives(term_id2clu, getClu2term(term_id2clu), onto)
    return term_id2clu


def generalize(reactions, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose=False):
    interesting_term_ids = set(species_id2chebi_id.values()) - ubiquitous_chebi_ids
    term_id2clu = fixIncompatibilities(reactions, onto, species_id2chebi_id, interesting_term_ids, verbose)
    if not term_id2clu:
        return {}, {}

    r2clu = getReaction2cluster(reactions, term_id2clu, species_id2chebi_id)

    log(verbose, "  annotating generalized terms...")
    term_id2clu = update(term_id2clu, onto)
    if verbose:
        printFinalClusters(term_id2clu, onto)

    s_id2clu = {s_id: term_id2clu[t] for (s_id, t) in
                filter(lambda (s_id, t): t in term_id2clu, species_id2chebi_id.iteritems())}
    return s_id2clu, r2clu


def getUbRP(r, ubiquitous_ids):
    reactants, products = getReactants(r), getProducts(r)
    return reactants & ubiquitous_ids, products & ubiquitous_ids


def simplifiedNeedToReverse(r, ubiquitous_ids):
    u_rs, u_ps = getUbRP(r, ubiquitous_ids)
    return r.getReversible() and u_rs > u_ps


def getSimplifiedKey(r, ubiquitous_ids):
    reactants, products = getReactants(r), getProducts(r)
    ubiquitous_reactants, ubiquitous_products = reactants & ubiquitous_ids, products & ubiquitous_ids
    srs_len, sps_len = len(reactants - ubiquitous_ids), len(products - ubiquitous_ids)
    if r.getReversible() and simplifiedNeedToReverse(r, ubiquitous_ids):
        return ubiquitous_products, ubiquitous_reactants, sps_len, srs_len
    return ubiquitous_reactants, ubiquitous_products, srs_len, sps_len,


def shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose=False):
    ubiquitous_ids = set(
        filter(lambda s_id: species_id2chebi_id[s_id] in ubiquitous_chebi_ids, species_id2chebi_id.keys()))
    specific_ids = set(species_id2chebi_id.keys()) - ubiquitous_ids

    def getInsOuts(s_id):
        ins, outs = getPReactionsBySpecies(s_id, reactions), getRReactionsBySpecies(s_id, reactions)
        r_ins = filter(lambda r: not simplifiedNeedToReverse(r, ubiquitous_ids), ins) + filter(
            lambda r: simplifiedNeedToReverse(r, ubiquitous_ids), outs)
        r_outs = filter(lambda r: not r in r_ins, ins) + filter(lambda r: not r in r_ins, outs)
        return r_ins, r_outs

    def getRP(r):
        rs, ps = getReactants(r), getProducts(r)
        if simplifiedNeedToReverse(r, ubiquitous_ids):
            return ps, rs
        return rs, ps

    def check(s_id, checked):
        if s_id in checked:
            return [], None, []

        rs = getReactionsBySpecies(s_id, reactions)
        if len(rs) != 2:
            return [s_id], None, []
        ins, outs = getInsOuts(s_id)
        if 1 == len(ins) == len(outs):
            r_in, r_out = ins[0], outs[0]
            in_k, out_k = getSimplifiedKey(r_in, ubiquitous_ids), getSimplifiedKey(r_out, ubiquitous_ids)
            # same simplified keys that include at least one ubiquitous species
            if in_k == out_k and (in_k[0] or in_k[1]):
                checked.add(s_id)
                in_rs, in_ps = getRP(r_in)
                out_rs, out_ps = getRP(r_out)

                left_s_ids = in_rs - out_rs
                if len(left_s_ids) != 1:
                    return [s_id], (in_k, r_in.getName()), []
                left_id = left_s_ids.pop()

                right_s_ids = out_ps - in_ps
                if len(right_s_ids) != 1:
                    return [s_id], (in_k, r_in.getName()), []
                right_id = right_s_ids.pop()
                left_ts, l_key, left_rs = check(left_id, checked)
                if not r_in.getId() in left_rs:
                    left_rs += [r_in.getId()]
                right_ts, r_key, right_rs = check(right_id, checked)
                if not r_out.getId() in right_rs:
                    right_rs = [r_out.getId()] + right_rs
                return left_ts + [s_id] + right_ts, (in_k, r_in.getName()), left_rs + right_rs
        return [s_id], None, []

    result = []
    checked = set()
    for s_id in specific_ids:
        lst = check(s_id, checked)
        if len(lst[0]) > 1 and onto.commonPts({onto.getTerm(species_id2chebi_id[s_id]) for s_id in lst[0]}):
            result.append(lst)

    if verbose:
        printFinalChains(result)

    return result


def printFinalChains(chains):
    print "result reaction chains:"
    blueprint = []
    for chain in chains:
        s_ids, key, r_ids = chain
        print "   ", key[1], " : ", len(r_ids)
        blueprint.append(len(r_ids))
    print "   ", sorted(blueprint)


def map2chebi(cofactors, input_model, onto):
    species_id2chebi_id, fake_terms = get_species_to_chebi(input_model, onto)
    terms = [onto.getTerm(t_id) for t_id in set(species_id2chebi_id.values())]
    ontology = subOntology(onto, terms, relationships={'is_a'} | EQUIVALENT_TERM_RELATIONSHIPS, step=None,
                           min_deepness=11)
    for t in fake_terms:
        onto.removeTerm(t)
    cofactor_ids = set(filter(lambda cofactor_id: ontology.getTerm(cofactor_id), cofactors))
    ubiquitous_chebi_ids = cofactor_ids | getUbiquitousSpeciesSet(input_model, species_id2chebi_id, ontology)
    return ontology, species_id2chebi_id, ubiquitous_chebi_ids


def generalize_model(input_model, onto, cofactors, sh_chains=True, verbose=False):
    remove_is_a_reactions(input_model)

    log(verbose, "filtering reactions and species...")
    # go only for reactions inside organelles
    reactions = filter(lambda reaction: filterReactionByNotTransport(reaction, input_model),
                       input_model.getListOfReactions())
    s_ids = set()
    for r in reactions:
        s_ids |= getProducts(r) | getReactants(r)
    species = {input_model.getSpecies(s_id) for s_id in s_ids}

    log(verbose, "mapping species to ChEBI...")
    ontology, species_id2chebi_id, ubiquitous_chebi_ids = map2chebi(cofactors, input_model, onto, species)

    if sh_chains:
        # shorten chains
        log(verbose, "chain shortening...")
        chains = shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
        if chains:
             # save
             input_model = save_as_chain_shortened_sbml(chains, input_model, verbose)
             # update species_id2chebi_id
             for s_id in species_id2chebi_id.keys():
                 if not input_model.getSpecies(s_id):
                     del species_id2chebi_id[s_id]
             # update reactions, go only for reactions inside organelles
             reactions = filter(lambda r: filterReactionByNotTransport(r, input_model), input_model.getListOfReactions())

    # generalize
    log(verbose, "generalizing...")
    s_id2clu, r2clu = generalize(reactions, species_id2chebi_id, ubiquitous_chebi_ids, ontology, verbose)
    s_id2clu = {s_id: ontology.getTerm(clu) for (s_id, clu) in s_id2clu.iteritems()}

    return input_model, species_id2chebi_id, ubiquitous_chebi_ids, s_id2clu, r2clu
