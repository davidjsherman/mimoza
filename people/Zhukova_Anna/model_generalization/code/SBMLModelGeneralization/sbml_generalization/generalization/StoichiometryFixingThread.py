from collections import defaultdict
import threading
from sbml_generalization.generalization.reaction_filters import get_reactions_by_term

__author__ = 'anna'

st_fix_lock = threading.RLock()


def good(t_set, conflicts):
	if not t_set:
		return False
	if len(t_set) == 1:
		return True
	for c_ts in conflicts:
		if len(t_set & c_ts) > 1:
			return False
	return True


def get_conflict_num(t_set, conflicts):
	if not t_set or len(t_set) == 1:
		return 0
	res = 0
	for c_ts in conflicts:
		res += len(t_set & c_ts) / 2
	return res


class StoichiometryFixingThread(threading.Thread):
	def __init__(self, model, term_ids, species_id2term_id, onto, clu, term_id2clu):
		threading.Thread.__init__(self)
		self.model = model
		self.term_ids = term_ids
		self.species_id2term_id = species_id2term_id
		self.onto = onto
		self.clu = clu
		self.term_id2clu = term_id2clu
		# self.term_id2clu = defaultdict()

	def get_conflicts(self):
		term_id2s_ids = defaultdict(set)
		for s_id, t_id in self.species_id2term_id.iteritems():
			c_id = self.model.getSpecies(s_id).getCompartment()
			if (t_id, c_id) in self.term_ids:
				term_id2s_ids[t_id, c_id].add(s_id)
		r2term_ids = defaultdict(set)
		rs = list(self.model.getListOfReactions())
		for t_id in self.term_ids:
			for r in get_reactions_by_term(t_id, rs, term_id2s_ids):
				r2term_ids[r.getId()].add(t_id)
		return [{t_id for (t_id, _) in terms} for terms in r2term_ids.itervalues() if len(terms) > 1]

	def get_common_roots(self):
		# the least common ancestors, or roots if there are none
		common_ancestor_terms = self.onto.common_points({self.onto.get_term(t) for t in self.term_ids}, 3)
		if not common_ancestor_terms:
			common_ancestor_terms = set()
			for t in self.term_ids:
				term = self.onto.get_term(t)
				# then it's a fake term
				if not term:
					continue
				common_ancestor_terms |= self.onto.get_generalized_ancestors_of_level(term, set(), None, 3)
		return common_ancestor_terms

	def get_covered_term_ids(self, term, term_ids):
		result = set()
		for sub_t in self.onto.get_sub_tree(term):
			sub_t_id = sub_t.get_id()
			if sub_t_id in term_ids:
				result.add(sub_t_id)
		return result

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
		processed = set()
		for T in common_ancestor_terms:
			T_covered_term_ids = self.get_covered_term_ids(T, self.term_ids)
			T_level = self.get_level(T)
			process(T_covered_term_ids, (3, T_level), basics)
			for t in self.onto.get_generalized_descendants(T, False, set()):
				if t in processed:
					continue
				processed.add(t)

				t_covered_term_ids = self.get_covered_term_ids(t, T_covered_term_ids)
				if not t_covered_term_ids:
					continue
				t_level = self.get_level(t)
				if process(t_covered_term_ids, (3, t_level), basics):
					# complement set
					complement = T_covered_term_ids - t_covered_term_ids
					if complement:
						process(complement, (2, T_level), basics)

		if len(self.term_ids) + len(conflicts) < 60:
			# the differences between sets already in Psi
			for _ in xrange(2):
				to_add = []
				i = 0
				for basic in basics:
					i1, j1 = set2score[tuple(basic)]
					i += 1
					for t_covered_term_ids in basics[i:]:
						for complement_covered_term_ids in (basic - t_covered_term_ids, t_covered_term_ids - basic):
							if complement_covered_term_ids:
								i0, j0 = set2score[tuple(t_covered_term_ids)]
								score = min(i0, i1) - 1, min(j0, j1)
								process(complement_covered_term_ids, score, to_add)
				basics += to_add

		result = [term_set for term_set in psi if good(set(term_set), conflicts)]
		return result, set2score

	def greedy(self, psi, set2score):
		terms = set(self.term_ids)
		while terms and psi:
			s = max(psi, key=lambda candidate_terms: (len(set(candidate_terms) & terms), set2score[candidate_terms]))
			result = set(s)
			#yield result
			yield result & terms
			terms -= result
			psi.remove(s)

	def run(self):
		conflicts = self.get_conflicts()
		if not conflicts:
			return
		self.term_ids = {t_id for (t_id, _) in self.term_ids}
		psi, set2score = self.get_psi_set(conflicts)
		i = 0
		for ts in self.greedy(psi, set2score):
			i += 1
			n_clu = self.clu + (i,)
			with st_fix_lock:
				for t in ts:
					# clu[0] is a compartment_id
					self.term_id2clu[(t, self.clu[0])] = n_clu