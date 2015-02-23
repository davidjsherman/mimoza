import logging

from sbml_generalization.utils.misc import invert_map


__author__ = 'anna'


def log(verbose, msg):
    if verbose:
        logging.info(msg)


def log_clus(term_id2clu, onto, model, verbose):
    if verbose:
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
