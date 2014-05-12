#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-

import cgi
import hashlib
import logging
import os
import cgitb
from tulip import tlp
from libsbml import SBMLReader, writeSBMLToFile
import sys
from modules.html_generator import create_thanks_for_uploading_html, create_thanks_for_uploading_generalized_html
from sbml_generalization.utils.compartment_positioner import get_comp2go, sort_comps
from sbml_generalization.utils.obo_ontology import parse, get_chebi, get_go, Term
from sbml_generalization.generalization.reaction_filters import getGeneAssociation
import base64
from mimoza.mimoza import *
from runner.mod_gen_helper import process_generalized_model

ALREADY_EXISTS = 1
OK = 0
NOT_MODEL = 2
ALREADY_GENERALIZED = 3

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


def check_md5(file_name):
    with open(file_name) as file_to_check:
        # read contents of the file
        data = file_to_check.read()
        # pipe contents of the file through
        return hashlib.md5(data).hexdigest()

verbose = True

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

    m_id = check_md5(sbml_file) #"%s" % model_id
    directory = '../html/%s/' % m_id
    if os.path.exists(directory):
        if os.path.exists('%sindex.html' % directory):
            return (ALREADY_EXISTS, (model_id, m_id))
    else:
        os.makedirs(directory)




    log_file = None
    try:
        log_file = '%s/log.log' % directory
        with open(log_file, "w+"):
            pass
    except:
        pass
    logging.basicConfig(level=logging.INFO, filename=log_file)

    chebi = parse(get_chebi())

    # groups_sbml = new_sbml_file
    r_id2ch_id, r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps = process_generalized_model(chebi, model, sbml_file)
    if r_id2g_id or ub_sps:
        new_sbml_file = '%s%s_with_groups.xml' % (directory, model_id)
        if sbml_file != new_sbml_file:
            if not writeSBMLToFile(doc, new_sbml_file):
                return NOT_MODEL, None
            os.remove(sbml_file)
        return ALREADY_GENERALIZED, (model_id, model.getName(), m_id)

    new_sbml_file = '%s%s.xml' % (directory, model_id)
    if sbml_file != new_sbml_file:
        if not writeSBMLToFile(doc, new_sbml_file):
            return NOT_MODEL, None
        os.remove(sbml_file)
    return OK, (model_id, model.getName(), m_id)

result, args = upload_file()

scripts = '\n'.join(['<script src="%s" type="text/javascript"></script>' % it for it in JS_SCRIPTS])
print '''Content-Type: text/html;charset=utf-8


        <html lang="en">

          <head>
            <link media="all" href="%s" type="text/css" rel="stylesheet" />
            <link href="%s" type="image/x-icon" rel="shortcut icon" />
            %s
            <title>Checking...</title>
          </head>

          <body>
          <p class="centre indent">Please, be patient while we are checking your model...</p>
          <div class="centre margin" id="visualize_div">
            <img class="centre" src="%s" id="img" />
          </div>
          <div id="hidden" style="visibility:hidden;height:0px;">''' % (MIMOZA_CSS, MIMOZA_FAVICON, scripts, LOADER_ICON)

url = MIMOZA_UPLOAD_ERROR_URL
if OK == result:
    (m_id, m_name, m_dir_id) = args
    create_thanks_for_uploading_html(m_id, m_name, '../html/', m_dir_id, MIMOZA_URL, 'comp.html', MIMOZA_CSS, JS_SCRIPTS,
                                       MIMOZA_FAVICON, PROGRESS_ICON)
    # existing_m_url = '%s/%s/index.html' % (MIMOZA_URL, m_dir_id)
    url = '%s/%s/index.html' % (MIMOZA_URL, m_dir_id)
    # print generate_redirecting_html(existing_m_url, MIMOZA_CSS, MIMOZA_FAVICON)
# elif NOT_MODEL == result:
# 	pass
    # print generate_error_html(MIMOZA_CSS, MIMOZA_FAVICON, 'Upload Error', 'Is it really in SBML?',
    #                     'Your file does not seem to contain a model in <a href="%s" target="_blank">SBML</a> format.</p>' % SBML_ORG,
    #                     '''Please, check you file and <a href="%s">try again</a>.
    #                            <br>Or contact %s to complain about this problem.''' % (MIMOZA_URL, generate_contact(CONTACT_EMAIL)))
elif ALREADY_EXISTS == result:
    # model_id, m_dir_id, existing_m_dir_id = args
    #
    # # existing_m_url = '%s/%s/comp.html' % (MIMOZA_URL, existing_m_dir_id)
    # # url = '%s/%s/comp.html' % (MIMOZA_URL, m_dir_id)
    # # sbml = '../html/%s/%s.xml' % (m_dir_id, model_id)
    #
    # create_exists_html(model_id, existing_m_dir_id, '../html/', m_dir_id, MIMOZA_URL, 'comp.html', MIMOZA_CSS, JS_SCRIPTS,
    #                                    MIMOZA_FAVICON, PROGRESS_ICON)
    # url = '%s/%s/index.html' % (MIMOZA_URL, m_dir_id)
    # # print generate_exists_html(MIMOZA_CSS, JS_SCRIPTS, MIMOZA_FAVICON, model_id, existing_m_url, url, sbml, m_dir_id, PROGRESS_ICON)

    model_id, m_dir_id = args
    url = '%s/%s/index.html' % (MIMOZA_URL, m_dir_id)
elif ALREADY_GENERALIZED == result:
    (m_id, m_name, m_dir_id) = args
    create_thanks_for_uploading_generalized_html(m_id, m_name, '../html/', m_dir_id, MIMOZA_URL, 'comp.html', MIMOZA_CSS, JS_SCRIPTS,
                                       MIMOZA_FAVICON, PROGRESS_ICON)
    # existing_m_url = '%s/%s/index.html' % (MIMOZA_URL, m_dir_id)
    url = '%s/%s/index.html' % (MIMOZA_URL, m_dir_id)


print '''</div>
          </body>
          <script type="text/javascript">
                window.location = "%s"
          </script>
        </html>''' % url
sys.stdout.flush()

