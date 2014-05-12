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
scripts = '\n'.join(['<script src="%s" type="text/javascript"></script>' % it for it in JS_SCRIPTS])

print '''Content-Type: text/html;charset=utf-8


        <html lang="en">

          <head>
            <link media="all" href="%s" type="text/css" rel="stylesheet" />
            <link href="%s" type="image/x-icon" rel="shortcut icon" />
            %s
            <title>Visualizing...</title>
          </head>

          <body>
          <p class="centre indent">Please, be patient while we are visualising your model...</p>
          <div class="centre margin" id="visualize_div">
            <img class="centre" src="%s" id="img" />
          </div>
          <div id="hidden" style="visibility:hidden;height:0px;">''' % (MIMOZA_CSS, MIMOZA_FAVICON, scripts, PROGRESS_ICON)

sys.stdout.flush()

temp = os.dup(sys.stdout.fileno())
try:
    # this is a hack to prevent Tulip from printing stuff and producing 500
    # stdout = os.fdopen(os.dup(sys.stdout.fileno()), 'w')
    # stderr = os.fdopen(os.dup(sys.stderr.fileno()), 'w')
    # check_and_set_swig_binary(binary="swig", path="/usr/local/bin/")
    # args = {'signature': 'instant_module_4f54380a7a9b9ae759599376130bf4b4be6f10a6', 'cache_dir': '/var/www/uploads/.instant/cache'}
    # redirect = inline("""
    # void redirect(void) {
    #     freopen("/var/www/uploads/log.log", "w", stdout);
    #     freopen("/var/www/uploads/log.log", "w", stderr);
    # }
    # """, **args)
    # redirect()

    # reader = SBMLReader()
    # doc = reader.readSBML(sbml)
    # model = doc.getModel()
    # model_id = model.getId()
    url = '%s/%s/comp.html' % (MIMOZA_URL, m_dir_id)

    if not os.path.exists('../html/%s/comp.html' % m_dir_id):
        chebi = parse(get_chebi())
        reader = SBMLReader()
        input_document = reader.readSBML(groups_sbml)
        input_model = input_document.getModel()

        # sbml -> tulip graph
        log(True, 'sbml -> tlp')
        graph = tlp.newGraph()
        graph, onto, name2id_go = import_sbml(graph, input_model, groups_sbml, True, log_file)

        url = visualize_model(directory, m_dir_id, input_model, graph, name2id_go, groups_sbml, url, MIMOZA_URL, JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON, True)

    # redirect_back = inline("""
    # void redirect(void) {
    #     fclose(stdout);
    #     fclose(stderr);
    # }
    # """, **args)
    # redirect_back()

    # print generate_redirecting_html(url, MIMOZA_CSS, MIMOZA_FAVICON)
# except Exception as e:
#     print generate_generalization_error_html(MIMOZA_URL, MIMOZA_CSS, MIMOZA_FAVICON, e.message, CONTACT_EMAIL)
except Exception as e:
    log(True, e.message)
    url = MIMOZA_ERROR_URL
    # print generate_generalization_error_html(MIMOZA_URL, MIMOZA_CSS, MIMOZA_FAVICON, '', CONTACT_EMAIL)

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