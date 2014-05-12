import datetime
import logging
from sbml_generalization.utils.misc import invert_map

__author__ = 'anna'


def log(verbose, msg):
	if verbose:
		msg = '%s\n%s\n' % (msg, datetime.datetime.now().time())
		logging.info(msg)


def log_chains(chains, verbose):
	if verbose:
		logging.info("reaction chains:")
		blueprint = []
		for chain in chains:
			s_ids, key, r_ids = chain
			logging.info("   %s : %s" % (key[1], len(r_ids)))
			blueprint.append(len(r_ids))
		logging.info("   %s\n" % sorted(blueprint))


def log_clusters(term_id2clu, onto, verbose, blueprint_only=False):
	if verbose:
		clu2term = invert_map(term_id2clu)
		blueprint = []
		msg = ''
		for clu in sorted(clu2term.iterkeys(), key=lambda k: -len(clu2term[k])):
			term_ids = clu2term[clu]
			if len(term_ids) == 1:
				continue
			blueprint.append(len(term_ids))
			if not blueprint_only:
				msg += "   %s (%s) <-> %s\n" % ((onto.getTerm(clu[1]).getName(), clu[0]) if isinstance(clu[1], str)
				                                else clu, len(term_ids), [onto.getTerm(it[0]).getName() for it in term_ids])
		logging.info("quotient species sets:   %s\n" % sorted(blueprint))
		if not blueprint_only:
			logging.info("   %s\n" % msg)


def log_r_clusters(r_id2clu, verbose):
	if verbose:
		clu2r = invert_map(r_id2clu)
		logging.info("quotient reaction sets:")
		blueprint = []
		for clu in sorted(clu2r.iterkeys(), key=lambda k: -len(clu2r[k])):
			rs = clu2r[clu]
			if len(rs) == 1:
				continue
			blueprint.append(len(rs))
			# print "   ", model.getReaction(list(rs)[0]).getName(), " (", len(rs), ") "
		logging.info("   %s\n" % sorted(blueprint))