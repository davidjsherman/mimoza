from dircache import listdir
import os
import sys

import libsbml
from orangecontrib.bio.ontology import OBOOntology

from sbml_generalization.onto.onto_getter import get_chebi
from sbml_generalization.annotation.miriam_converter import to_identifiers_org_format
from sbml_generalization.annotation.rdf_annotation_helper import add_annotation
from sbml_generalization.sbml.sbml_helper import create_compartment, create_species, create_reaction, save_as_sbml

RHEA_IN_DIR = "/home/anna/Documents/IBGC/Models/rhea/rd/"
RHEA_OUT_FILE = "/home/anna/Documents/IBGC/Models/rhea/rhea.txt"
RHEA_SBML_DIR = "/home/anna/Documents/IBGC/Models/rhea/sbml/"
RHEA_SBML = "rhea"

__author__ = 'anna'


def normalize(line):
    return line.replace('\n', '').strip().replace('  ', ' ')


def get_rhea_info():
    r2rsps = {}
    for f in listdir(RHEA_IN_DIR):
        if -1 == f.find('.rd'):
            continue
        r_id = f[:f.find('.rd')]
        r_num, p_num = -1, -1
        rs, ps = [], []
        with open(RHEA_IN_DIR + f, 'r') as in_f:
            started = False
            for line in in_f:
                if not started:
                    if line.find("RHEA:release=") == -1:
                        continue
                    else:
                        started = True
                elif r_num == -1:
                    line = normalize(line)
                    r_num, p_num = [int(it) for it in line.split(' ')]
                elif line.find('CHEBI') != -1:
                    chebi = normalize(line)
                    if r_num > 0:
                        rs.append(chebi)
                        r_num -= 1
                    else:
                        ps.append(chebi)
                        p_num -= 1
        r2rsps[r_id] = rs, ps
    return r2rsps


def write_rhea_file(r2rsps):
    with open(RHEA_OUT_FILE, "w+") as rhea_f:
        for r_id, (rs, ps) in r2rsps.iteritems():
            rhea_f.write("%s %s %s\n" % (r_id, ','.join(rs), ','.join(ps)))


def main(argv=None):
    # write_rhea_file(get_rhea_info())
    r_id2rsps = {}
    with open(RHEA_OUT_FILE, "r") as rhea_f:
        for line in rhea_f:
            line = line.replace('\n', '')
            if not line.strip(): continue
            r_id, rs, ps = line.split(' ')
            rs, ps = rs.split(',') if rs else [], ps.split(',') if ps else []
            r_id2rsps[r_id] = rs, ps
    r_ids = list(r_id2rsps.iterkeys())
    r_len = len(r_ids)
    step = r_len + 1
    start = 0
    iteration = 300
    # onto = parse(get_chebi())
    onto = OBOOntology(get_chebi())
    if not os.path.exists(RHEA_SBML_DIR):
        os.makedirs(RHEA_SBML_DIR)
    while start < r_len:
        sbml = "%s%s_%d.xml" % (RHEA_SBML_DIR, RHEA_SBML, iteration)
        to_sbml(r_ids[start: min(start + step, r_len)], r_id2rsps, sbml, onto)
        iteration += 1
        start += step


def to_sbml(r_ids, r2rsps, sbml, onto):
    doc = libsbml.SBMLDocument(2, 4)
    model = doc.createModel()
    model.setName("Rhea")
    model.setId("iRhea")
    comp_id = create_compartment(model, "cell").getId()
    sps = set()
    for r_id in r_ids:
        rs, ps = r2rsps[r_id]
        sps |= set(rs)
        sps |= set(ps)
    c_id2id = {}
    for c_id in sps:
        # term = onto.get_term(c_id)
        name = onto.term(c_id).name if c_id in onto else c_id
        species = create_species(model, comp_id, None, name)
        add_annotation(species, libsbml.BQB_IS, to_identifiers_org_format(c_id))
        c_id2id[c_id] = species.getId()
    for r_id in r_ids:
        rs, ps = r2rsps[r_id]
        reactants = [c_id2id[c_id] for c_id in rs]
        products = [c_id2id[c_id] for c_id in ps]
        reaction = create_reaction(model, reactants, products, r_id, "r_" + r_id)
        add_annotation(reaction, libsbml.BQB_IS, to_identifiers_org_format(r_id))
    if model:
        save_as_sbml(model, sbml)


if __name__ == "__main__":
    sys.exit(main())
