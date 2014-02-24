#!/usr/local/bin/python2.7
import cgi
import os
import cgitb
from runner.tulip_helper import visualize_model

MIMOZA_URL = 'http://mimoza.bordeaux.inria.fr'

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
import base64

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
	global form, file_item, fn, safe_fn, f_path, f, chunk, m_id, message
	form = cgi.FieldStorage()
	# A nested FieldStorage instance holds the file
	file_item = form['file_input']
	# Test if the file was uploaded
	if file_item.filename:
		# strip leading path from file name to avoid directory traversal attacks
		fn = os.path.basename(file_item.filename)
		safe_fn = base64.urlsafe_b64encode(fn)
		f_path = '../uploads/' + safe_fn
		f = open(f_path, 'wb', 10000)
		# Read the file in chunks
		for chunk in file_buffer(file_item.file):
			f.write(chunk)
		f.close()
		return True, f_path
	else:
		return False, None


result, f_path = upload_file()
if result:
	redirectURL = visualize_model('../html/', MIMOZA_URL, 'comp.html', f_path, JS_SCRIPTS, CSS_SCRIPTS, FAVIICON, TILE, False)
	print 'Content-Type: text/html'
	print 'Location: %s' % redirectURL
	print  # HTTP says you have to have a blank line between headers and content
	print '<html>'
	print '  <head>'
	print '    <meta http-equiv="refresh" content="0;url=%s" />' % redirectURL
	print '    <title>You are going to be redirected</title>'
	print '  </head>'
	print '  <body>'
	print '    Redirecting... <a href="%s">Click here if you are not redirected</a>' % redirectURL
	print '  </body>'
	print '</html>'
else:
	print 'Content-Type: text/html'
	print  # HTTP says you have to have a blank line between headers and content
	print '<html>'
	print '  <head>'
	print '    <title>Upload Error</title>'
	print '  </head>'
	print '  <body>'
	print '     <p>Your file was not uploaded. Please, try again</p>'
	print '  </body>'
	print '</html>'

