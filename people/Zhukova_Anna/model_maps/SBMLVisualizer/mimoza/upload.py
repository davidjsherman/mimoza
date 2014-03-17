#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-

import cgi
import os
import cgitb
from libsbml import SBMLReader, writeSBMLToFile
from modules.html_generator import create_thanks_for_uploading_html, generate_redirecting_html, generate_error_html, \
	generate_contact, generate_exists_html
import base64
from mimoza.mimoza import *

ALREADY_EXISTS = 1
OK = 0
NOT_MODEL = 2

cgitb.enable()

# Windows needs stdio set for binary mode.
try:
	import msvcrt

	msvcrt.setmode(0, os.O_BINARY)  # stdin  = 0
	msvcrt.setmode(1, os.O_BINARY)  # stdout = 1
except ImportError:
	pass


# Generator to buffer file chunks
def file_buffer(f, chunk_size=10000):
	while True:
		chunk = f.read(chunk_size)
		if not chunk:
			break
		yield chunk


def upload_file():
	form = cgi.FieldStorage()
	# A nested FieldStorage instance holds the file
	file_item = form['file_input']
	# Test if the file was uploaded
	if file_item.filename:
		# strip leading path from file name to avoid directory traversal attacks
		file_name = os.path.basename(file_item.filename)
		safe_fn = base64.urlsafe_b64encode(file_name)
		sfn = "%s" % safe_fn
		i = 0
		while os.path.exists("../uploads/%s" % sfn):
			sfn = '%s_%d' % (safe_fn, i)
			i += 1
		f_path = '../uploads/%s' % sfn
		f = open(f_path, 'wb', 10000)
		# Read the file in chunks
		for chunk in file_buffer(file_item.file):
			f.write(chunk)
		f.close()
		return process_file(f_path)
	else:
		return NOT_MODEL, None


def process_file(sbml_file):
	reader = SBMLReader()
	doc = reader.readSBML(sbml_file)
	model = doc.getModel()
	if not model:
		return NOT_MODEL, None
	model_id = model.getId()
	if not model_id:
		sbml_name = os.path.splitext(os.path.basename(sbml_file))[0]
		model.setId(sbml_name)
		model_id = sbml_name

	m_id = "%s" % model_id
	i = 0
	existing_model = None
	while os.path.exists('../html/%s/' % m_id):
		if os.path.exists('../html/%s/comp.html' % m_id):
			existing_model = m_id
		# return ALREADY_EXISTS, (model_id, sbml_file)
		m_id = '%s_%d' % (model_id, i)
		i += 1
	directory = '../html/%s/' % m_id
	os.makedirs(directory)

	new_sbml_file = '%s%s.xml' % (directory, model_id)
	if sbml_file != new_sbml_file:
		if not writeSBMLToFile(doc, new_sbml_file):
			return NOT_MODEL, None
		# copyfile(sbml_file, new_sbml_file)
		os.remove(sbml_file)

	return (ALREADY_EXISTS, (model_id, m_id, existing_model)) if existing_model else (
		OK, (model_id, model.getName(), m_id))


result, args = upload_file()
if OK == result:
	(m_id, m_name, m_dir_id) = args
	create_thanks_for_uploading_html(m_id, m_name, '../html/', m_dir_id, MIMOZA_URL, 'comp.html', MIMOZA_CSS,
	                                   MIMOZA_FAVICON, PROGRESS_ICON)
	existing_m_url = '%s/%s/index.html' % (MIMOZA_URL, m_dir_id)
	print generate_redirecting_html(existing_m_url, MIMOZA_CSS, MIMOZA_FAVICON)
elif NOT_MODEL == result:
	print generate_error_html(MIMOZA_CSS, MIMOZA_FAVICON, 'Upload Error', 'Is it really in SBML?',
	                    'Your file does not seem to contain a model in <a href="%s" target="_blank">SBML</a> format.</p>' % SBML_ORG,
	                    '''Please, check you file and <a href="%s">try again</a>.
	                           <br>Or contact %s to complain about this problem.''' % (MIMOZA_URL, generate_contact(CONTACT_EMAIL)))
elif ALREADY_EXISTS == result:
	model_id, m_dir_id, existing_m_dir_id = args

	existing_m_url = '%s/%s/comp.html' % (MIMOZA_URL, existing_m_dir_id)
	url = '%s/%s/comp.html' % (MIMOZA_URL, m_dir_id)
	sbml = '../html/%s/%s.xml' % (m_dir_id, model_id)
	print generate_exists_html(MIMOZA_CSS, MIMOZA_FAVICON, model_id, existing_m_url, url, sbml, m_dir_id, PROGRESS_ICON)


