from utils.ontology import Term
from utils.reaction_filters import getReactants, getProducts
from utils.misc import add2map, invert

__author__ = 'anna'


def getReactions2Factor(reactions, term_id2clu, s_id2term_id):
    vk2r = {}
    for r in reactions:
        key = getVerticalKey(r, term_id2clu, s_id2term_id)
        add2map(vk2r, key, r)
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


def getRReactions(t_id, reactions, term_id2s_ids):
    return filter(lambda r: len(term_id2s_ids[t_id] & getReactants(r)) > 0, reactions)


def getPReactions(t_id, reactions, term_id2s_ids):
    return filter(lambda r: len(term_id2s_ids[t_id] & getProducts(r)) > 0, reactions)


def getReactions(t_id, reactions, term_id2s_ids):
    return filter(lambda r: len(term_id2s_ids[t_id] & (getReactants(r) | getProducts(r))) > 0, reactions)


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
    clu2term_ids = invert(term_id2clu)
    term_id2s_ids = invert(species_id2term_id)

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
            # tr_r = lambda r: ("in", r.getName()) if alignedToVKey(r, term2clu, species_id2term) else (
            #     "out", r.getName())
            # tr_p = lambda r: ("out", r.getName()) if alignedToVKey(r, term2clu, species_id2term) else (
            #     "in", r.getName())
            # print t_id.getName(), {tr_r(r) for r in getRReactions(t_id, reactions, term_id2s_ids)} | \
            #              {tr_p(r) for r in getPReactions(t_id, reactions, term_id2s_ids)}
            neighbours = {transform_r(r) for r in getRReactions(t_id, reactions, term_id2s_ids)} | \
                         {transform_p(r) for r in getPReactions(t_id, reactions, term_id2s_ids)}
            key = tuple(sorted(neighbours))
            add2map(neighbours2term_ids, key, t_id)
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
    term2s_ids = invert(species_id2term_id)
    for t_id in term_ids:
        for r in getReactions(t_id, reactions, term2s_ids):
            add2map(r2term_ids, r, t_id)
    return filter(lambda terms: len(terms) > 1, r2term_ids.values())


def fixStoich(reactions, term_id2clu, species_id2term_id, onto):
    clu2term_ids = invert(term_id2clu)
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
        result |= onto.getAnyChildren(t, False, set()) | onto.getEqualTerms(t) | {t}
    return result


def getPsiSet(onto, term_ids, conflicts):
    def good(t_set, conflicts):
        if not t_set:
            return False
        if len(t_set) <= 1:
            return True
        good = True
        for c_ts in conflicts:
            if len(t_set & c_ts) > 1:
                good = False
                break
        return good

    transform = lambda t: {t.getId() for t in
                           (onto.getAnyChildren(t, False, set()) | {t} | onto.getEqualTerms(t))} & term_ids

    Ts = onto.commonPts({onto.getTerm(t) for t in term_ids})
    if not Ts:
        Ts = onto.getRoots()

    basics, psi, set2score = [], set(), {}
    for T in Ts:
        element = transform(T)
        basics.append(element)
        element = tuple(sorted(element))
        level = onto.getLevel(T)
        set2score[element] = (3, max(level), min(level))
        psi.add(element)

    for T in Ts:
        options = onto.getAnyChildren(T, direct=False, checked=set())
        for t in options:
            t_set = transform(t)
            if len(t_set) == 0:
                continue
            element = tuple(sorted(t_set))
            psi.add(element)
            level = onto.getLevel(t)
            set2score[element] = (3, max(level), min(level))

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

    to_add = set()
    ps = list(psi)
    i = 0
    for s in psi:
        i += 1
        for ss in ps[i:]:
            sss = tuple(sorted(set(s) - set(ss)))
            if sss:
                to_add.add(sss)
                set2score[sss] = avg_tup(set2score[s])
            sss = tuple(sorted(set(ss) - set(s)))
            if sss:
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
    clu2term_ids = invert(term_id2clu)
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
    clu2term = invert(term2clu)
    for clu, terms in clu2term.iteritems():
        if len(terms) <= 1:
            del term2clu[terms.pop()]


def printClusters(term_id2clu, onto):
    clu2term_id = invert(term_id2clu)
    print "   quotient species sets:"
    for clu, term_ids in clu2term_id.iteritems():
        if len(term_ids) == 1:
            continue
        print "     (", len(term_ids), ") ", [onto.getTerm(it).getName() for it in term_ids]
        print


def printFinalClusters(term_id2clu, onto):
    clu2term = invert(term_id2clu)
    print "result quotient species sets:"
    blueprint = []
    for clu, term_ids in clu2term.iteritems():
        if len(term_ids) == 1:
            continue
        blueprint.append(len(term_ids))
        print "   ", onto.getTerm(clu).getName(), " (", len(term_ids), ") <-> ", [onto.getTerm(it).getName() for it in
                                                                                  term_ids]
        print
    print sorted(blueprint)


def log(verbose, msg):
    if verbose:
        print msg


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


def generalize(reactions, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose):
    interesting_term_ids = set(species_id2chebi_id.values()) - ubiquitous_chebi_ids
    term_id2clu = fixIncompatibilities(reactions, onto, species_id2chebi_id, interesting_term_ids, verbose)
    if not term_id2clu:
        return None

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


def shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose):
    ubiquitous_ids = set(
        filter(lambda k: not species_id2chebi_id[k] in ubiquitous_chebi_ids, species_id2chebi_id.keys()))
    specific_terms = {species_id2chebi_id[s_id] for s_id in set(species_id2chebi_id.keys()) - ubiquitous_ids}

    term_id2s_ids = invert(species_id2chebi_id)

    def getInsOuts(t_id):
        ins, outs = getPReactions(t_id, reactions, term_id2s_ids), getRReactions(t_id, reactions, term_id2s_ids)
        r_ins = filter(lambda r: not simplifiedNeedToReverse(r, ubiquitous_ids), ins) + filter(
            lambda r: simplifiedNeedToReverse(r, ubiquitous_ids), outs)
        r_outs = filter(lambda r: not r in ins, r_ins) + filter(lambda r: not r in ins, outs)
        return r_ins, r_outs

    def getRP(r):
        rs, ps = getReactants(r), getProducts(r)
        if simplifiedNeedToReverse(r, ubiquitous_ids):
            return ps, rs
        return rs, ps

    def check(t_id, checked):
        if t_id in checked:
            return [], None

        rs = getReactions(t_id, reactions, term_id2s_ids)
        if len(rs) != 2:
            return [t_id], None
        ins, outs = getInsOuts(t_id)
        #		print graph["name"][n], len(ins), len(outs)
        if 1 == len(ins) == len(outs):
            r_in, r_out = ins[0], outs[0]
            in_k, out_k = getSimplifiedKey(r_in, ubiquitous_ids), getSimplifiedKey(r_out, ubiquitous_ids)
            #			print in_k, " vs ", out_k
            if in_k == out_k and (in_k[0] or in_k[1]):
                checked.add(t_id)
                print in_k
                #				verbose(graph.getInNodes(r_in), graph)
                #				verbose(graph.getInNodes(r_out), graph)

                in_rs, in_ps = getRP(r_in)
                out_rs, out_ps = getRP(r_out)
                left_t_ids = in_rs - out_rs
                #				verbose(left_t_ids, graph)
                if len(left_t_ids) != 1:
                    return [t_id], in_k
                left_id = left_t_ids.pop()

                right_term_ids = out_ps - in_ps
                #				print right_term_ids
                if len(right_term_ids) != 1:
                    return [t_id], in_k
                right_id = right_term_ids.pop()

                return check(left_id, checked)[0] + [t_id] + check(right_id, checked)[0], in_k
        return [t_id], None

    result = []
    checked = set()
    for t_id in specific_terms:
        lst = check(t_id, checked)
        if len(lst[0]) > 1 and onto.commonPts({onto.getTerm(t) for t in lst[0]}):
            result.append(lst)

    return result

    #TODO: save this result
    # if result:
    #     quotient = graph.addCloneSubGraph(graph.getName() + " quotient")
    #     clone = graph.addCloneSubGraph(graph.getName())
    #
    # getR = lambda rs: filter(lambda it: key == getSimplifiedKey(it, ubs, graph), rs)[0]
    # for (lst, key,) in result:
    #     print len(lst)
    #     start, end = lst[0], lst[len(lst) - 1]
    #     nds = set()
    #     #		verbose([start, end], graph)
    #     #		verbose(lst, graph)
    #     for n in lst[1:]:
    #         r = getR(graph.getInNodes(n))
    #         nds |= {r} | set(graph.getInOutNodes(r))
    #     start_r = getR(graph.getOutNodes(start))
    #     nds -= set(graph.getInNodes(start_r))
    #     end_r = getR(graph.getInNodes(end))
    #     nds -= set(graph.getOutNodes(end_r))
    #     #		verbose(nds, graph)
    #
    #     metaNode = quotient.createMetaNode(list(nds), False)
    #     for prop in ["compartment", "outsideCompartment", \
    #                  "reaction", "reversible", "sboTerm", "ubiquitous", \
    #                  "viewBorderColor", "viewBorderWidth", "viewColor", "viewFont", "viewFontSize", \
    #                  "viewLabelColor", "viewLabelPosition", "viewLayout", "viewRotation", "viewSelection", \
    #                  "viewShape", "viewTexture"]:
    #         quotient[prop][metaNode] = graph[prop][start_r]
    #     quotient["id"][metaNode] = "meta_" + graph["id"][start_r]
    #     quotient["viewSize"][metaNode] = tlp.Size(6, 6) #bb.width(), bb.height())
    #     quotient["viewLabel"][metaNode] = "generalized\nchain\n{0}".format(graph["name"][start_r])
    #     rs = {graph.getInNodes(m).next() for m in lst[1:]}
    #     quotient["reversible"][metaNode] = True
    #     for r in rs:
    #         if not graph["reversible"][r]:
    #             quotient["reversible"][metaNode] = False
    #             break
    #     quotient["geneAssociation"][metaNode] = " and ".join(graph["geneAssociation"][it] for it in rs)
    #     quotient["ecNumber"][metaNode] = ",".join(graph["ecNumber"][it] for it in rs)
