from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi
from sbml_generalization.utils.logger import log, log_chains, log_clusters, log_r_clusters
from sbml_generalization.utils.misc import add_to_map, invert_map
from sbml_generalization.utils.obo_ontology import Term, subOntology
from reaction_filters import getReactants, getProducts

from sbml_generalization.generalization.mark_ubiquitous import getUbiquitousSpeciesSet


__author__ = 'anna'

EQUIVALENT_TERM_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of', 'is_tautomer_of'}


def get_reactions_to_factor(reactions, s_id2clu, s_id2term_id):
    vk2r = {}
    for r in reactions:
        key = get_vertical_key(r, s_id2clu, s_id2term_id)
        add_to_map(vk2r, key, r)
    return vk2r.values()


def get_vertical_key(r, s_id2clu, s_id2term_id):
    ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes \
        = get_key_elements(r, s_id2clu, s_id2term_id)
    if r.getReversible() and need_to_reverse(
            (ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes,)):
        return ubiquitous_products, ubiquitous_reactants, specific_product_classes, specific_reactant_classes
    return ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes


def need_to_reverse((ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes, )):
    return (ubiquitous_reactants > ubiquitous_products) or (
        not ubiquitous_reactants and not ubiquitous_products and specific_reactant_classes > specific_product_classes)


def get_key_elements(r, s_id2clu, s_id2term_id):
    reactants, products = getReactants(r), getProducts(r)

    def classify(s_ids):
        specific, ubiquitous = [], []
        for s_id in s_ids:
            if s_id in s_id2clu:
                specific.append(s_id2clu[s_id])
            else:
                ubiquitous.append(s_id2term_id[s_id] if s_id in s_id2term_id else s_id)
        transform = lambda collection: tuple(sorted(collection))
        return transform(specific), transform(ubiquitous)

    specific_reactant_classes, ubiquitous_reactants = classify(reactants)
    specific_product_classes, ubiquitous_products = classify(products)
    return ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes


def aligned_to_v_key(r, term_id2clu, s_id2term_id):
    if not r.getReversible():
        return True
    return not need_to_reverse(get_key_elements(r, term_id2clu, s_id2term_id))


def generalize_reactions(reactions, s_id2clu, s_id2term_id):
    rs_clusters = get_reactions_to_factor(reactions, s_id2clu, s_id2term_id)
    r2clu, i = {}, 0
    for rs in rs_clusters:
        for r in rs:
            r2clu[r] = i
        i += 1
    return r2clu


def get_r_reactions_by_term(t_id, reactions, term_id2s_ids):
    return (r for r in reactions if len(term_id2s_ids[t_id] & getReactants(r)) > 0)


def get_p_reactions_by_term(t_id, reactions, term_id2s_ids):
    return (r for r in reactions if len(term_id2s_ids[t_id] & getProducts(r)) > 0)


def get_reactions_by_term(t_id, reactions, term_id2s_ids):
    return (r for r in reactions if len(term_id2s_ids[t_id] & (getReactants(r) | getProducts(r))) > 0)


def get_r_reactions_by_species(s_id, reactions):
    return [r for r in reactions if s_id in getReactants(r)]


def get_p_reactions_by_species(s_id, reactions):
    return [r for r in reactions if s_id in getProducts(r)]


def get_reactions_by_species(s_id, reactions):
    return [r for r in reactions if s_id in (getReactants(r) | getProducts(r))]


def merge_based_on_neighbours(lst):
    new_lst = []
    for neighbours, terms in lst:
        neighbours = set(neighbours)
        to_remove = []
        for (new_neighbours, new_terms) in new_lst:
            if neighbours & new_neighbours:
                neighbours |= new_neighbours
                terms |= new_terms
                to_remove.append((new_neighbours, new_terms))
        new_lst = [it for it in new_lst if not it in to_remove] + [(neighbours, terms)]
    return new_lst


def maximize(reactions, term_id2clu, species_id2term_id, onto):
    clu2term_ids = invert_map(term_id2clu)
    term_id2s_ids = invert_map(species_id2term_id)
    s_id2clu = {s_id: term_id2clu[t] for (s_id, t) in species_id2term_id.iteritems() if t in term_id2clu}

    r2clu = generalize_reactions(reactions, s_id2clu, species_id2term_id)

    for (clu, term_ids) in clu2term_ids.iteritems():
        #print [onto.getTerm(it).getName() for it in term_ids]
        if len(term_ids) <= 1:
            continue
        neighbours2term_ids = {}
        neighbourless_terms = set()
        for t_id in term_ids:
            neighbours = {("in" if t_id in get_vertical_key(r, s_id2clu, species_id2term_id)[3] else "out", r2clu[r])
                          for r in
                          get_reactions_by_term(t_id, reactions, term_id2s_ids)}
            if neighbours:
                key = tuple(sorted(neighbours))
                add_to_map(neighbours2term_ids, key, t_id)
            else:
                neighbourless_terms.add(t_id)
            #print onto.getTerm(t_id).getName(), neighbours
        new_lst = merge_based_on_neighbours(neighbours2term_ids.iteritems())
        i = 0
        if len(new_lst) > 1:
            for neighbours, term_ids in new_lst:
                n_clu = clu + (i,)
                i += 1
                for t in term_ids:
                    term_id2clu[t] = n_clu
        for t in neighbourless_terms:
            term_id2clu[t] = clu + (i,)
            i += 1
    return term_id2clu


def compute_eq0(interesting_term_ids, onto):
    #clu = (0,)
    term_id2clu = {}
    i = 0
    psi = [tuple(t.getId() for t in onto.get_sub_tree(root)) for root in onto.getRoots()]
    for t_set in greedy(interesting_term_ids, psi, {it: 1 for it in psi}):
        clu = (i,)
        term_id2clu.update({t_id: clu for t_id in t_set})
        i += 1
        #return {term_id: clu for term_id in interesting_term_ids}
    return term_id2clu


def get_conflicts(reactions, term_ids, species_id2term_id):
    r2term_ids = {}
    term2s_ids = invert_map(species_id2term_id)
    for t_id in term_ids:
        for r in get_reactions_by_term(t_id, reactions, term2s_ids):
            add_to_map(r2term_ids, r, t_id)
    return [terms for terms in r2term_ids.itervalues() if len(terms) > 1]


def fix_stoichiometry(reactions, term_id2clu, species_id2term_id, onto):
    clu2term_ids = invert_map(term_id2clu)
    for clu, term_ids in clu2term_ids.iteritems():
        if len(term_ids) <= 1:
            continue
        conflicts = get_conflicts(reactions, term_ids, species_id2term_id)
        if not conflicts:
            continue
            #print [[onto.getTerm(it).getName() for it in trms] for trms in conflicts]
        psi, set2score = get_psi_set(onto, term_ids, conflicts)
        i = 0
        for ts in greedy(term_ids, psi, set2score):
            i += 1
            n_clu = clu + (i,)
            for t in ts:
                term_id2clu[t] = n_clu
    return term_id2clu


def get_parent_options(term_ids, onto):
    options = onto.commonPts({onto.getTerm(t) for t in term_ids})
    if not options:
        options = onto.getRoots()
    result = set()
    for t in options:
        result |= onto.get_sub_tree(t)
    return result


def get_psi_set(onto, term_ids, conflicts):
    def good(t_set):
        if not t_set:
            return False
        if len(t_set) == 1:
            return True
        for c_ts in conflicts:
            if len(t_set & c_ts) > 1:
                return False
        return True

    get_covered_term_ids = lambda term: {sub_t.getId() for sub_t in onto.get_sub_tree(term)} & term_ids

    # the least common ancestors, or roots if there are none
    common_ancestor_terms = onto.commonPts({onto.getTerm(t) for t in term_ids})
    if not common_ancestor_terms:
        common_ancestor_terms = onto.getRoots()

    psi, basics, set2score = set(), [], {}

    def process(element, score):
        el = tuple(sorted(element))
        if element in psi:
            return False
        basics.append(element)
        psi.add(el)
        set2score[el] = score
        return True

    # sets defined by the least common ancestors
    # print "ANCESTORS: ", [t.getName() for t in common_ancestor_terms]
    for T in common_ancestor_terms:
        T_element = get_covered_term_ids(T)
        T_level = onto.getLevel(T)
        process(T_element, (3, sum(T_level) / len(T_level)))
        for t in onto.getAnyChildren(T, False, set()):
            element = get_covered_term_ids(t)
            if not element:
                continue
            level = onto.getLevel(t)
            if process(element, (3, sum(level) / len(level))):
                # complement set
                complement = T_element - element
                if complement:
                    process(complement, (2, sum(T_level) / len(T_level)))

    def avg_tup(s0, s1):
        i0, j0 = set2score[tuple(sorted(s0))]
        i1, j1 = set2score[tuple(sorted(s1))]
        return min(i0, i1) - 1, min(j0, j1)

    # the differences between sets already in Psi
    for _ in [0, 3]:
        to_add = []
        i = 0
        for basic in basics:
            i += 1
            for element in basics[i:]:
                for complement_set in (basic - element, element - basic):
                    if len(complement_set) > 0:
                        c_element = tuple(sorted(complement_set))
                        if c_element in psi:
                            continue
                        psi.add(c_element)
                        to_add.append(complement_set)
                        set2score[c_element] = avg_tup(element, basic)
        basics += to_add

    result = [term_set for term_set in psi if good(set(term_set))]
    #for ts in result:
    #    print [onto.getTerm(t).getName() for t in ts], set2score[tuple(sorted(ts))]
    return result, set2score


def greedy(terms, psi, set2score):
    terms = set(terms)
    while terms and psi:
        s = max(psi, key=lambda candidate_terms: (len(set(candidate_terms) & terms), set2score[candidate_terms]))
        result = set(s)
        #yield result
        yield result & terms
        terms -= result
        psi.remove(s)


def update(term_id2clu, onto):
    clu2term_ids = invert_map(term_id2clu)
    used = set()
    i = 0
    for clu, term_ids in clu2term_ids.iteritems():
        terms = {onto.getTerm(t) for t in term_ids}
        common_ancestors = set(onto.commonPts(terms))
        options = common_ancestors - used
        if options:
            common_ancestor_term = options.pop()
        else:
            name = common_ancestors.pop().getName() + " (another)" if common_ancestors else ' or '.join(
                [t.getName() for t in terms])
            common_ancestor_term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
            onto.addTerm(common_ancestor_term)
            i += 1
        used.add(common_ancestor_term)
        for t in term_ids:
            term_id2clu[t] = common_ancestor_term.getId()
    return term_id2clu


def filter_clu_to_terms(term2clu):
    clu2term = invert_map(term2clu)
    for clu, terms in clu2term.iteritems():
        if len(terms) <= 1:
            del term2clu[terms.pop()]


def fix_incompatibilities(reactions, onto, species_id2chebi_id, interesting_term_ids, verbose):
    #log(verbose, "  computing eq 0...")
    term_id2clu = compute_eq0(interesting_term_ids, onto)
    #log_clusters(term_id2clu, onto, verbose)
    #log(verbose, "  maximizing...")
    term_id2clu = maximize(reactions, term_id2clu, species_id2chebi_id, onto)
    filter_clu_to_terms(term_id2clu)
    #log_clusters(term_id2clu, onto, verbose)
    #log(verbose, "  preserving stoichiometry...")
    term_id2clu = fix_stoichiometry(reactions, term_id2clu, species_id2chebi_id, onto)
    filter_clu_to_terms(term_id2clu)
    #log_clusters(term_id2clu, onto, verbose)
    #log(verbose, "  maximizing...")
    term_id2clu = maximize(reactions, term_id2clu, species_id2chebi_id, onto)
    filter_clu_to_terms(term_id2clu)
    #log_clusters(term_id2clu, onto, verbose)
    return term_id2clu


def generalize_species(reactions, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose=False):
    interesting_term_ids = set(species_id2chebi_id.values()) - ubiquitous_chebi_ids
    term_id2clu = fix_incompatibilities(reactions, onto, species_id2chebi_id, interesting_term_ids, verbose)
    if not term_id2clu:
        return {}
    term_id2clu = update(term_id2clu, onto)
    log_clusters(term_id2clu, onto, verbose)
    return {s_id: onto.getTerm(term_id2clu[t]) for (s_id, t) in species_id2chebi_id.iteritems() if t in term_id2clu}


def get_ubiquitous_reactants_products(r, ubiquitous_ids):
    reactants, products = getReactants(r), getProducts(r)
    return reactants & ubiquitous_ids, products & ubiquitous_ids


def simplified_need_to_reverse(r, ubiquitous_ids):
    u_rs, u_ps = get_ubiquitous_reactants_products(r, ubiquitous_ids)
    return r.getReversible() and u_rs > u_ps


def get_simplified_key(r, ubiquitous_ids):
    reactants, products = getReactants(r), getProducts(r)
    ubiquitous_reactants, ubiquitous_products = reactants & ubiquitous_ids, products & ubiquitous_ids
    srs_len, sps_len = len(reactants - ubiquitous_ids), len(products - ubiquitous_ids)
    if r.getReversible() and simplified_need_to_reverse(r, ubiquitous_ids):
        return ubiquitous_products, ubiquitous_reactants, sps_len, srs_len
    return ubiquitous_reactants, ubiquitous_products, srs_len, sps_len,


def shorten_chains(reactions, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose=False):
    ubiquitous_ids = {s_id for s_id in species_id2chebi_id.iterkeys() if
                      species_id2chebi_id[s_id] in ubiquitous_chebi_ids}

    def get_in_out_reactions(s_id):
        ins, outs = get_p_reactions_by_species(s_id, reactions), get_r_reactions_by_species(s_id, reactions)
        r_ins = [r for r in ins if not simplified_need_to_reverse(r, ubiquitous_ids)] \
                + [r for r in outs if simplified_need_to_reverse(r, ubiquitous_ids)]
        r_outs = [r for r in ins if not r in r_ins] + [r for r in outs if not r in r_ins]
        return r_ins, r_outs

    def get_aligned_reactants_products(r):
        rs, ps = getReactants(r), getProducts(r)
        if simplified_need_to_reverse(r, ubiquitous_ids):
            return ps, rs
        return rs, ps

    def check(s_id, already_checked):
        if s_id in already_checked:
            return [], None, []

        rs = get_reactions_by_species(s_id, reactions)
        if len(rs) != 2:
            return [s_id], None, []
        ins, outs = get_in_out_reactions(s_id)
        if 1 == len(ins) == len(outs):
            r_in, r_out = ins[0], outs[0]
            in_k, out_k = get_simplified_key(r_in, ubiquitous_ids), get_simplified_key(r_out, ubiquitous_ids)
            # same simplified keys that include at least one ubiquitous species
            if in_k == out_k and (in_k[0] or in_k[1]):
                already_checked.add(s_id)
                in_rs, in_ps = get_aligned_reactants_products(r_in)
                out_rs, out_ps = get_aligned_reactants_products(r_out)

                left_s_ids = in_rs - out_rs
                if len(left_s_ids) != 1:
                    return [s_id], (in_k, r_in.getName()), []
                left_id = left_s_ids.pop()

                right_s_ids = out_ps - in_ps
                if len(right_s_ids) != 1:
                    return [s_id], (in_k, r_in.getName()), []
                right_id = right_s_ids.pop()
                left_ts, l_key, left_rs = check(left_id, already_checked)
                if not r_in.getId() in left_rs:
                    left_rs += [r_in.getId()]
                right_ts, r_key, right_rs = check(right_id, already_checked)
                if not r_out.getId() in right_rs:
                    right_rs = [r_out.getId()] + right_rs
                return left_ts + [s_id] + right_ts, (in_k, r_in.getName()), left_rs + right_rs
        return [s_id], None, []

    result = []
    checked = set()
    specific_ids = (s_id for s_id in species_id2chebi_id.iterkeys() if \
                    not species_id2chebi_id[s_id] in ubiquitous_chebi_ids)
    for s_id in specific_ids:
        lst = check(s_id, checked)
        if len(lst[0]) > 1 and onto.commonPts((onto.getTerm(species_id2chebi_id[s_id]) for s_id in lst[0])):
            result.append(lst)

    log_chains(result, verbose)

    return result


def map2chebi(cofactors, input_model, onto):
    species_id2chebi_id, fake_terms = get_species_to_chebi(input_model, onto)
    terms = [onto.getTerm(t_id) for t_id in set(species_id2chebi_id.values())]
    ontology = subOntology(onto, terms, relationships={'is_a'} | EQUIVALENT_TERM_RELATIONSHIPS, step=None,
                           min_deepness=11)
    for t in fake_terms:
        onto.removeTerm(t)
    cofactor_ids = {cofactor_id for cofactor_id in cofactors if ontology.getTerm(cofactor_id)}
    ubiquitous_chebi_ids = cofactor_ids | getUbiquitousSpeciesSet(input_model, species_id2chebi_id, ontology)
    return ontology, species_id2chebi_id, ubiquitous_chebi_ids
