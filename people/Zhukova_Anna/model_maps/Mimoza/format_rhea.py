from dircache import listdir
import os
import sys

import libsbml

from mod_sbml.annotation.chebi.chebi_annotator import CHEBI_PREFIX
from mod_sbml.annotation.chebi.chebi_serializer import get_chebi
from mod_sbml.annotation.miriam_converter import to_identifiers_org_format
from mod_sbml.annotation.rdf_annotation_helper import add_annotation
from mod_sbml.onto import parse
from sbml_generalization.sbml.sbml_helper import create_species, save_as_sbml
from mod_sbml.sbml.sbml_manager import create_reaction, create_compartment

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
    r_id2m_id2st = {}
    with open(RHEA_OUT_FILE, "r") as rhea_f:
        for line in rhea_f:
            line = line.replace('\n', '')
            if not line.strip(): continue
            r_id, rs, ps = line.split(' ')
            rs, ps = rs.split(',') if rs else [], ps.split(',') if ps else []
            r_id2m_id2st[r_id] = {m_id: 1 for m_id in rs}, {m_id: 1 for m_id in ps}
    r_ids = list(r_id2m_id2st.iterkeys())
    r_len = len(r_ids)
    step = r_len + 1
    start = 0
    iteration = 300
    # onto = parse(get_chebi())
    onto = parse(get_chebi())
    if not os.path.exists(RHEA_SBML_DIR):
        os.makedirs(RHEA_SBML_DIR)
    while start < r_len:
        sbml = "%s%s_%d.xml" % (RHEA_SBML_DIR, RHEA_SBML, iteration)
        to_sbml(r_ids[start: min(start + step, r_len)], r_id2m_id2st, sbml, onto)
        iteration += 1
        start += step


def to_sbml(r_ids, r2m_id2st, sbml, onto):
    doc = libsbml.SBMLDocument(2, 4)
    model = doc.createModel()
    model.setName("Rhea")
    model.setId("iRhea")
    comp_id = create_compartment(model, "cell").getId()
    sps = set()
    for r_id in r_ids:
        m_id2st = r2m_id2st[r_id]
        sps |= set(m_id2st.iterkeys())
    c_id2id = {}
    for c_id in sps:
        # term = onto.get_term(c_id)
        name = onto.get_term(c_id).get_name() if c_id in onto else c_id
        species = create_species(model, compartment_id=comp_id, name=name)
        add_annotation(species, libsbml.BQB_IS, to_identifiers_org_format(c_id, CHEBI_PREFIX))
        c_id2id[c_id] = species.getId()
    for r_id in r_ids:
        r_id2st, p_id2st = r2m_id2st[r_id]
        r_id2st = {c_id2id[m_id]: st for (m_id, st) in r_id2st.iteritems()}
        p_id2st = {c_id2id[m_id]: st for (m_id, st) in p_id2st.iteritems()}
        create_reaction(model, r_id2st, p_id2st, name=r_id, id_="r_" + r_id)
    if model:
        save_as_sbml(model, sbml)


if __name__ == "__main__":
    sys.exit(main())
