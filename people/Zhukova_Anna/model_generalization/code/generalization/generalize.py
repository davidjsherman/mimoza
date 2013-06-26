from utils.reaction_filters import getReactants, getProducts
from utils.misc import add2map

__author__ = 'anna'


def getReactions2Factor(reactions, s_id2clu):
    vk2r = {}
    for r in reactions:
        key = getVerticalKey(r, s_id2clu)
        if key in vk2r:
            vk2r[key].append(r)
        else:
            vk2r[key] = [r]
    return vk2r.values()


def getVerticalKey(r, s_id2clu):
    ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes \
        = getKeyElements(r, s_id2clu)
    if r.getReversible():
        if needToReverse(ubiquitous_reactants, ubiquitous_products, specific_reactant_classes,
                         specific_product_classes):
            ubiquitous_reactants, ubiquitous_products = ubiquitous_products, ubiquitous_reactants
            specific_reactant_classes, specific_product_classes = specific_product_classes, specific_reactant_classes
    return ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes


def needToReverse(ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes):
    return (ubiquitous_reactants > ubiquitous_products) or (
        not ubiquitous_reactants and not ubiquitous_products and specific_reactant_classes > specific_product_classes)


def getKeyElements(r, s_id2clu):
    reactants, products = getReactants(r), getProducts(r)

    ub_tr = lambda f: tuple(sorted(filter(lambda it: not (it in s_id2clu), f)))
    ubiquitous_reactants, ubiquitous_products = ub_tr(reactants), ub_tr(products)

    getSpecificClasses = lambda species, id2parent: [s_id2clu[s_id] if s_id in s_id2clu else s_id for s_id in species]
    sp_tr = lambda f: tuple(sorted(getSpecificClasses(filter(lambda it: it in s_id2clu, f), s_id2clu)))
    specific_reactant_classes, specific_product_classes = sp_tr(reactants), sp_tr(products)

    return ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes


def alignToVKey(reactions, s_id2clu):
    for r in reactions:
        if not r.getReversible():
            continue
        ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes \
            = getKeyElements(r, s_id2clu)
        if needToReverse(ubiquitous_reactants, ubiquitous_products, specific_reactant_classes,
                         specific_product_classes):
            reactants = list(r.getListOfReactants())
            products = list(r.getListOfProducts())
            for p_s in products:
                r.addReactant(p_s)
                r.removeProduct(0)
            for r_s in reactants:
                r.addProduct(r_s)
                r.removeReactant(0)


def getReaction2cluster(reactions, s_id2clu):
    rs_clusters = getReactions2Factor(reactions, s_id2clu)
    r2clu, i = {}, 0
    for rs in rs_clusters:
        for r in rs:
            r2clu[r] = i
        i += 1
    return r2clu


def getRReactions(s_id, reactions):
    return filter(lambda r: s_id in getReactants(r), reactions)


def getPReactions(s_id, reactions):
    return filter(lambda r: s_id in getProducts(r), reactions)


def getReactions(s_id, reactions):
    return filter(lambda r: s_id in getReactants(r) or s_id in getProducts(r), reactions)


def maximize(reactions, term2clu, species_id2chebi_term):
    s_id2clu, clu2s_ids = {}, {}
    for s_id, term in species_id2chebi_term.iteritems():
        if term in term2clu:
            clu = term2clu[term]
            s_id2clu[s_id] = clu
            add2map(clu2s_ids, clu, s_id)

    r2clu = getReaction2cluster(reactions, s_id2clu)
    alignToVKey(reactions, s_id2clu)

    for (clu, s_ids) in clu2s_ids.iteritems():
        if len(s_ids) <= 1:
            continue
        neighbours2terms = {}
        for s_id in s_ids:
            # reactions this species participated in
            neighbours = {("in", r2clu[r]) for r in getRReactions(s_id, reactions)} | {("out", r2clu[r]) for r in
                                                                                       getPReactions(s_id, reactions)}
            key = tuple(sorted(neighbours))
            add2map(neighbours2terms, key, species_id2chebi_term[s_id])
        lst = neighbours2terms.iteritems()
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
        if len(new_lst) > 1:
            i = 0
            for neighbours, terms in new_lst:
                n_clu = clu + (i,)
                i += 1
                for t in terms:
                    term2clu[t] = n_clu
    return term2clu


def getClu2term(term2clusters):
    clu2term = {}
    for term, clu in term2clusters.iteritems():
        add2map(clu2term, clu, term)
    return clu2term


def computeEq0(interesting_terms):
    return {term: (0,) for term in interesting_terms}


def getConflicts(reactions, terms, species_id2chebi_term):
    r2s_ids = {}
    for s_id in species_id2chebi_term.keys():
        if species_id2chebi_term[s_id] in terms:
            for r in getReactions(s_id, reactions):
                add2map(r2s_ids, r, s_id)
    conflicts = [{species_id2chebi_term[s_id] for s_id in species_ids} for species_ids in r2s_ids.values()]
    return filter(lambda sps: len(sps) > 1, conflicts)


def fixStoich(reactions, term2clu, species_id2chebi_term, onto):
    clu2terms = getClu2term(term2clu)
    for clu, terms in clu2terms.iteritems():
        if len(terms) <= 1:
            continue
        conflicts = getConflicts(reactions, terms, species_id2chebi_term)
        if not conflicts:
            continue
        # print [t.getName() for t in terms]
        # print " >> ", [{n.getName() for n in ns} for ns in conflicts]
        t_sets = partition(terms, onto, conflicts)
        i = 0
        for ts in t_sets:
            # print "---> ", [t.getName() for t in ts]
            i += 1
            n_clu = clu + (i,)
            for t in ts:
                term2clu[t] = n_clu
    return term2clu


def getParentOptions(terms, onto):
    options = set()
    for t in terms:
        options |= onto.getAnyParents(t, False, set()) | onto.getEqualTerms(t) | {t}
    return options


def getPsiSet(onto, terms, conflicts):

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

    psi = set()

    set2score = {}
    for t in getParentOptions(terms, onto):
        t_set = (onto.getAnyChildren(t, False, set()) | {t} | onto.getEqualTerms(t)) & terms
        if len(t_set) > 1:
            element = tuple(sorted(t_set))
            psi.add(element)
            set2score[element] = (3, min(onto.getLevel(t)))

        # compl_set = terms - t_set
        # if len(compl_set) > 1:
        #     element = tuple(sorted(compl_set))
        #     psi.add(element)
        #     set2score[element] = 2

            #	print len(psi)
    # if len(psi) > 50:
    #     psi = {tuple(t) for t in filter(lambda it: good(set(it), conflicts), psi)}

    for t in terms:
        element = (t,)
        psi.add(element)
        set2score[element] = (3, min(onto.getLevel(t)))

    to_add = set()
    ps = list(psi)
    i = 0
    for s in psi:
        i += 1
        for ss in ps[i:]:
            sss = tuple(sorted(set(s) - set(ss)))
            if sss:
                to_add.add(sss)
                set2score[sss] = (2, 0)
            sss = tuple(sorted(set(ss) - set(s)))
            if sss:
                to_add.add(sss)
                set2score[sss] = (2, 0)
    psi |= to_add

    return filter(lambda s: good(set(s), conflicts), psi), set2score


def partition(terms, onto, conflicts):
    psi, set2score = getPsiSet(onto, terms, conflicts)
    parts = list(reversed(greedy(terms, psi, set2score)))
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
    while terms and psi:
        s = max(psi, key=lambda it: (len(set(it) & terms), set2score[it]))
        phi.append(s)
        terms -= set(s)
        psi.remove(s)
    return [set(it) for it in phi]


def cluster2term(terms, onto):
    # print "ROOTS ", [t.getName() for t in onto.getRoots()]
    options = onto.commonPts(terms)
    if not options:
        options = onto.getRoots()
    return options.pop()


def computeRepresentatives(term2clu, clu2term, onto):
    clu2t, t2clu = {}, {}
    for clu, terms in clu2term.iteritems():
        T = cluster2term(terms, onto)
        clu2t[clu] = T
        add2map(t2clu, T, clu)
    Ts = list(t2clu.keys())
    i = 0
    tr = lambda it: onto.getAnyChildren(it, False, set()) | onto.getEqualTerms(it, None, 0, set())
    t2not = {}
    for t in Ts:
        kids = tr(t)
        i += 1
        for o_t in Ts[i:]:
            if tr(o_t) & kids:
                if o_t in kids:
                    add2map(t2not, t, o_t)
                else:
                    add2map(t2not, o_t, t)
    for clu, terms in clu2term.iteritems():
        T = clu2t[clu]
        name = T.getName()
        if T in t2not:
            name = name + ", but not " + ", nor ".join([t.getName() for t in t2not[T]])
        for t in terms:
            term2clu[t] = (name, list(T.getAllIds()))
    return term2clu


def update(term2clu, onto):
    clu2terms = getClu2term(term2clu)
    for clu, terms in clu2terms.iteritems():
        T = cluster2term(terms, onto)
        for t in terms:
            term2clu[t] = T
    return term2clu


def filterClu2Terms(term2clu):
    clu2term = getClu2term(term2clu)
    for clu, terms in clu2term.iteritems():
        if len(terms) <= 1:
            del term2clu[terms.pop()]


def printClusters(term2clu):
    clu2term = getClu2term(term2clu)
    print "-- Species clusters: --"
    for clu, terms in clu2term.iteritems():
        print [it.getName() for it in terms]
        print


def printFinalClusters(term2clu):
    clu2term = getClu2term(term2clu)
    print "-- Species clusters: --"
    for clu, terms in clu2term.iteritems():
        print clu.getName(), " <-> ", [it.getName() for it in terms]
        print


def fixIncompatibilities(reactions, onto, species_id2chebi_term, interesting_terms):
    print "---eq-0---"
    term2clu = computeEq0(interesting_terms)
    # printClusters(term2clu)
    print "---maximize---"
    term2clu = maximize(reactions, term2clu, species_id2chebi_term)
    filterClu2Terms(term2clu)
    # printClusters(term2clu)
    print "---stoich---"
    term2clu = fixStoich(reactions, term2clu, species_id2chebi_term, onto)
    filterClu2Terms(term2clu)
    printClusters(term2clu)
    print "---maximize---"
    term2clu = maximize(reactions, term2clu, species_id2chebi_term)
    filterClu2Terms(term2clu)
    # printClusters(term2clu)
    # term2clu = computeRepresentatives(term2clu, getClu2term(term2clu), onto)
    print "---update---"
    term2clu = update(term2clu, onto)
    printFinalClusters(term2clu)
    print "---done---"
    return term2clu


def generalize(reactions, species_id2chebi_term, ubiquitous_chebi_terms, onto):
    interesting_terms = set(species_id2chebi_term.values()) - ubiquitous_chebi_terms
    term2clu = fixIncompatibilities(reactions, onto, species_id2chebi_term, interesting_terms)
    if not term2clu:
        return None

    s_id2clu, clu2s_ids = {}, {}
    for s_id, term in species_id2chebi_term.iteritems():
        if term in term2clu:
            clu = term2clu[term]
            add2map(clu2s_ids, clu, s_id)
            s_id2clu[s_id] = clu
    r2clu = getReaction2cluster(reactions, s_id2clu)
    clu2rs = {}
    for r, clu in r2clu.iteritems():
        add2map(clu2rs, clu, r)
    return clu2s_ids, clu2rs, s_id2clu, r2clu