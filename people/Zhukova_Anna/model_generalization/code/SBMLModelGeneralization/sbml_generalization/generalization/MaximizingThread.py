from collections import defaultdict
import threading
from sbml_generalization.generalization.reaction_filters import get_reactions_by_term
from sbml_generalization.generalization.vertical_key import get_vertical_key

__author__ = 'anna'

max_lock = threading.RLock()


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


class MaximizingThread(threading.Thread):
	def __init__(self, model, term_ids, term_id2s_ids, species_id2term_id, clu, term_id2clu, s_id2clu,
	             ubiquitous_chebi_ids, r_id2clu):
		threading.Thread.__init__(self)
		self.model = model
		self.term_ids = term_ids
		self.term_id2s_ids = term_id2s_ids
		self.species_id2term_id = species_id2term_id
		self.clu = clu
		self.term_id2clu = term_id2clu
		self.s_id2clu = s_id2clu
		self.ubiquitous_chebi_ids = ubiquitous_chebi_ids
		self.r_id2clu = r_id2clu

	def run(self):
		neighbours2term_ids = defaultdict(set)
		neighbourless_terms = set()
		rs = list(self.model.getListOfReactions())
		for t_id in self.term_ids:
			neighbours = {
				("in" if t_id in get_vertical_key(r, self.s_id2clu, self.species_id2term_id, self.ubiquitous_chebi_ids)[
					3] else "out",
				 self.r_id2clu[r.getId()]) for r
				in get_reactions_by_term(t_id, rs, self.term_id2s_ids)}
			if neighbours:
				key = tuple(neighbours)
				neighbours2term_ids[key].add(t_id)
			else:
				neighbourless_terms.add(t_id)
		new_lst = merge_based_on_neighbours(neighbours2term_ids.iteritems())
		i = 0
		if len(new_lst) > 1:
			for neighbours, term_ids in new_lst:
				n_clu = self.clu + (i,)
				i += 1
				with max_lock:
					for t in term_ids:
						self.term_id2clu[t] = n_clu
		with max_lock:
			for t in neighbourless_terms:
				self.term_id2clu[t] = self.clu + (i,)
				i += 1