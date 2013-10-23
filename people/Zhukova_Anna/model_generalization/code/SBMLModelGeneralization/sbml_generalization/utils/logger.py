import datetime
from sbml_generalization.utils.misc import invert_map

__author__ = 'anna'


def log(verbose, msg):
    if verbose:
        print msg
        print datetime.datetime.now().time()
        print


def log_chains(chains, verbose):
    if not verbose:
        return
    print "reaction chains:"
    blueprint = []
    for chain in chains:
        s_ids, key, r_ids = chain
        print "   ", key[1], " : ", len(r_ids)
        blueprint.append(len(r_ids))
    print "   ", sorted(blueprint)


def log_clusters(term_id2clu, onto, verbose):
    if not verbose:
        return
    clu2term = invert_map(term_id2clu)
    print "quotient species sets:"
    blueprint = []
    for clu in sorted(clu2term.iterkeys(), key=lambda k: -len(clu2term[k])):
        term_ids = clu2term[clu]
        if len(term_ids) == 1:
            continue
        blueprint.append(len(term_ids))
        print "   ", onto.getTerm(clu).getName(), " (", len(term_ids), ") <-> ", [onto.getTerm(it).getName() for it in
                                                                                  term_ids]
    print "   ", sorted(blueprint)