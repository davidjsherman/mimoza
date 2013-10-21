from genericpath import exists, isfile
from os import listdir, makedirs
import sys
from generalization.mark_ubiquitous import getCofactors
from generalization.sbml_generalizer import convert
from runner.path2models.gather_FA_statistics import get_statistics
from utils.logger import log
from utils.obo_ontology import parse, get_chebi

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
            convert(ontology, cofactor_ids, in_sbml, out_sbml, groups_sbml, None, verbose)


if __name__ == "__main__":
    sys.exit(main())