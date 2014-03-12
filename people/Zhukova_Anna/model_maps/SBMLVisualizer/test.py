#!/usr/local/bin/python2.7
import cgi
import os
import cgitb
from libsbml import SBMLReader, writeSBMLToFile
from modules.html_generator import generate_thanks_for_uploading_html
import base64

MIMOZA_URL = 'http://mimoza.bordeaux.inria.fr'

MIMOZA_SHORTCUT_ICON = '<link href=\"%s/lib/modelmap/fav.ico\" type=\"image/x-icon\" rel=\"shortcut icon\" />' % MIMOZA_URL

MIMOZA_STYLE = '<link media="all" href="%s/lib/modelmap/modelmap.css" type="text/css" rel="stylesheet" />' % MIMOZA_URL

ALREADY_EXISTS = 1
OK = 0
NOT_MODEL = 2

TILE = '%s/lib/modelmap/white512.jpg' % MIMOZA_URL

FAV_ICON = '%s/lib/modelmap/fav.ico' % MIMOZA_URL

PROGRESS_ICON = '%s/lib/modelmap/ajax-loader.gif' % MIMOZA_URL

JS_SCRIPTS = [('%s/lib/leaflet/leaflet.js' % MIMOZA_URL), ('%s/lib/leaflet_label/leaflet.label.js' % MIMOZA_URL), 'http://code.jquery.com/jquery-2.0.3.min.js', 'http://code.jquery.com/ui/1.10.4/jquery-ui.js', ('%s/lib/modelmap/maptools.js' % MIMOZA_URL)]

CSS_SCRIPTS = [('%s/lib/modelmap/modelmap.css' % MIMOZA_URL), ('%s/lib/leaflet/leaflet.css' % MIMOZA_URL), ('%s/lib/leaflet_label/leaflet.label.css' % MIMOZA_URL), 'http://code.jquery.com/ui/1.10.4/themes/smoothness/jquery-ui.css']

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

	return (ALREADY_EXISTS, (model_id, m_id, existing_model)) if existing_model else (OK, (model_id, model.getName(), m_id))


result, args = upload_file()
if OK == result:
	(m_id, m_name, m_dir_id) = args
	generate_thanks_for_uploading_html(m_id, m_name, '../html/',  m_dir_id, MIMOZA_URL, 'comp.html', CSS_SCRIPTS, FAV_ICON, PROGRESS_ICON)
	existing_m_url = '%s/%s/index.html' % (MIMOZA_URL, m_dir_id)
	# redirectURL = visualize_model('../html/', MIMOZA_URL, 'comp.html', f_path, JS_SCRIPTS, CSS_SCRIPTS, FAVIICON, TILE, False)
	print 'Content-Type: text/html'
	print 'Location: %s' % existing_m_url
	print  # HTTP says you have to have a blank line between headers and content
	print '<html lang="en">'
	print '  <head>'
	print MIMOZA_STYLE
	print MIMOZA_SHORTCUT_ICON
	print '    <meta http-equiv="refresh" content="0;url=%s" />' % existing_m_url
	print '    <title>You are going to be redirected</title>'
	print '  </head>'
	print '  <body>'
	print '    Redirecting... <a href="%s">Click here if you are not redirected</a>' % existing_m_url
	print '  </body>'
	print '</html>'
elif NOT_MODEL == result:
	print 'Content-Type: text/html'
	print  # HTTP says you have to have a blank line between headers and content
	print '<html lang="en">'
	print '  <head>'
	print MIMOZA_STYLE
	print MIMOZA_SHORTCUT_ICON
	print '    <title>Upload error</title>'
	print '  </head>'
	print '  <body>'
	print '<h1 class="capitalize">Is it really in SBML?</h1>'

	print '<div class="indent" id="all">'
	print '<p>Your file does not seem to contain a model in <a href="%s" target="_blank">SBML</a> format.</p>' % "http://sbml.org"
	print '<p>Please, check you file and <a href="%s">try again</a>.</p>' % MIMOZA_URL
	print '</div>'
	print '  </body>'
	print '</html>'
elif ALREADY_EXISTS == result:
	model_id, m_dir_id, existing_m_dir_id = args

	existing_m_url = '%s/%s/comp.html' % (MIMOZA_URL, existing_m_dir_id)
	url = '%s/%s/comp.html' % (MIMOZA_URL, m_dir_id)
	sbml = '../html/%s/%s.xml' % (m_dir_id, model_id)
	print 'Content-Type: text/html'
	print  # HTTP says you have to have a blank line between headers and content
	print '<html lang="en">'
	print '  <head>'
	print MIMOZA_STYLE
	print MIMOZA_SHORTCUT_ICON
	print '    <title>%s exists</title>' % model_id
	print '  </head>'
	print '  <body>'
	print '<h1 class="capitalize">Already at Mimoza</h1>'

	print '<div class="indent" id="all">'

	print '<p>Thank you for uploading your model <span class="pant">%s</span>!</p>' % model_id
	print '<p>There is already <a href="%s" target="_blank">a processed model</a> with this identifier, check it out!</p>' % existing_m_url
	print '<p><span id="expl">If you prefer to carry on with your model instead, press the button below.</span> <br>After the visualisation is done, it will become available at <a href="%s">%s</a>. <br>It might take some time (up to 2-4 hours for genome-scale models), so, please, be patient and do not lose hope :)</p>' % (url, url)


	print '<div class="centre margin" id="visualize_div">'
	print '<form action="/cgi-bin/visualise.py" method="POST" name="input_form" enctype="multipart/form-data">'
	print '<input type="hidden" name="sbml" value="%s" />' % sbml
	print '<input type="hidden" name="dir" value="%s" />' % m_dir_id
	print '<input class="ui-button" type="submit" id="bb" value="Visualise" onclick="progress()"/>'
	print '</form>'
	print '</div>'

	print '<div class="centre margin" id="visualize_div">'
	print '<img src="%s" style="visibility:hidden" id="img" />' % PROGRESS_ICON
	print '</div>'

	print '</div>'
	print '''<script>function progress() {
		document.getElementById("img").style.visibility="visible";
		document.getElementById("visualize_div").style.visibility="hidden";
		var span = document.getElementById('expl');
		while (span.firstChild) {
			span.removeChild(span.firstChild);
		}
		span.appendChild(document.createTextNode("We are currently visualising your model..."));
	}</script>'''


	print '  </body>'
	print '</html>'

