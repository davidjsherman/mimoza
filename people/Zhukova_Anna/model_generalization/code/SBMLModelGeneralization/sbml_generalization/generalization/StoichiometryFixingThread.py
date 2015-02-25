from collections import defaultdict, Counter
from itertools import chain
import threading
from sbml_generalization.generalization.reaction_filters import get_reactants, get_products
from sbml_generalization.generalization.vertical_key import get_vk2r_ids, vk2s_vk, get_vertical_key, get_r_compartments
from sbml_generalization.utils.misc import invert_map

__author__ = 'anna'

st_fix_lock = threading.RLock()


def compute_s_id2clu(unmapped_s_ids, model, species_id2term_id, term_id2clu):
    s_id2clu = {}
    for s_id, t_id in species_id2term_id.iteritems():
        if t_id in term_id2clu:
            s_id2clu[s_id] = (model.getSpecies(s_id).getCompartment(), term_id2clu[t_id])
    for s_id in unmapped_s_ids:
        if s_id in term_id2clu:
            s_id2clu[s_id] = (model.getSpecies(s_id).getCompartment(), term_id2clu[s_id])
    return s_id2clu


def good(t_set, conflicts):
    if not t_set:
        return False
    if len(t_set) == 1:
        return True
    for c_ts in conflicts:
        if len(t_set & c_ts) > 1:
            return False
    return True


def get_most_problematic_term(t_set, conflicts):
    if not t_set or len(t_set) == 1:
        return None
    result = Counter()
    for c_ts in conflicts:
        common = t_set & c_ts
        if len(common) > 1:
            result.update({t: 1 for t in common})
    return max(result.iterkeys(), key=lambda t: result[t])


def get_conflict_num(t_set, conflicts):
    if not t_set or len(t_set) == 1:
        return 0
    res = 0
    for c_ts in conflicts:
        res += len(t_set & c_ts) / 2
    return res


def suggest_clusters(model, unmapped_s_ids, term_id2clu, s_id2term_id, ubiquitous_chebi_ids):
    if not unmapped_s_ids:
        return
    s_id2clu = compute_s_id2clu(set(), model, s_id2term_id, term_id2clu)
    term_id2s_ids = invert_map(s_id2term_id)
    vk2r_ids = get_vk2r_ids(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids)
    vk2r_ids = {vk: r_ids for (vk, r_ids) in vk2r_ids.iteritems() if len(r_ids) > 1}
    processed_r_ids = reduce(lambda s1, s2: s1 | s2, vk2r_ids.itervalues(), set())

    s_vk2vk = defaultdict(set)
    for vk in vk2r_ids.iterkeys():
        s_vk2vk[vk2s_vk(vk)].add(vk)

    s_id2r_ids = defaultdict(list)
    for r in (r for r in model.getListOfReactions() if r.getNumReactants() + r.getNumProducts() > 2):
        r_id = r.getId()
        for s_id in chain((species_ref.getSpecies() for species_ref in r.getListOfReactants()),
                          (species_ref.getSpecies() for species_ref in r.getListOfProducts())):
            s_id2r_ids[s_id].append(r_id)

    for r in model.getListOfReactions():
        if r.getId() in processed_r_ids or not unmapped_s_ids & (get_reactants(r) | get_products(r)):
            continue
        ub_rs, ub_ps, rs, ps = get_vertical_key(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids)
        vk = (ub_rs, ub_ps, rs, ps), get_r_compartments(model, r)
        rs, ps = set(rs), set(ps)
        partial_rs, partial_ps = {s_id for s_id in rs if s_id not in unmapped_s_ids}, {s_id for s_id in ps if s_id not in unmapped_s_ids}
        if vk in vk2r_ids or len(ub_rs) + len(ub_ps) + len(partial_rs) + len(partial_ps) < 2:
            continue
        s_vk = vk2s_vk(vk)
        if s_vk in s_vk2vk:
            ub_rs, ub_ps = tuple(sorted(ub_rs)), tuple(sorted(ub_ps))
            for ((vk_ub_rs, vk_ub_ps, vk_rs, vk_ps), comps) in s_vk2vk[s_vk]:
                vk_rs, vk_ps = {s_id if s_id not in s_id2clu else  s_id2clu[s_id] for s_id in vk_rs}, \
                         {s_id if s_id not in s_id2clu else s_id2clu[s_id] for s_id in vk_ps}
                proposal = {}
                if vk_ub_rs == ub_ps and vk_ub_ps == ub_rs and not partial_rs - vk_ps and not partial_ps - vk_rs:
                    vk_ub_rs, vk_ub_ps, partial_rs, partial_ps = vk_ub_ps, vk_ub_rs, partial_ps, partial_rs
                if vk_ub_rs == ub_rs and vk_ub_ps == ub_ps and not partial_rs - vk_rs and not partial_ps - vk_ps:
                    r_s_ids = rs - vk_rs
                    p_s_ids = ps - vk_ps
                    if 0 < len(r_s_ids) <= 1 and 0 < len(p_s_ids) <= 1 and r_s_ids or p_s_ids:
                        if r_s_ids and vk_rs - rs:
                            s_id = r_s_ids.pop()
                            clu = (vk_rs - rs).pop()
                            # if it is a species id instead of a cluster, continue
                            if not isinstance(clu, tuple):
                                continue
                            # if it is not a species id but a cluster, continue
                            if not isinstance(s_id, str):
                                continue
                            candidate_sps = {model.getSpecies(sp_id) for sp_id in
                                             (term_id2s_ids[s_id2term_id[s_id]] if s_id in s_id2term_id else [s_id])}
                            comp, term = clu
                            for s in candidate_sps:
                                proposal[s.getId()] = term
                        if p_s_ids and vk_ps - ps:
                            s_id = p_s_ids.pop()
                            clu = (vk_ps - ps).pop()
                            # if it is a species id instead of a cluster, continue
                            if not isinstance(clu, tuple):
                                continue
                            # if it is not a species id but a cluster, continue
                            if not isinstance(s_id, str):
                                continue
                            candidate_sps = {model.getSpecies(it) for it in
                                             (term_id2s_ids[s_id2term_id[s_id]] if s_id in s_id2term_id else {s_id})}
                            comp, term = clu
                            for s in candidate_sps:
                                proposal[s.getId()] = term
                if proposal:
                    for s_id, clu in proposal.iteritems():
                        term_id2clu[s_id] = clu
                        unmapped_s_ids -= {s_id}


def infer_clusters(model, unmapped_s_ids, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
    if not unmapped_s_ids:
        return
    term_id2s_ids = invert_map(s_id2term_id)
    clu2s_ids = invert_map(s_id2clu)
    vk2r_ids = get_vk2r_ids(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids)
    vk2r_ids = {vk: r_ids for (vk, r_ids) in vk2r_ids.iteritems() if len(r_ids) > 1}
    processed_r_ids = reduce(lambda s1, s2: s1 | s2, vk2r_ids.itervalues(), set())

    s_vk2vk = defaultdict(set)
    for vk in vk2r_ids.iterkeys():
        s_vk2vk[vk2s_vk(vk)].add(vk)

    s_id2r_ids = defaultdict(list)
    for r in (r for r in model.getListOfReactions() if r.getNumReactants() + r.getNumProducts() > 2):
        r_id = r.getId()
        for s_id in chain((species_ref.getSpecies() for species_ref in r.getListOfReactants()),
                          (species_ref.getSpecies() for species_ref in r.getListOfProducts())):
            s_id2r_ids[s_id].append(r_id)

    def in_species_conflict(term, candidate_sps, proposal_s_id2clu):
        proposal_clu2s_ids = invert_map(proposal_s_id2clu)
        for s in candidate_sps:
            s_clu = s.getCompartment(), term
            rs = {r_id for r_id in s_id2r_ids[s.getId()]}
            clu_s_ids = clu2s_ids[s_clu] | proposal_clu2s_ids[s_clu]
            for clu_s_id in clu_s_ids:
                if {r_id for r_id in s_id2r_ids[clu_s_id]} & rs:
                    return True
        return False

    for r in model.getListOfReactions():
        if r.getId() in processed_r_ids or not unmapped_s_ids & (get_reactants(r) | get_products(r)):
            continue
        ub_rs, ub_ps, rs, ps = get_vertical_key(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids)
        vk = (ub_rs, ub_ps, rs, ps), get_r_compartments(model, r)
        rs, ps = set(rs), set(ps)
        partial_rs, partial_ps = {s_id for s_id in rs if s_id not in unmapped_s_ids}, {s_id for s_id in ps if s_id not in unmapped_s_ids}
        if vk in vk2r_ids or len(ub_rs) + len(ub_ps) + len(partial_rs) + len(partial_ps) < 2:
            continue
        s_vk = vk2s_vk(vk)
        if s_vk in s_vk2vk:
            ub_rs, ub_ps = tuple(sorted(ub_rs)), tuple(sorted(ub_ps))
            for ((vk_ub_rs, vk_ub_ps, vk_rs, vk_ps), comps) in s_vk2vk[s_vk]:
                vk_rs, vk_ps = {s_id if s_id not in s_id2clu else  s_id2clu[s_id] for s_id in vk_rs}, \
                         {s_id if s_id not in s_id2clu else s_id2clu[s_id] for s_id in vk_ps}
                proposal = {}
                if vk_ub_rs == ub_ps and vk_ub_ps == ub_rs and not partial_rs - vk_ps and not partial_ps - vk_rs:
                    vk_ub_rs, vk_ub_ps, partial_rs, partial_ps = vk_ub_ps, vk_ub_rs, partial_ps, partial_rs
                if vk_ub_rs == ub_rs and vk_ub_ps == ub_ps and not partial_rs - vk_rs and not partial_ps - vk_ps:
                    r_s_ids = rs - vk_rs
                    p_s_ids = ps - vk_ps
                    if 0 < len(r_s_ids) <= 1 and 0 < len(p_s_ids) <= 1 and r_s_ids or p_s_ids:
                        if r_s_ids and vk_rs - rs:
                            s_id = r_s_ids.pop()
                            clu = (vk_rs - rs).pop()
                            # if it is a species id instead of a cluster, continue
                            if not isinstance(clu, tuple):
                                continue
                            candidate_sps = {model.getSpecies(it) for it in
                                             (term_id2s_ids[s_id2term_id[s_id]] if s_id in s_id2term_id else {s_id})}
                            comp, term = clu
                            if not in_species_conflict(term, candidate_sps, proposal):
                                for s in candidate_sps:
                                    proposal[s.getId()] = s.getCompartment(), term
                            else:
                                continue
                        if p_s_ids and vk_ps - ps:
                            s_id = p_s_ids.pop()
                            clu = (vk_ps - ps).pop()
                            # if it is a species id instead of a cluster, continue
                            if not isinstance(clu, tuple):
                                continue
                            candidate_sps = {model.getSpecies(it) for it in
                                             (term_id2s_ids[s_id2term_id[s_id]] if s_id in s_id2term_id else {s_id})}
                            comp, term = clu
                            if not in_species_conflict(term, candidate_sps, proposal):
                                for s in candidate_sps:
                                    proposal[s.getId()] = s.getCompartment(), term
                            else:
                                continue
                if proposal:
                    s_id2clu.update(proposal)
                    for s_id, clu in proposal.iteritems():
                        clu2s_ids[clu].add(s_id)
                    unmapped_s_ids -= set(proposal.iterkeys())


class StoichiometryFixingThread(threading.Thread):
    def __init__(self, model, s_id2term_id, ub_chebi_ids, unmapped_s_ids, term_ids, conflicts, onto, clu, term_id2clu):
        threading.Thread.__init__(self)
        self.ub_chebi_ids = ub_chebi_ids
        self.s_id2term_id = s_id2term_id
        self.model = model
        self.unmapped_s_ids = set(unmapped_s_ids)
        self.term_ids = set(term_ids)
        self.onto = onto
        self.clu = clu
        self.term_id2clu = term_id2clu
        self.conflicts = conflicts

    def get_common_roots(self):
        # the least common ancestors, or roots if there are none
        common_ancestor_terms = self.onto.common_points({self.onto.get_term(t) for t in self.term_ids}, 3)
        if not common_ancestor_terms:
            terms = (self.onto.get_term(t) for t in self.term_ids)
            common_ancestor_terms = \
                reduce(lambda s1, s2: s1 | s2,
                       (self.onto.get_generalized_ancestors_of_level(term, set(), None, 3) for term in terms if term),
                       set())
        return common_ancestor_terms

    def get_covered_term_ids(self, term, term_ids):
        return term_ids & {t.get_id() for t in self.onto.get_sub_tree(term)}

    def get_level(self, t):
        level = self.onto.get_level(t)
        return sum(level) / len(level)

    def get_psi_set(self, conflicts):
        common_ancestor_terms = self.get_common_roots()

        psi, basics, set2score = set(), [], {}

        def process(covered_term_ids, score, basics):
            covered_term_ids_tuple = tuple(covered_term_ids)
            if covered_term_ids_tuple in psi:
                return False
            if get_conflict_num(covered_term_ids, conflicts) > 40:
                return True
            basics.append(covered_term_ids)
            psi.add(covered_term_ids_tuple)
            set2score[covered_term_ids_tuple] = score
            return True

        # sets defined by the least common ancestors
        for t_id in self.term_ids:
            term = self.onto.get_term(t_id)
            ancestor_level = self.get_level(term) if term else 0
            process({t_id}, (3, ancestor_level), basics)

        processed = set(self.term_ids)

        for common_ancestor in common_ancestor_terms:
            if common_ancestor.get_id() in processed:
                continue
            processed.add(common_ancestor.get_id())

            common_ancestor_covered_term_ids = self.get_covered_term_ids(common_ancestor, self.term_ids)
            ancestor_level = self.get_level(common_ancestor)
            process(common_ancestor_covered_term_ids, (3, ancestor_level), basics)
            for t in self.onto.get_generalized_descendants(common_ancestor, False, set()):
                if t.get_id() in processed:
                    continue
                processed.add(t.get_id())
                t_covered_term_ids = self.get_covered_term_ids(t, common_ancestor_covered_term_ids)
                if not t_covered_term_ids:
                    continue
                t_level = self.get_level(t)
                process(t_covered_term_ids, (3, t_level), basics)
                # if process(t_covered_term_ids, (3, t_level), basics):
                    # complement set
                    # complement = common_ancestor_covered_term_ids - t_covered_term_ids
                    # if complement:
                    #     process(complement, (2, ancestor_level), basics)

        # if len(self.term_ids) + len(conflicts) < 60:
        #     # the differences between sets already in Psi
        #     for _ in xrange(2):
        #         to_add = []
        #         i = 0
        #         for basic in basics:
        #             i1, j1 = set2score[tuple(basic)]
        #             i += 1
        #             for t_covered_term_ids in basics[i:]:
        #                 for complement_covered_term_ids in (basic - t_covered_term_ids, t_covered_term_ids - basic):
        #                     if complement_covered_term_ids:
        #                         i0, j0 = set2score[tuple(t_covered_term_ids)]
        #                         score = min(i0, i1) - 1, min(j0, j1)
        #                         process(complement_covered_term_ids, score, to_add)
        #         basics += to_add

        # result = [term_set for term_set in psi if good(set(term_set), conflicts)]
        result = psi
        return result, set2score

    def greedy(self, psi, set2score, conflicts):
        terms = set(self.term_ids)
        while terms and psi:
            if good(set(terms), conflicts):
                yield terms
                break
            s = max((term_set for term_set in psi if good(set(term_set), conflicts)), key=lambda candidate_terms: (len(set(candidate_terms) & terms), set2score[candidate_terms]))
            result = set(s)
            if len(result & terms) == 1:
                problematic_term = get_most_problematic_term(set(terms), conflicts)
                if problematic_term:
                    s = (problematic_term,)
                    result = {problematic_term}
            yield result & terms
            terms -= result
            psi.remove(s)

    def run(self):
        conflicts = self.conflicts
        if not conflicts:
            return
        psi, set2score = self.get_psi_set(conflicts)
        i = 0
        for ts in self.greedy(psi, set2score, conflicts):
            i += 1
            n_clu = self.clu + (i,)
            with st_fix_lock:
                for t in ts:
                    # clu[0] is a compartment_id
                    self.term_id2clu[t] = n_clu
        s_id2clu = compute_s_id2clu(set(), self.model, self.s_id2term_id, self.term_id2clu)
        infer_clusters(self.model, self.unmapped_s_ids, s_id2clu, self.s_id2term_id, self.ub_chebi_ids)
        for s_id in self.unmapped_s_ids:
            with st_fix_lock:
                if s_id in s_id2clu:
                    self.term_id2clu[s_id] = s_id2clu[s_id][1]
                elif s_id in self.term_id2clu:
                    del self.term_id2clu[s_id]