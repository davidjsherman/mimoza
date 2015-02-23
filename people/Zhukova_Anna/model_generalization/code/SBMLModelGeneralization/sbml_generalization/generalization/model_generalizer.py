from collections import defaultdict, Counter
from itertools import chain
from math import sqrt

from sbml_generalization.generalization.MaximizingThread import MaximizingThread
from sbml_generalization.generalization.StoichiometryFixingThread import StoichiometryFixingThread, compute_s_id2clu, \
    infer_clusters, suggest_clusters
from sbml_generalization.generalization.vertical_key import is_reactant, get_vk2r_ids
from sbml_generalization.utils.logger import log, log_clus
from sbml_generalization.utils.misc import invert_map
from sbml_generalization.utils.obo_ontology import Term
from sbml_generalization.generalization.mark_ubiquitous import get_ubiquitous_species_set, UBIQUITOUS_THRESHOLD


__author__ = 'anna'

EQUIVALENT_TERM_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of', 'is_tautomer_of'}


def generalize_reactions(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids, simplified=False):
    vk2r = get_vk2r_ids(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids)
    r_id2clu, i = {}, 0
    for r_ids in vk2r.itervalues():
        for r_id in r_ids:
            r_id2clu[r_id] = i
        i += 1
    return r_id2clu


def maximize(unmapped_s_ids, model, term_id2clu, species_id2term_id, ub_chebi_ids):
    clu2term_ids = invert_map(term_id2clu)
    s_id2clu = compute_s_id2clu(unmapped_s_ids, model, species_id2term_id, term_id2clu)

    r_id2clu = generalize_reactions(model, s_id2clu, species_id2term_id, ub_chebi_ids)

    thrds = []
    for (clu, term_ids) in clu2term_ids.iteritems():
        if len(term_ids) <= 1:
            continue

        thread = MaximizingThread(model, term_ids, species_id2term_id, clu, term_id2clu,
                                  s_id2clu, ub_chebi_ids, r_id2clu)
        thrds.append(thread)
        thread.start()  # This actually causes the thread to run
    for th in thrds:
        th.join()  # This waits until the thread has completed
    return term_id2clu


def update_binary_vectors(unmapped_s_ids, model, term_id2clu, species_id2term_id, ubiquitous_chebi_ids):
    clu2term_ids = invert_map(term_id2clu)
    s_id2clu = compute_s_id2clu(unmapped_s_ids, model, species_id2term_id, term_id2clu)

    r_id2clu = generalize_reactions(model, s_id2clu, species_id2term_id, ubiquitous_chebi_ids)
    t_id2rs = defaultdict(list)
    for r in (r for r in model.getListOfReactions() if r.getNumReactants() > 1 or r.getNumProducts() > 1):
        for s_id in chain((species_ref.getSpecies() for species_ref in r.getListOfReactants()),
                          (species_ref.getSpecies() for species_ref in r.getListOfProducts())):
            if s_id in species_id2term_id:
                t_id2rs[species_id2term_id[s_id]].append(r)

    for clu, t_ids in clu2term_ids.iteritems():
        t_id2directed_r_clus = {}
        all_r_clus = set()
        for t_id in t_ids:
            directed_r_clus = {(r_id2clu[r.getId()],
                                "in" if is_reactant(t_id, r, s_id2clu, species_id2term_id,
                                                    ubiquitous_chebi_ids) else "out")
                               for r in t_id2rs[t_id]}
            t_id2directed_r_clus[t_id] = directed_r_clus
            all_r_clus |= {clu[0] for clu in directed_r_clus}

        r_clu2index = dict(zip(all_r_clus, xrange(0, len(all_r_clus))))
        vector2t_ids = defaultdict(list)
        for t_id in t_id2directed_r_clus.iterkeys():
            directed_indexed_r_clus = []
            for r_clu in t_id2directed_r_clus[t_id]:
                directed_indexed_r_clus.append((r_clu2index[r_clu[0]], r_clu[1]))
            vector = tuple(
                [1 if (it, "in") in directed_indexed_r_clus else (-1 if (it, "out") in directed_indexed_r_clus else 0)
                 for it in xrange(0, len(all_r_clus))])
            vector2t_ids[vector].append(t_id)

        vectors = vector2t_ids.keys()
        # A conflict: There exist two similar reactions, one of which produces a species while the other consumes it.
        conflict_indices = [i for i in xrange(0, len(all_r_clus)) if
                            next((t for t in vectors if 1 == t[i]), None) and next((t for t in vectors if -1 == t[i]),
                                                                                   None)]
        if not conflict_indices:
            continue

        in_conflict = lambda v1, v2: next((True for j in conflict_indices if v1[j] * v2[j] == -1), False)
        intersect = lambda v1, v2: next((True for j in xrange(0, len(all_r_clus)) if v1[j] == v2[j] != 0), False)
        median_vector = lambda vector_list: [median(vector_list, j, vector2t_ids) for j in xrange(0, len(all_r_clus))]

        most_conflict_index = max(conflict_indices, key=lambda i: len([t for t in vectors if 0 != t[i]]))
        current_vectors = []
        for concerned_vector in sorted((vector for vector in vectors if vector[most_conflict_index] != 0),
                                       key=lambda vector: -len(vector2t_ids[vector])):
            compatible_vectors = sorted(
                ((c_vectors, total) for (c_vectors, total) in current_vectors if
                 not in_conflict(concerned_vector, total)),
                key=lambda (c_vectors, tot): distance(concerned_vector, median_vector(c_vectors)))
            if compatible_vectors:
                c_vectors, total = compatible_vectors[0]
                c_vectors.append(concerned_vector)
                for j in xrange(0, len(all_r_clus)):
                    if concerned_vector[j] != 0:
                        total[j] = concerned_vector[j]
            else:
                current_vectors.append(([concerned_vector], list(concerned_vector)))

        neutral_vectors = [vector for vector in vectors if vector[most_conflict_index] == 0]
        compatible_intersecting_vectors = lambda v, vs: [(_, tot) for (_, tot) in vs if
                                                         not in_conflict(v, tot) and intersect(v, tot)]

        while neutral_vectors:
            incompatible_vectors = [concerned_vector for concerned_vector in neutral_vectors if
                                    not next(((_, tot) for (_, tot) in current_vectors if
                                              not in_conflict(concerned_vector, tot)), None)]
            if not incompatible_vectors:
                concerned_vector = min(neutral_vectors,
                                       key=lambda vector: min(distance(vector, median_vector(c_vectors))
                                                              for (c_vectors, tot) in current_vectors if
                                                              not in_conflict(vector, tot)))

                comp_clus = compatible_intersecting_vectors(concerned_vector, current_vectors)
                if comp_clus:
                    c_vectors, total = max(((c_vs, tot) for (c_vs, tot) in comp_clus), key=lambda (c_vs, tot):
                    sum((1 if concerned_vector[j] == tot[j] != 0 else 0 for j in xrange(0, len(all_r_clus)))))
                    c_vectors.append(concerned_vector)
                    for j in xrange(0, len(all_r_clus)):
                        if concerned_vector[j] != 0:
                            total[j] = concerned_vector[j]
                else:
                    current_vectors.append(([concerned_vector], list(concerned_vector)))
            else:
                concerned_vector = max(incompatible_vectors, key=lambda vector: len(vector2t_ids[vector]))
                current_vectors.append(([concerned_vector], list(concerned_vector)))
            neutral_vectors.remove(concerned_vector)

        i = 0
        for (c_vectors, _) in current_vectors:
            n_clu = clu + (i,)
            i += 1
            for concerned_vector in c_vectors:
                for t in vector2t_ids[concerned_vector]:
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


def cover_t_ids(model, species_id2term_id, ubiquitous_chebi_ids, t_ids, onto, clu=None):
    term_id2clu = {}
    real_terms = {onto.get_term(t_id) for t_id in t_ids if onto.get_term(t_id)}
    unmapped_s_ids = {s_id for s_id in t_ids if not onto.get_term(s_id)}
    roots = onto.common_points(real_terms)
    if roots:
        root_id = roots[0].get_id()
        new_clu = clu + (root_id, ) if clu else (root_id, )
        return {t_id: new_clu for t_id in t_ids}
    roots = set()
    for term in real_terms:
        roots |= onto.get_generalized_ancestors_of_level(term, set(), None, 4)
    psi = {tuple(sorted(t.id for t in onto.get_sub_tree(root))): root.id for root in roots}
    for t_set, root_id in greedy({t.get_id() for t in real_terms}, psi, {it: 1 for it in psi}):
        new_clu = clu + (root_id, ) if clu else (root_id, )
        term_id2clu.update({t_id: new_clu for t_id in t_set})

    s_id2clu = compute_s_id2clu(set(), model, species_id2term_id, term_id2clu)
    infer_clusters(model, unmapped_s_ids, s_id2clu, species_id2term_id, ubiquitous_chebi_ids)
    for s_id in unmapped_s_ids:
        if s_id in s_id2clu:
            term_id2clu[s_id] = s_id2clu[s_id][1]
    return term_id2clu


def update_onto(onto, term_id2clu):
    ancestors = []
    clu2t_ids = invert_map(term_id2clu)
    for clu, t_ids in clu2t_ids.iteritems():
        if len(t_ids) <= 1:
            continue
        terms = {onto.get_term(t_id) for t_id in t_ids if onto.get_term(t_id)}
        if terms:
            ancestors.extend(set(onto.common_points(terms)))
    removed_something = False
    count = Counter(ancestors)
    for t in (t for t in count.keys() if count[t] > 1):
        # if this term has been already removed as an ancestor/equivalent of another term
        if not onto.get_term(t.get_id()):
            continue
        for it in onto.get_generalized_ancestors(t, relationships=EQUIVALENT_TERM_RELATIONSHIPS):
            onto.remove_term(it, True)
        for it in onto.get_equivalents(t, relationships=EQUIVALENT_TERM_RELATIONSHIPS):
            onto.remove_term(it, True)
        onto.remove_term(t, True)
        removed_something = True
    return removed_something


def fix_stoichiometry(model, term_id2clu, species_id2term_id, ub_chebi_ids, onto):
    clu2term_ids = invert_map(term_id2clu)
    thrds = []
    conflicts = []
    for r in model.getListOfReactions():
        t_ids = {species_id2term_id[s_id] if s_id in species_id2term_id else s_id
                 for s_id in chain((species_ref.getSpecies() for species_ref in r.getListOfReactants()),
                                   (species_ref.getSpecies() for species_ref in r.getListOfProducts()))}
        if len(t_ids) > 1:
            conflicts.append(t_ids)
    for clu, term_ids in clu2term_ids.iteritems():
        if len(term_ids) <= 1:
            continue
        clu_conflicts = [set(it) for it in {tuple(t_ids & term_ids) for t_ids in conflicts} if len(it) > 1]
        real_term_ids = {t_id for t_id in term_ids if onto.get_term(t_id)}
        unmapped_s_ids = {s_id for s_id in term_ids if not onto.get_term(s_id)}
        if clu_conflicts:
            thread = StoichiometryFixingThread(model, species_id2term_id, ub_chebi_ids, unmapped_s_ids, real_term_ids,
                                               clu_conflicts, onto, clu, term_id2clu)
            thrds.append(thread)
            thread.start()  # This actually causes the thread to run
    for th in thrds:
        th.join()  # This waits until the thread has completed


def greedy(terms, psi, set2score):
    terms = set(terms)
    while terms and psi:
        s = max(psi.iterkeys(),
                key=lambda candidate_terms: (len(set(candidate_terms) & terms), set2score[candidate_terms]))
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
        terms = {onto.get_term(t) for t in term_ids if onto.get_term(t)}
        common_ancestors = {t for t in onto.common_points(terms)} if terms else set()
        options = common_ancestors - used
        if options:
            common_ancestor_term = options.pop()
        else:
            name = common_ancestors.pop().get_name() + " (another)" if common_ancestors else 'fake term'
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
        if len(terms) == 1:
            del term2clu[terms.pop()]


def fix_t_id2clu(onto, term_id2clu):
    for t_id in term_id2clu.keys():
        if not onto.get_term(t_id):
            del term_id2clu[t_id]


def cover_with_onto_terms(model, onto, species_id2chebi_id, term_id2clu, ubiquitous_chebi_ids):
    onto_updated = update_onto(onto, term_id2clu)
    if onto_updated:
        for clu, t_ids in invert_map(term_id2clu).iteritems():
            if len(t_ids) == 1:
                del term_id2clu[t_ids.pop()]
            else:
                new_t_id2clu = cover_t_ids(model, species_id2chebi_id, ubiquitous_chebi_ids, t_ids, onto, clu)
                for t_id in t_ids:
                    if t_id in new_t_id2clu:
                        term_id2clu[t_id] = new_t_id2clu[t_id]
                    else:
                        del term_id2clu[t_id]
    return onto_updated


def maximization_step(model, onto, species_id2chebi_id, term_id2clu, ub_term_ids, unmapped_s_ids, verbose):
    onto_updated = True
    while onto_updated:
        log(verbose, "  satisfying metabolite diversity...")
        term_id2clu = maximize(unmapped_s_ids, model, term_id2clu, species_id2chebi_id, ub_term_ids)
        onto_updated = cover_with_onto_terms(model, onto, species_id2chebi_id, term_id2clu, ub_term_ids)


def fix_incompatibilities(unmapped_s_ids, model, onto, species_id2chebi_id, ubiquitous_chebi_ids, verbose):
    if not ubiquitous_chebi_ids:
        ubiquitous_chebi_ids = set()
    chebi_ids = set(species_id2chebi_id.itervalues()) - ubiquitous_chebi_ids

    log(verbose, "  aggressive metabolite grouping...")
    term_id2clu = cover_t_ids(model, species_id2chebi_id, ubiquitous_chebi_ids, chebi_ids, onto)
    onto.trim({it[0] for it in term_id2clu.itervalues()}, relationships=EQUIVALENT_TERM_RELATIONSHIPS)
    suggest_clusters(model, unmapped_s_ids, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
    filter_clu_to_terms(term_id2clu)
    # log_clus(term_id2clu, onto, model, verbose)

    maximization_step(model, onto, species_id2chebi_id, term_id2clu, ubiquitous_chebi_ids, unmapped_s_ids, verbose)
    filter_clu_to_terms(term_id2clu)
    # log_clus(term_id2clu, onto, model, verbose)

    log(verbose, "  preserving stoichiometry...")
    # update_binary_vectors(unmapped_s_ids, model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
    # filter_clu_to_terms(term_id2clu)
    fix_stoichiometry(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids, onto)
    filter_clu_to_terms(term_id2clu)
    # log_clus(term_id2clu, onto, model, verbose)

    maximization_step(model, onto, species_id2chebi_id, term_id2clu, ubiquitous_chebi_ids, unmapped_s_ids, verbose)
    filter_clu_to_terms(term_id2clu)
    # log_clus(term_id2clu, onto, model, verbose)

    return term_id2clu


def generalize_species(model, s_id2chebi_id, ub_s_ids, onto, ub_chebi_ids, verbose=False, threshold=UBIQUITOUS_THRESHOLD):
    unmapped_s_ids = {s.getId() for s in model.getListOfSpecies() if s.getId() not in s_id2chebi_id}
    term_id2clu = fix_incompatibilities(unmapped_s_ids, model, onto, s_id2chebi_id, ub_chebi_ids, verbose)
    if term_id2clu:
        term_id2clu = update(term_id2clu, onto)
        s_id2clu = compute_s_id2clu(unmapped_s_ids, model, s_id2chebi_id, term_id2clu)
    else:
        s_id2clu = {}
    if not ub_s_ids:
        s_id2deg = Counter()
        for r in model.getListOfReactions():
            for s_id in (species_ref.getSpecies() for species_ref in
                         chain(r.getListOfReactants(), r.getListOfProducts())):
                s_id2deg.update({s_id: 1})
        chebi_id2s_id = invert_map(s_id2chebi_id)
        for chebi_id, s_ids in chebi_id2s_id.iteritems():
            count = max(s_id2deg[s_id] for s_id in s_ids)
            for s_id in s_ids:
                s_id2deg[s_id] = count
        ub_s_ids = {s.getId() for s in model.getListOfSpecies() if
                    (s.getId() not in s_id2clu) and
                    (s_id2deg[s.getId()] >= threshold
                     or (s.getId() in s_id2chebi_id and s_id2chebi_id[s.getId()] in ub_chebi_ids))}
    # unmapped_s_ids = {s_id for s_id in unmapped_s_ids if s_id not in s_id2clu}
    # infer_clusters(model, unmapped_s_ids, s_id2clu, species_id2chebi_id, ub_chebi_ids)
    return s_id2clu, ub_s_ids


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
