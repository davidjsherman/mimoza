import logging
import os
from os.path import dirname, abspath
from shutil import copytree

import libsbml

from sbml_vis.converter.sbml2tlp import import_sbml
from sbml_vis.converter.tulip_graph2geojson import graph2geojson
from sbml_vis.file.md5_checker import check_md5
from sbml_vis.file.serializer import serialize
from sbml_generalization.generalization.sbml_generalizer import generalize_model, ubiquitize_model
from mimoza.mimoza_path import MIMOZA_URL, JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON
import mimoza
from sbml_generalization.onto.obo_ontology import parse
from sbml_generalization.onto.onto_getter import get_chebi
from sbml_generalization.sbml.sbgn_helper import save_as_sbgn
from sbml_generalization.sbml.sbml_helper import parse_layout_sbml, LoPlError, save_as_layout_sbml, check_for_groups, \
    SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS

__author__ = 'anna'

def get_lib():
    return os.path.join(os.path.dirname(os.path.abspath(mimoza.mimoza_path.__file__)), '..', 'lib')

def process_sbml(sbml, verbose, ub_ch_ids=None, path=None, generalize=True, log_file=None):
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
    m_id = path if path else check_md5(sbml)
    sbml_dir = dirname(abspath(sbml))
    directory = os.path.join(sbml_dir, m_id)
    if not os.path.exists(directory):
        os.makedirs(directory)
    lib_path = os.path.join(directory, 'lib')
    if not os.path.exists(lib_path):
        copytree(get_lib(), lib_path)
    if verbose:
        logging.captureWarnings(True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S", filename=log_file)
        logging.captureWarnings(True)
    groups_sbml = os.path.join(directory, '%s_with_groups.xml' % model_id)
    gen_sbml = os.path.join(directory, '%s_generalized.xml' % model_id)
    if check_for_groups(sbml, SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS):
        if sbml != groups_sbml:
            if not libsbml.SBMLWriter().writeSBMLToFile(doc, groups_sbml):
                raise Exception("Could not write your model to %s" % groups_sbml)
    else:
        chebi = parse(get_chebi())
        if generalize:
            generalize_model(groups_sbml, gen_sbml, sbml, chebi, ub_chebi_ids=ub_ch_ids)
        else:
            gen_sbml = None
            ubiquitize_model(groups_sbml, sbml, chebi, ub_chebi_ids=ub_ch_ids)

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
    if gen_sbml:
        gen_document = reader.readSBML(gen_sbml)
        gen_model = gen_document.getModel()
    else:
        gen_model = False
    save_as_layout_sbml(groups_model, gen_model, groups_sbml, gen_sbml, n2lo, ub_sps)

    groups_sbgn = os.path.join(directory, '%s.sbgn' % model_id)
    gen_sbgn = os.path.join(directory, '%s_generalized.sbgn' % model_id)
    save_as_sbgn(n2lo, e2lo, groups_model, groups_sbgn)
    logging.info('   exported as SBGN %s' % groups_sbgn)
    if gen_model:
        save_as_sbgn(n2lo, e2lo, gen_model, gen_sbgn)

    serialize(directory=directory, m_dir_id=m_id, input_model=input_model, c_id2level2features=fc,
              c_id2out_c_id=c_id2out_c_id, groups_sbml=groups_sbml,
              main_url=MIMOZA_URL, scripts=JS_SCRIPTS, css=CSS_SCRIPTS, fav=MIMOZA_FAVICON)

