#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-

import os
import cgi
import cgitb
from instant import check_and_set_swig_binary, inline

from libsbml import SBMLReader
import sys
from mimoza.mimoza import *
from modules.c_stdout_redirect import RedirectDescriptor
from modules.html_generator import generate_redirecting_html, generate_generalization_error_html
from runner.tulip_helper import visualize_model

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

    reader = SBMLReader()
    doc = reader.readSBML(sbml)
    model = doc.getModel()
    model_id = model.getId()
    url = '%s/%s/comp.html' % (MIMOZA_URL, m_dir_id)

    if not os.path.exists('../html/%s/comp.html' % m_dir_id):
        url = visualize_model('../html/', m_dir_id, MIMOZA_URL, 'comp.html', sbml, JS_SCRIPTS, CSS_SCRIPTS, MIMOZA_FAVICON, TILE, True)

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
except:
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