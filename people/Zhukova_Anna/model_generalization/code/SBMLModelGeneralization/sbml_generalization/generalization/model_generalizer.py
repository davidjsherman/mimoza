from collections import Counter
from itertools import chain
import logging

from sbml_generalization.generalization.MaximizingThread import MaximizingThread
from sbml_generalization.generalization.StoichiometryFixingThread import StoichiometryFixingThread, compute_s_id2clu, \
    infer_clusters, suggest_clusters
from sbml_generalization.generalization.vertical_key import get_vk2r_ids
from sbml_generalization.utils.misc import invert_map
from sbml_generalization.onto.obo_ontology import Term
from sbml_generalization.annotation.mark_ubiquitous import UBIQUITOUS_THRESHOLD


__author__ = 'anna'

EQUIVALENT_TERM_RELATIONSHIPS = {'is_conjugate_base_of', 'is_conjugate_acid_of', 'is_tautomer_of'}


def generalize_reactions(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
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


def filter_clu_to_terms(term2clu):
    clu2term = invert_map(term2clu)
    for clu, terms in clu2term.iteritems():
        if len(terms) == 1:
            del term2clu[terms.pop()]


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


def maximization_step(model, onto, species_id2chebi_id, term_id2clu, ub_term_ids, unmapped_s_ids):
    onto_updated = True
    while onto_updated:
        logging.info("  satisfying metabolite diversity...")
        term_id2clu = maximize(unmapped_s_ids, model, term_id2clu, species_id2chebi_id, ub_term_ids)
        onto_updated = cover_with_onto_terms(model, onto, species_id2chebi_id, term_id2clu, ub_term_ids)


def fix_incompatibilities(unmapped_s_ids, model, onto, species_id2chebi_id, ubiquitous_chebi_ids):
    if not ubiquitous_chebi_ids:
        ubiquitous_chebi_ids = set()
    chebi_ids = set(species_id2chebi_id.itervalues()) - ubiquitous_chebi_ids

    logging.info("  aggressive metabolite grouping...")
    term_id2clu = cover_t_ids(model, species_id2chebi_id, ubiquitous_chebi_ids, chebi_ids, onto)
    onto.trim({it[0] for it in term_id2clu.itervalues()}, relationships=EQUIVALENT_TERM_RELATIONSHIPS)
    suggest_clusters(model, unmapped_s_ids, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
    # filter_clu_to_terms(term_id2clu)
    # log_clus(term_id2clu, onto, model)

    maximization_step(model, onto, species_id2chebi_id, term_id2clu, ubiquitous_chebi_ids, unmapped_s_ids)
    # filter_clu_to_terms(term_id2clu)
    # log_clus(term_id2clu, onto, model)

    logging.info("  preserving stoichiometry...")
    fix_stoichiometry(model, term_id2clu, species_id2chebi_id, ubiquitous_chebi_ids, onto)
    # filter_clu_to_terms(term_id2clu)
    # log_clus(term_id2clu, onto, model)

    maximization_step(model, onto, species_id2chebi_id, term_id2clu, ubiquitous_chebi_ids, unmapped_s_ids)
    # filter_clu_to_terms(term_id2clu)
    # log_clus(term_id2clu, onto, model)

    return term_id2clu


def log_clus(term_id2clu, onto, model):
    clu2term = invert_map(term_id2clu)
    blueprint = []
    msg = ''
    for clu in sorted(clu2term.iterkeys(), key=lambda k: -len(clu2term[k])):
        term_ids = clu2term[clu]
        if len(term_ids) == 1:
            continue
        blueprint.append(len(term_ids))
        msg += "(%s) <-> %s\n" % (len(term_ids), [
            onto.get_term(it).get_name() if onto.get_term(it) else model.getSpecies(
                it).getName() if model.getSpecies(it) else it for it in term_ids])
    logging.info("    quotient species sets: %s\n%s\n\n" % (sorted(blueprint), msg))


def generalize_species(model, s_id2chebi_id, ub_s_ids, onto, ub_chebi_ids, threshold=UBIQUITOUS_THRESHOLD):
    unmapped_s_ids = {s.getId() for s in model.getListOfSpecies() if s.getId() not in s_id2chebi_id}
    term_id2clu = fix_incompatibilities(unmapped_s_ids, model, onto, s_id2chebi_id, ub_chebi_ids)
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
