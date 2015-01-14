# !/usr/bin/env python
# encoding: utf-8

import getopt
import logging
import os
from os.path import dirname, abspath
from shutil import copytree

from libsbml import SBMLReader, SBMLWriter

from mimoza.mimoza import JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON, MIMOZA_URL
from sbml_vis.converter.sbml2tlp import import_sbml
from sbml_vis.file.md5_checker import check_md5
from sbml_vis.file.serializer import serialize
from sbml_vis.converter.tulip_graph2geojson import graph2geojson
import mimoza.mimoza
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.utils.obo_ontology import parse, get_chebi
from sbml_generalization.generalization.sbml_helper import check_for_groups, SBO_CHEMICAL_MACROMOLECULE, \
    GROUP_TYPE_UBIQUITOUS, save_as_layout_sbml, \
    parse_layout_sbml, LoPlError


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

    reader = SBMLReader()
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
        # 	with open(log_file, "w+"):
        # 		pass
        # except:
        # 	pass
        logging.basicConfig(level=logging.INFO)  #, filename=log_file)

    groups_sbml = '%s%s_with_groups.xml' % (directory, model_id)
    gen_sbml = '%s%s_generalized.xml' % (directory, model_id)
    # layout_sbml = '%s%s_with_layout.xml' % (directory, model_id)
    # gen_layout_sbml = '%s%s_generalized_with_layout.xml' % (directory, model_id)
    if check_for_groups(sbml, SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS):
        if sbml != groups_sbml:
            if not SBMLWriter().writeSBMLToFile(doc, groups_sbml):
                raise Exception("Could not write your model to %s" % groups_sbml)
    else:
        chebi = parse(get_chebi())
        generalize_model(groups_sbml, gen_sbml, sbml, chebi, cofactors=None,
                         verbose=True)  # , ub_s_ids={'C00112MM', 'C00112Cyto', 'C00112_b', 'C00044MM', 'C00081MM',
        # 'C00104MM', 'C00704MM', 'C00131MM', 'C00131Cyto', 'C00131_b',
        # 'C00286Cyto', 'C00286_b', 'C00286MM', 'C00363Cyto', 'C00363MM',
        # 'C00363_b', 'C00459_b', 'C00459Cyto', 'C00459MM',
        # 'C00008MM', 'C00008Cyto', 'C00008_b', 'C00020MM', 'C00020Cyto',
        # 'C00002_b', 'C00002Cyto', 'C00002MM', 'C00024MM', 'C00033MM',
        # 'C00055MM', 'C00011Cyto', 'C00011_b', 'C00011MM', 'C00063MM',
        # 'C00010MM', 'C00010_b', 'C00010Cyto', 'C00013Cyto', 'C00016MM',
        # 'C00016Cyto', 'C00016_b', 'C01352MM', 'C00035_b', 'C00035MM',
        # 'C00035Cyto', 'C00080Cyto', 'C00080_b', 'C00080MM', 'C00001MM',
        # 'C00001Cyto', 'C00001_b', 'C00027MM', 'C00288Cyto', 'C00288MM',
        # 'C00288_b', 'C00003Cyto', 'C00003_b', 'C00003MM', 'C00004Cyto',
        # 'C00004MM', 'C00006MM', 'C00005MM', 'C00009Cyto', 'C00009MM',
        # 'C00009_b', 'C00007Cyto', 'C00007MM', 'C00007_b', 'C00013MM',
        # 'C00015MM', 'C00015Cyto', 'C00015_b', 'C00075MM', 'C00206_b',
        # 'C00206MM', 'C00206Cyto', 'C00458_b', 'C00458MM', 'C00458Cyto',
        # 'C00361Cyto', 'C00361_b', 'C00229MM', 'C03939MM',
        # 'C00361MM', 'C14818MM', 'C14818Cyto', 'C14818_b',
        # 'C00014MM', 'C00014Cyto'})

    reader = SBMLReader()
    input_document = reader.readSBML(groups_sbml)
    input_model = input_document.getModel()

    root, c_id2info, c_id2outs, chebi, ub_sps = import_sbml(input_model, groups_sbml, True)
    c_id2out_c_id = {}
    for c_id, info in c_id2info.iteritems():
        _, _, (_, out_c_id) = info
        if out_c_id:
            c_id2out_c_id[c_id] = out_c_id

    try:
        n2xy = parse_layout_sbml(sbml)
    except LoPlError:
        n2xy = None

    fc, (n2lo, (d_w, d_h)) = graph2geojson(c_id2info, c_id2outs, root, True, chebi, n2xy)

    groups_document = reader.readSBML(groups_sbml)
    groups_model = groups_document.getModel()
    gen_document = reader.readSBML(gen_sbml)
    gen_model = gen_document.getModel()
    save_as_layout_sbml(groups_model, gen_model, groups_sbml, gen_sbml, n2lo, (d_w, d_h), ub_sps, verbose)

    serialize(directory=directory, m_dir_id=m_id, input_model=input_model, c_id2level2features=fc,
              c_id2out_c_id=c_id2out_c_id, groups_sbml=groups_sbml,
              main_url=MIMOZA_URL, scripts=JS_SCRIPTS, css=CSS_SCRIPTS, fav=MIMOZA_FAVICON, verbose=verbose)


def get_lib():
    return "%s/../lib" % os.path.dirname(os.path.abspath(mimoza.mimoza.__file__))


if __name__ == "__main__":
    sys.exit(main())