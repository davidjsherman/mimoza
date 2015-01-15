from collections import defaultdict, Counter
from itertools import chain
from math import sqrt

from sbml_generalization.generalization.MaximizingThread import MaximizingThread
from sbml_generalization.generalization.StoichiometryFixingThread import StoichiometryFixingThread
from sbml_generalization.generalization.reaction_filters import get_reactants, get_products
from sbml_generalization.generalization.vertical_key import get_vertical_key, is_reactant
from sbml_generalization.utils.logger import log_clusters, log
from sbml_generalization.utils.misc import invert_map
from sbml_generalization.utils.obo_ontology import Term
from sbml_generalization.generalization.mark_ubiquitous import get_ubiquitous_species_set, UBIQUITOUS_THRESHOLD


__author__ = 'anna'

EQUIVALENT_TERM_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of', 'is_tautomer_of'}


def get_r_compartments(model, r):
    s_ids = get_reactants(r) | get_products(r)
    return tuple({model.getSpecies(s_id).getCompartment() for s_id in s_ids})


def get_reaction_ids_to_factor(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
    vk2r = defaultdict(set)
    for r in model.getListOfReactions():
        vk2r[(get_vertical_key(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids), get_r_compartments(model, r))].add(
            r.getId())
    return vk2r


def generalize_reactions(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
    r_id2clu, i = {}, 0
    for r_ids in get_reaction_ids_to_factor(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids).itervalues():
        for r_id in r_ids:
            r_id2clu[r_id] = i
        i += 1
    return r_id2clu


def compute_s_id2clu(model, species_id2term_id, term_id2clu):
    s_id2clu = {}
    for s_id, t_id in species_id2term_id.iteritems():
        if t_id in term_id2clu:
            s_id2clu[s_id] = (term_id2clu[t_id], model.getSpecies(s_id).getCompartment())
    return s_id2clu


def maximize(model, term_id2clu, species_id2term_id, ubiquitous_chebi_ids):
    clu2term_ids = invert_map(term_id2clu)
    s_id2clu = compute_s_id2clu(model, species_id2term_id, term_id2clu)

    r_id2clu = generalize_reactions(model, s_id2clu, species_id2term_id, ubiquitous_chebi_ids)

    thrds = []
    for (clu, term_ids) in clu2term_ids.iteritems():
        if len(term_ids) <= 1:
            continue

        thread = MaximizingThread(model, term_ids, species_id2term_id, clu, term_id2clu,
                                  s_id2clu, ubiquitous_chebi_ids, r_id2clu)
        thrds.append(thread)
        thread.start()  # This actually causes the thread to run
    for th in thrds:
        th.join()  # This waits until the thread has completed
    return term_id2clu


def update_binary_vectors(model, term_id2clu, species_id2term_id, ubiquitous_chebi_ids):
    clu2term_ids = invert_map(term_id2clu)
    s_id2clu = compute_s_id2clu(model, species_id2term_id, term_id2clu)

    r_id2clu = generalize_reactions(model, s_id2clu, species_id2term_id, ubiquitous_chebi_ids)
    t_id2rs = defaultdict(list)
    for r in (r for r in model.getListOfReactions() if r.getNumReactants() > 1 or r.getNumProducts() > 1):
        for s_id in chain((species_ref.getSpecies() for species_ref in r.getListOfReactants()),
                          (species_ref.getSpecies() for species_ref in r.getListOfProducts())):
            if s_id in species_id2term_id:
                t_id2rs[species_id2term_id[s_id]].append(r)

    for clu, t_ids in clu2term_ids.iteritems():
        r2t_ids = defaultdict(set)
        for t_id in t_ids:
            for r in t_id2rs[t_id]:
                r2t_ids[r.getId()].add(t_id)

        t_id2r_clus = {}
        all_clus = set()
        for t_id in t_ids:
            clus = {(r_id2clu[r.getId()],
                     "in" if is_reactant(t_id, r, s_id2clu, species_id2term_id, ubiquitous_chebi_ids) else "out")
                    for r in t_id2rs[t_id]}
            t_id2r_clus[t_id] = clus
            all_clus |= {clu[0] for clu in clus}
        clu2index = dict(zip(all_clus, xrange(0, len(all_clus))))
        vector2t_ids = defaultdict(list)
        for t_id in t_id2r_clus.iterkeys():
            cls = []
            for r_clu in t_id2r_clus[t_id]:
                cls.append((clu2index[r_clu[0]], r_clu[1]))
            vector = tuple(
                [1 if (it, "in") in cls else (-1 if (it, "out") in cls else 0) for it in xrange(0, len(all_clus))])
            vector2t_ids[vector].append(t_id)

        vectors = vector2t_ids.keys()
        conflicts = [i for i in xrange(0, len(all_clus)) if
                     next((t for t in vectors if 1 == t[i]), None) and next((t for t in vectors if -1 == t[i]), None)]
        if not conflicts:
            continue

        in_conflict = lambda v1, v2: next((True for j in conflicts if v1[j] * v2[j] == -1), False)
        median_vector = lambda vector_list: [median(vector_list, j, vector2t_ids) for j in xrange(0, len(all_clus))]
        i = max(conflicts, key=lambda i: len([t for t in vectors if 0 != t[i]]))
        current_vectors = []
        for vector in sorted((vector for vector in vectors if vector[i] != 0),
                             key=lambda vector: -len(vector2t_ids[vector])):
            good_vectors = sorted(
                ((c_vectors, tot) for (c_vectors, tot) in current_vectors if not in_conflict(vector, tot)),
                key=lambda (c_vectors, tot): distance(vector, median_vector(c_vectors)))
            if good_vectors:
                c_vectors, tot = good_vectors[0]
                c_vectors.append(vector)
                for j in xrange(0, len(all_clus)):
                    if vector[j] != 0:
                        tot[j] = vector[j]
            else:
                current_vectors.append(([vector], list(vector)))

        neutral_vectors = [vector for vector in vectors if vector[i] == 0]

        intersect = lambda v1, v2: next((True for j in xrange(0, len(all_clus)) if v1[j] == v2[j] != 0), False)
        compatible_clusters = lambda vector, vectors: [(vs, tot) for (vs, tot) in vectors if
                                                       not in_conflict(vector, tot) and intersect(vector, tot)]

        while neutral_vectors:
            bad_vectors = [vector for vector in neutral_vectors if
                           not next(((c_vectors, tot) for (c_vectors, tot) in current_vectors if
                                     not in_conflict(vector, tot)), None)]
            if not bad_vectors:
                vector = min(neutral_vectors, key=lambda vector: min(distance(vector, median_vector(c_vectors))
                                                                     for (c_vectors, tot) in current_vectors if
                                                                     not in_conflict(vector, tot)))

                comp_clus = compatible_clusters(vector, current_vectors)
                if comp_clus:
                    c_vectors, tot = max(((c_vs, tot) for (c_vs, tot) in comp_clus), key=lambda (c_vs, tot):
                    sum((1 if vector[j] == tot[j] != 0 else 0 for j in xrange(0, len(all_clus)))))
                    c_vectors.append(vector)
                    for j in xrange(0, len(all_clus)):
                        if vector[j] != 0:
                            tot[j] = vector[j]
                else:
                    current_vectors.append(([vector], list(vector)))
            else:
                vector = max(bad_vectors, key=lambda vector: len(vector2t_ids[vector]))
                current_vectors.append(([vector], list(vector)))
            neutral_vectors.remove(vector)

        i = 0
        for (c_vectors, _) in current_vectors:
            n_clu = (clu, i)
            i += 1
            for vector in c_vectors:
                for t in vector2t_ids[vector]:
                    term_id2clu[t] = n_clu


def median(arrays, j, array2num):
    total, length = 0, 0
    for array in arrays:
        l = len(array2num[array])
        total += array[j] * l
        length += l

    return int(round(float(total) / length))


def distance(a, b):
    return sqrt(sum(pow(a[i] - b[i], 2) for i in xrange(0, len(a))))


def cover_t_ids(t_ids, onto):
    term_id2clu = {}
    roots = onto.common_points({onto.get_term(t_id) for t_id in t_ids})
    if roots:
        r_id = roots[0].id
        return {t_id: (r_id,) for t_id in t_ids}
    roots = set()
    for t in t_ids:
        term = onto.get_term(t)
        # then it's a fake term
        if not term:
            continue
        roots |= onto.get_generalized_ancestors_of_level(term, set(), None, 3)
    psi = {tuple(sorted(t.id for t in onto.get_sub_tree(root))): root.id for root in roots}
    i = 0
    for t_set, root_id in greedy(t_ids, psi, {it: 1 for it in psi}):
        term_id2clu.update({t_id: (root_id,) for t_id in t_set})
        i += 1
    return term_id2clu


def update_onto(onto, term_id2clu):
    ancestors = []
    clu2t_ids = invert_map(term_id2clu)
    for clu, t_ids in clu2t_ids.iteritems():
        if len(t_ids) <= 1:
            continue
        terms = {onto.get_term(t_id) for t_id in t_ids}
        ancestors.extend(onto.common_points(terms))
    removed_something = False
    count = Counter(ancestors)
    for t in (t for t in count.keys() if count[t] > 1):
        # if this term has been already removed as an ancestor/equivalent of another term
        if not onto.get_term(t.id):
            continue
        for it in onto.get_generalized_ancestors(t, relationships=EQUIVALENT_TERM_RELATIONSHIPS):
            onto.remove_term(it, True)
        for it in onto.get_equivalents(t, relationships=EQUIVALENT_TERM_RELATIONSHIPS):
            onto.remove_term(it, True)
        onto.remove_term(t, True)
        removed_something = True
    return removed_something


def fix_stoichiometry(model, term_id2clu, species_id2term_id, onto):
    clu2term_ids = invert_map(term_id2clu)
    thrds = []
    for clu, term_ids in clu2term_ids.iteritems():
        if len(term_ids) <= 1:
            continue
        thread = StoichiometryFixingThread(model, term_ids, species_id2term_id, onto, clu, term_id2clu)
        thrds.append(thread)
        thread.start()  # This actually causes the thread to run
    for th in thrds:
        th.join()  # This waits until the thread has completed
    return term_id2clu


def greedy(terms, psi, set2score):
    terms = set(terms)
    while terms and psi:
        s = max(psi.iterkeys(), key=lambda candidate_terms: (len(set(candidate_terms) & terms), set2score[candidate_terms]))
        result = set(s)
        # yield result
        yield result & terms, psi[s]
        terms -= result
        del psi[s]


def update(term_id2clu, onto):
    clu2term_ids = invert_map(term_id2clu)
    used = set()
    i = 0
    for clu, term_ids in clu2term_ids.iteritems():
        terms = {onto.get_term(t) for t in term_ids}
        common_ancestors = {t for t in onto.common_points(terms)}
        options = common_ancestors - used
        if options:
            common_ancestor_term = options.pop()
        else:
            name = common_ancestors.pop().get_name() + " (another)" if common_ancestors else ' or '.join(
                [t.get_name() for t in terms])
            common_ancestor_term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
            onto.add_term(common_ancestor_term)
            i += 1
        used.add(common_ancestor_term)
        for t in term_ids:
            term_id2clu[t] = common_ancestor_term.get_id()
    return term_id2clu


def update_clu(s_id2clu, onto, s_id2term_id, model):
    clu2s_ids = invert_map(s_id2clu)
    used = set()
    i = 0
    for clu, s_ids in clu2s_ids.iteritems():
        c_id = model.getSpecies(list(s_ids)[0]).getCompartment()
        terms = {onto.get_term(s_id2term_id[s_id]) for s_id in s_ids if s_id in s_id2term_id}
        if terms:
            common_ancestors = {(t, c_id) for t in onto.common_points(terms)}
            options = common_ancestors - used
            if options:
                common_ancestor_term = options.pop()[0]
            else:
                name = common_ancestors.pop()[0].get_name() + " (another)" if common_ancestors else ' or '.join(
                    [t.get_name() for t in terms])
                common_ancestor_term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
                onto.add_term(common_ancestor_term)
                i += 1
        else:
            name = ' or '.join([model.getSpecies(s_id).getName() for s_id in s_ids])
            common_ancestor_term = Term(t_id="chebi:unknown_{0}".format(i), name=name)
            onto.add_term(common_ancestor_term)
            i += 1
        used.add((common_ancestor_term, c_id,))
        for s_id in s_ids:
            s_id2clu[s_id] = (c_id, common_ancestor_term)
    return s_id2clu


def filter_clu_to_terms(term2clu):
    clu2term = invert_map(term2clu)
    for clu, terms in clu2term.iteritems():
        if len(terms) <= 1:
            del term2clu[terms.pop()]


def fix_incompatibilities(model, onto, species_id2chebi_id, ubiquitous_chebi_ids, verbose):
    chebi_ids = set(species_id2chebi_id.itervalues()) - ubiquitous_chebi_ids
    log(verbose, "  aggressive metabolite grouping...")
    term_id2clu = cover_t_ids(chebi_ids, onto)
    onto.trim({it[0] for it in term_id2clu.itervalues()}, relationships=EQUIVALENT_TERM_RELATIONSHIPS)
    # log_clusters(term_id2clu, onto, verbose, True)
    onto_updated = True
    while onto_updated:
        log(verbose, "  satisfying metabolite diversity...")
        term_id2clu = maximize(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
        onto_updated = update_onto(onto, term_id2clu)
        for clu, t_ids in invert_map(term_id2clu).iteritems():
            if len(t_ids) == 1:
                del term_id2clu[t_ids.pop()]
            else:
                term_id2clu.update(cover_t_ids(t_ids, onto))

    # log_clusters(term_id2clu, onto, verbose, True)
    update_binary_vectors(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
    log(verbose, "  preserving stoichiometry...")
    term_id2clu = fix_stoichiometry(model, term_id2clu, species_id2chebi_id, onto)
    filter_clu_to_terms(term_id2clu)
    # log_clusters(term_id2clu, onto, verbose, True)
    onto_updated = True
    while onto_updated:
        log(verbose, "  satisfying metabolite diversity...")
        term_id2clu = maximize(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
        onto_updated = update_onto(onto, term_id2clu)
        for clu, t_ids in invert_map(term_id2clu).iteritems():
            if len(t_ids) == 1:
                del term_id2clu[t_ids.pop()]
            else:
                term_id2clu.update(cover_t_ids(t_ids, onto))
    # log_clusters(term_id2clu, onto, verbose, True)
    return term_id2clu


# def infer_clusters(model, s_ids, term_id2clu):


def generalize_species(model, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose=False):
    term_id2clu = fix_incompatibilities(model, onto, species_id2chebi_id, ubiquitous_chebi_ids, verbose)
    if not term_id2clu:
        return {}
    term_id2clu = update(term_id2clu, onto)
    # log_clusters(term_id2clu, onto, verbose)
    s_id2clu = {}
    t_c_id2species = defaultdict(set)
    for (s_id, t) in species_id2chebi_id.iteritems():
        c_id = model.getSpecies(s_id).getCompartment()
        if t in term_id2clu:
            s_id2clu[s_id] = (c_id, onto.get_term(term_id2clu[t]))
        else:
            t_c_id2species[(t, c_id)].add(s_id)
    # If there were several species in the same compartment
    # with the same ChEBI id, let's cluster them, too.
    for ((t, c_id), s_set) in t_c_id2species.iteritems():
        if len(s_set) > 1:
            term = onto.get_term(t)
            for s_id in s_set:
                s_id2clu[s_id] = (c_id, term)
    # log(verbose, "  generalizing by simplified key...")
    # vk2r_ids = get_reaction_ids_to_factor(model, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
    # simplified_key_generalization(model, s_id2clu, ubiquitous_chebi_ids, vk2r_ids, onto)
    # s_id2clu = update_clu(s_id2clu, onto, species_id2chebi_id, model)
    log_clusters(s_id2clu, onto, verbose, True)

    return s_id2clu


def sort_by_compartment(input_model, r_sps):
    comp2r_sps = defaultdict(list)
    for it in r_sps:
        if isinstance(it, tuple):
            c_id, term = it
            comp2r_sps[c_id].append(term)
        else:
            comp2r_sps[input_model.getSpecies(it).getCompartment()].append(it)
    return comp2r_sps


def map2chebi(species_id2chebi_id, cofactors, input_model, onto, threshold=UBIQUITOUS_THRESHOLD):
    cofactor_ids = {cofactor_id for cofactor_id in cofactors if onto.get_term(cofactor_id)}
    ubiquitous_chebi_ids = cofactor_ids | get_ubiquitous_species_set(input_model, species_id2chebi_id, onto, threshold)
    return ubiquitous_chebi_ids
