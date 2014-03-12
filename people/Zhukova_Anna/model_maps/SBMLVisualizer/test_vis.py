#!/usr/local/bin/python2.7
import cgi
import cgitb
import os
from libsbml import SBMLReader, writeSBMLToFile
from runner.tulip_helper import visualize_model

MIMOZA_URL = 'http://mimoza.bordeaux.inria.fr'

MIMOZA_SHORTCUT_ICON = '<link href=\"%s/lib/modelmap/fav.ico\" type=\"image/x-icon\" rel=\"shortcut icon\" />' % MIMOZA_URL

MIMOZA_STYLE = '<link media="all" href="%s/lib/modelmap/modelmap.css" type="text/css" rel="stylesheet" />' % MIMOZA_URL

TILE = '%s/lib/modelmap/white512.jpg' % MIMOZA_URL

FAVIICON = '%s/lib/modelmap/fav.ico' % MIMOZA_URL

JS_SCRIPTS = [('%s/lib/leaflet/leaflet.js' % MIMOZA_URL),
              ('%s/lib/leaflet_label/leaflet.label.js' % MIMOZA_URL),
              'http://code.jquery.com/jquery-2.0.3.min.js', 'http://code.jquery.com/ui/1.10.4/jquery-ui.js',
              ('%s/lib/modelmap/maptools.js' % MIMOZA_URL)]

CSS_SCRIPTS = [('%s/lib/modelmap/modelmap.css' % MIMOZA_URL),
               ('%s/lib/leaflet/leaflet.css' % MIMOZA_URL),
               ('%s/lib/leaflet_label/leaflet.label.css' % MIMOZA_URL),
               'http://code.jquery.com/ui/1.10.4/themes/smoothness/jquery-ui.css']

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
	redirectURL = '%s/%s/comp.html' % (MIMOZA_URL, m_dir_id)
	if not os.path.exists('../html/%s/comp.html' % m_dir_id):
		visualize_model('../html/',  m_dir_id, MIMOZA_URL, 'comp.html', sbml, JS_SCRIPTS, CSS_SCRIPTS, FAVIICON, TILE, False)
	print 'Content-Type: text/html'
	print 'Location: %s' % redirectURL
	print # HTTP says you have to have a blank line between headers and content
	print '<html lang="en">'

	print '  <head>'
	print MIMOZA_STYLE
	print MIMOZA_SHORTCUT_ICON
	print '    <meta http-equiv="refresh" content="0;url=%s" />' % redirectURL
	print '    <title>Redirecting...</title>'
	print '  </head>'

	print '  <body>'
	print '    Redirecting to <a href="%s">%s</a>' % (redirectURL, redirectURL)
	print '  </body>'

	print '</html>'

except Exception as e:
	print 'Content-Type: text/html'
	print # HTTP says you have to have a blank line between headers and content
	print '<html lang="en">'

	print '  <head>'
	print MIMOZA_STYLE
	print MIMOZA_SHORTCUT_ICON
	print '    <title>Error</title>'
	print '  </head>'

	print '  <body>'
	print '    <h1 class="capitalize">Oops, something went wrong...</h1>'
	print '    <div class="indent" id="all">'
	print '      <p>We tried hard, but did not manage to visualize your model. Sorry!</p>'
	print '      <p>The reason is %s</p>' % e.message
	print '      <p>May be, try to <a href="%s">visualize another one</a>?</p>' % MIMOZA_URL
	print '    </div>'
	print '  </body>'

	print '</html>'
except:
	print 'Content-Type: text/html'
	print # HTTP says you have to have a blank line between headers and content
	print '<html lang="en">'

	print '  <head>'
	print MIMOZA_STYLE
	print MIMOZA_SHORTCUT_ICON
	print '    <title>Error</title>'
	print '  </head>'

	print '  <body>'
	print '    <h1 class="capitalize">Oops, something went wrong...</h1>'
	print '    <div class="indent" id="all">'
	print '      <p>We tried hard, but did not manage to visualize your model. Sorry!</p>'
	print '      <p>May be, try to <a href="%s">visualize another one</a>?</p>' % MIMOZA_URL
	print '    </div>'
	print '  </body>'

	print '</html>'
