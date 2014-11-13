#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-

import logging
import os
import cgi
import cgitb
import sys

from libsbml import SBMLReader
from sbml_generalization.generalization.sbml_helper import parse_layout_sbml, LoPlError, save_as_layout_sbml

from sbml_vis.file.serializer import serialize
from sbml_vis.converter.sbml2tlp import import_sbml
from mimoza.mimoza import *
from sbml_vis.converter.tulip_graph2geojson import graph2geojson

from sbml_generalization.utils.logger import log
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
gen_sbml = form['gen_sbml'].value
m_dir_id = form['dir'].value
directory = '../html/%s/' % m_dir_id
log_file = '%s/log.log' % directory
logging.basicConfig(level=logging.INFO, filename=log_file)
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
            <title>Visualizing...</title>
          </head>

          <body>
          <p class="centre indent">We are visualizing your model now...</p>
          <img class="img-centre" src="../%s" id="img" />
          <div id="hidden" style="visibility:hidden;height:0px;">''' % (
	MIMOZA_CSS, MIMOZA_FAVICON, scripts, PROGRESS_ICON)

sys.stdout.flush()

temp = os.dup(sys.stdout.fileno())
try:
	url = '/%s/comp.html' % m_dir_id

	if not os.path.exists('../html/%s/comp.html' % m_dir_id):
		chebi = parse(get_chebi())
		reader = SBMLReader()
		input_document = reader.readSBML(groups_sbml)
		input_model = input_document.getModel()

		# sbml -> tulip graph
		log(True, 'sbml -> tlp')
		graph, c_id2info, c_id2outs, chebi, ub_sps = import_sbml(input_model, groups_sbml, True)

		try:
			n2xy = parse_layout_sbml(groups_sbml)
		except LoPlError:
			n2xy = None

		fc, (n2lo, (d_w, d_h)) = graph2geojson(c_id2info, c_id2outs, graph, True, chebi, n2xy)

		if not n2xy or gen_sbml:
			groups_document = reader.readSBML(groups_sbml)
			groups_model = groups_document.getModel()
			gen_document = reader.readSBML(gen_sbml)
			gen_model = gen_document.getModel()
			save_as_layout_sbml(groups_model, gen_model, groups_sbml, gen_sbml, n2lo, (d_w, d_h), ub_sps, True)

		serialize(directory, m_dir_id, input_model, fc, groups_sbml, MIMOZA_URL, JS_SCRIPTS, CSS_SCRIPTS,
		          MIMOZA_FAVICON, True)

except Exception as e:
	log(True, e.message)
	url = MIMOZA_ERROR_URL

sys.stdout.flush()

print '''</div>
          </body>
          <script type="text/javascript">
                window.location = "%s"
          </script>
        </html>''' % url
sys.stdout.flush()