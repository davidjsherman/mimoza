from genericpath import exists, isfile
from os import listdir, makedirs
import sys

from sbml_generalization.utils.logger import log
from sbml_generalization.utils.obo_ontology import parse, get_chebi
from sbml_generalization.generalization.sbml_generalizer import convert
from sbml_generalization.generalization.mark_ubiquitous import getCofactors
from sbml_generalization.runner.path2models.gather_FA_statistics import get_statistics


__author__ = 'anna'

ROOT_DIR = "/Users/anna/Documents/PhD/magnome/MCCMB13/models/paper/sbml/"


def main(argv=None):
    chebi = get_chebi()
    verbose = True
    generalize_many(chebi, verbose)
    get_statistics()


def generalize_many(chebi, verbose):
    # annotate with ChEBI
    log(verbose, "parsing ChEBI...")
    ontology = parse(chebi)
    cofactor_ids = getCofactors(ontology)
    in_path = ROOT_DIR + "biomodels/"
    out_path = ROOT_DIR + "gen_biomodels/"
    if not exists(out_path):
        makedirs(out_path)
    gr_path = ROOT_DIR + "gr_biomodels/"
    if not exists(gr_path):
        makedirs(gr_path)
        for f in listdir(in_path):
            in_sbml = in_path + f
            out_sbml = out_path + f
            groups_sbml = gr_path + f
            if not isfile(in_sbml) or in_sbml.find(".xml") == -1:
                continue
            log(verbose, "Processing " + in_sbml)
            convert(out_sbml, groups_sbml, in_sbml, ontology, cofactor_ids, None, verbose)


if __name__ == "__main__":
    sys.exit(main())