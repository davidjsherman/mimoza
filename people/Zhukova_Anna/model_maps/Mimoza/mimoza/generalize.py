#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-
import logging
import os
import cgi
import cgitb
from os.path import dirname, abspath
import sys

from libsbml import SBMLReader

from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.utils.obo_ontology import parse, get_chebi
from sbml_generalization.utils.logger import log

from mimoza.mimoza import *
from sbml_vis.html.html_generator import create_thanks_for_uploading_generalized_html, generate_generalized_html


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
directory = '../html/%s/' % m_dir_id

log_file = '%s/log.log' % directory
logging.basicConfig(level=logging.INFO, format='%(message)s', filename=log_file)

# temp = os.dup(sys.stdout.fileno())
try:
	log(True, 'calling model_generalisation library')
	reader = SBMLReader()
	input_document = reader.readSBML(sbml)
	input_model = input_document.getModel()
	m_id = input_model.getId()

	sbml_directory = dirname(abspath(sbml))
	groups_sbml = "%s/%s_with_groups.xml" % (sbml_directory, m_id)

	if not os.path.exists(groups_sbml):
		chebi = parse(get_chebi())
		gen_sbml = "%s/%s_generalized.xml" % (sbml_directory, m_id)
		r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps = generalize_model(groups_sbml, gen_sbml, sbml, chebi, verbose=True)
	create_thanks_for_uploading_generalized_html(m_id, input_model.getName(), '../html/', m_dir_id,
	                                             MIMOZA_URL, 'comp.html', MIMOZA_CSS, JS_SCRIPTS,
	                                             MIMOZA_FAVICON, PROGRESS_ICON, generate_generalized_html)

except Exception as e:
	log(True, e.message)
	url = MIMOZA_ERROR_URL

sys.stdout.flush()
# os.dup2(temp, 2)
# sys.stdout = os.fdopen(2, 'w')

print '''</div>
          </body>
          <script type="text/javascript">
                window.location = "%s"
          </script>
        </html>''' % url
sys.stdout.flush()