#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-
import logging
import os
import cgi
import cgitb
from os.path import dirname, abspath
import sys
import libsbml

from sbml_generalization.generalization.model_generalizer import EQUIVALENT_TERM_RELATIONSHIPS
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.onto.obo_ontology import parse
from sbml_generalization.onto.onto_getter import get_chebi
from mimoza.mimoza_path import *
from sbml_vis.html.html_t_generator import create_thanks_for_uploading_html, generate_generalization_finished_html


cgitb.enable()
# Windows needs stdio set for binary mode.
try:
    import msvcrt

    msvcrt.setmode(0, os.O_BINARY)  # stdin  = 0
    msvcrt.setmode(1, os.O_BINARY)  # stdout = 1
except ImportError:
    pass

form = cgi.FieldStorage()
sbml = form['sbml'].value
m_dir_id = form['dir'].value
scripts = '\n'.join(['<script src="../%s" type="text/javascript"></script>' % it for it in JS_SCRIPTS])

print '''Content-Type: text/html;charset=utf-8


        <html lang="en">

          <head>
             <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
             <meta http-equiv="Pragma" content="no-cache" />
             <meta http-equiv="Expires" content="0" />
             <link media="all" href="../%s" type="text/css" rel="stylesheet" />
             <link href="../%s" type="image/x-icon" rel="shortcut icon" />
             %s
             <title>Generalizing...</title>
          </head>

          <body>
          <p class="centre indent">Please, be patient while we are generalizing your model...</p>
          <img class="img-centre" src="../%s" id="img" />
          <div id="hidden" style="visibility:hidden;height:0px;">''' % (
    MIMOZA_CSS, MIMOZA_FAVICON, scripts, METHOD_ICON)

sys.stdout.flush()
url = '%s/%s/index.html' % (MIMOZA_URL, m_dir_id)
directory = os.path.join('..', 'html', m_dir_id)

log_file = os.path.join(directory, 'log.log')
logging.basicConfig(level=logging.INFO, format='%(message)s', filename=log_file)

try:
    logging.info('calling model_generalisation library')
    reader = libsbml.SBMLReader()
    input_document = reader.readSBML(sbml)
    input_model = input_document.getModel()
    m_id = input_model.getId()

    sbml_directory = dirname(abspath(sbml))
    groups_sbml = os.path.join(sbml_directory, '%s_with_groups.xml' % m_id)

    if not os.path.exists(groups_sbml):
        chebi = parse(get_chebi(), EQUIVALENT_TERM_RELATIONSHIPS | {'has_role'})
        gen_sbml = os.path.join(sbml_directory, '%s_generalized.xml' % m_id)
        r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps = generalize_model(groups_sbml, gen_sbml, sbml, chebi
                                                                              )
    create_thanks_for_uploading_html(m_id, input_model.getName(), os.path.join('..', 'html'), m_dir_id,
                                     MIMOZA_URL, 'comp.html', PROGRESS_ICON, generate_generalization_finished_html)

except Exception as e:
    logging.info(e.message)
    url = MIMOZA_ERROR_URL

sys.stdout.flush()

print '''</div>
          </body>
          <script type="text/javascript">
                window.location = "%s"
          </script>
        </html>''' % url
sys.stdout.flush()