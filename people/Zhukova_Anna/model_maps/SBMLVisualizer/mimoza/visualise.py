#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-
import cgi
import cgitb
import os
from libsbml import SBMLReader
from modules.html_generator import generate_redirecting_html, generate_generalization_error_html
from runner.tulip_helper import visualize_model
from mimoza.mimoza import *

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


try:
	reader = SBMLReader()
	doc = reader.readSBML(sbml)
	model = doc.getModel()
	model_id = model.getId()
	url = '%s/%s/comp.html' % (MIMOZA_URL, m_dir_id)
	if not os.path.exists('../html/%s/comp.html' % m_dir_id):
		visualize_model('../html/', m_dir_id, MIMOZA_URL, 'comp.html', sbml, JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON, TILE, True, '../uploads/log.log')
	print generate_redirecting_html(url, MIMOZA_CSS, MIMOZA_FAVICON)
except Exception as e:
	print generate_generalization_error_html(MIMOZA_URL, MIMOZA_CSS, MIMOZA_FAVICON, e.message, CONTACT_EMAIL)
except:
	print generate_generalization_error_html(MIMOZA_URL, MIMOZA_CSS, MIMOZA_FAVICON, '', CONTACT_EMAIL)
