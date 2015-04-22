# !/usr/bin/env python
# encoding: utf-8

import getopt
import logging
import os
from os.path import dirname, abspath
from shutil import copytree

import libsbml

from mimoza.mimoza import JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON, MIMOZA_URL
from sbml.sbgn_helper import save_as_sbgn
from sbml_vis.converter.sbml2tlp import import_sbml
from sbml_vis.file.md5_checker import check_md5
from sbml_vis.file.serializer import serialize
from sbml_vis.converter.tulip_graph2geojson import graph2geojson
import mimoza.mimoza
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.onto.onto_getter import get_chebi
from sbml_generalization.onto.obo_ontology import parse
from sbml_generalization.sbml.sbml_helper import check_for_groups, SBO_CHEMICAL_MACROMOLECULE, \
    GROUP_TYPE_UBIQUITOUS, save_as_layout_sbml, parse_layout_sbml, LoPlError


__author__ = 'anna'
help_message = '''
Generalizes and visualizes an SBML model.
usage: main.py --model model.xml --verbose
'''

import sys


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def process_args(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "m:h:v",
                                   ["help", "model=", "verbose"])
    except getopt.error, msg:
        raise Usage(msg)
    sbml, verbose = None, False
    # option processing
    for option, value in opts:
        if option in ("-h", "--help"):
            raise Usage(help_message)
        if option in ("-m", "--model"):
            sbml = value
        if option in ("-v", "--verbose"):
            verbose = True
    if not sbml:
        raise Usage(help_message)
    return sbml, verbose


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        sbml, verbose = process_args(argv)
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2
    reader = libsbml.SBMLReader()
    doc = reader.readSBML(sbml)
    model = doc.getModel()
    if not model:
        raise Exception("The model should be in SBML format")
    model_id = model.getId()
    if not model_id:
        sbml_name = os.path.splitext(os.path.basename(sbml))[0]
        model.setId(sbml_name)
        model_id = sbml_name

    m_id = check_md5(sbml)
    sbml_dir = dirname(abspath(sbml))
    directory = '%s/%s/' % (sbml_dir, m_id)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists('%s/lib' % directory):
        copytree(get_lib(), '%s/lib' % directory)

    if verbose:
        # log_file = None
        # try:
        # log_file = '%s/log.log' % directory
        # with open(log_file, "w+"):
        #      pass
        # except:
        # 	pass
        logging.captureWarnings(True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")  #, filename=log_file)
        logging.captureWarnings(True)

    groups_sbml = '%s%s_with_groups.xml' % (directory, model_id)
    gen_sbml = '%s%s_generalized.xml' % (directory, model_id)

    if check_for_groups(sbml, SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS):
        if sbml != groups_sbml:
            if not libsbml.SBMLWriter().writeSBMLToFile(doc, groups_sbml):
                raise Exception("Could not write your model to %s" % groups_sbml)
    else:
        chebi = parse(get_chebi())
        _, _, species_id2chebi_id, ub_s_ids = \
            generalize_model(groups_sbml, gen_sbml, sbml, chebi)

    reader = libsbml.SBMLReader()
    input_document = reader.readSBML(groups_sbml)
    input_model = input_document.getModel()

    root, c_id2info, c_id2outs, chebi, ub_sps = import_sbml(input_model, groups_sbml)
    c_id2out_c_id = {}
    for c_id, info in c_id2info.iteritems():
        _, _, (_, out_c_id) = info
        if out_c_id:
            c_id2out_c_id[c_id] = out_c_id

    try:
        n2xy = parse_layout_sbml(sbml)
    except LoPlError:
        n2xy = None

    fc, (n2lo, e2lo) = graph2geojson(c_id2info, c_id2outs, root, chebi, n2xy)

    groups_document = reader.readSBML(groups_sbml)
    groups_model = groups_document.getModel()
    gen_document = reader.readSBML(gen_sbml)
    gen_model = gen_document.getModel()
    save_as_layout_sbml(groups_model, gen_model, groups_sbml, gen_sbml, n2lo, ub_sps)

    logging.info('exporting as SBGN...')
    groups_sbgn = '%s%s.sbgn' % (directory, model_id)
    gen_sbgn = '%s%s_generalized.sbgn' % (directory, model_id)
    save_as_sbgn(n2lo, e2lo, groups_model, groups_sbgn)
    logging.info('   exported as SBGN %s' % groups_sbgn)
    save_as_sbgn(n2lo, e2lo, gen_model, gen_sbgn)
    logging.info('   exported as SBGN %s' % gen_sbgn)

    serialize(directory=directory, m_dir_id=m_id, input_model=input_model, c_id2level2features=fc,
              c_id2out_c_id=c_id2out_c_id, groups_sbml=groups_sbml,
              main_url=MIMOZA_URL, scripts=JS_SCRIPTS, css=CSS_SCRIPTS, fav=MIMOZA_FAVICON)


def get_lib():
    return "%s/../lib" % os.path.dirname(os.path.abspath(mimoza.mimoza.__file__))


if __name__ == "__main__":
    sys.exit(main())