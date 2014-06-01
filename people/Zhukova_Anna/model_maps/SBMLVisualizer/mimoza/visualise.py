#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-
import logging

import os
import cgi
import cgitb
from tulip import tlp
from sbml_generalization.utils.logger import log

from libsbml import SBMLReader
import sys
from mimoza.mimoza import *
from modules.sbml2tlp import import_sbml
from runner.tulip_helper import visualize_model
from sbml_generalization.utils.obo_ontology import parse, get_chebi

cgitb.enable()
# Windows needs stdio set for binary mode.
try:
    import msvcrt
    msvcrt.setmode(0, os.O_BINARY)  # stdin  = 0
    msvcrt.setmode(1, os.O_BINARY)  # stdout = 1
except ImportError:
    pass

form = cgi.FieldStorage()
groups_sbml = form['sbml'].value
m_dir_id = form['dir'].value
directory = '../html/%s/' % m_dir_id
log_file = '%s/log.log' % directory
logging.basicConfig(level=logging.INFO, filename=log_file)
scripts = '\n'.join(['<script src="../%s" type="text/javascript"></script>' % it for it in JS_SCRIPTS])

print '''Content-Type: text/html;charset=utf-8


        <html lang="en">

          <head>
            <link media="all" href="../%s" type="text/css" rel="stylesheet" />
            <link href="../%s" type="image/x-icon" rel="shortcut icon" />
            %s
            <title>Visualizing...</title>
          </head>

          <body>
          <p class="centre indent">We are visualising your model now...</p>
          <img class="img-centre" src="../%s" id="img" />
          <div id="hidden" style="visibility:hidden;height:0px;">''' % (MIMOZA_CSS, MIMOZA_FAVICON, scripts, PROGRESS_ICON)

sys.stdout.flush()

temp = os.dup(sys.stdout.fileno())
try:
    url = '%s/%s/comp.html' % (MIMOZA_URL, m_dir_id)

    if not os.path.exists('../html/%s/comp.html' % m_dir_id):
        chebi = parse(get_chebi())
        reader = SBMLReader()
        input_document = reader.readSBML(groups_sbml)
        input_model = input_document.getModel()

        # sbml -> tulip graph
        log(True, 'sbml -> tlp')
        graph = tlp.newGraph()
        # graph, onto, name2id_go = import_sbml(graph, input_model, groups_sbml, True, log_file)
        graph, onto, c_id2info = import_sbml(graph, input_model, groups_sbml, True, log_file)

        # url = visualize_model(directory, m_dir_id, input_model, graph, name2id_go, groups_sbml, url, MIMOZA_URL, JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON, True)
        url = visualize_model(directory, m_dir_id, input_model, graph, c_id2info, groups_sbml, url, MIMOZA_URL, JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON, True)

except Exception as e:
    log(True, e.message)
    url = MIMOZA_ERROR_URL

sys.stdout.flush()
os.dup2(temp, 2)
sys.stdout = os.fdopen(2, 'w')

print '''</div>
          </body>
          <script type="text/javascript">
                window.location = "%s"
          </script>
        </html>''' % url
sys.stdout.flush()