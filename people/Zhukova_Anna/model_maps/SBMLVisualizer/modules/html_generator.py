__author__ = 'anna'
import markup


def normalize(organelle):
	return organelle.lower().replace(' ', '_')


def denormalize(organelle):
	return organelle.replace('_', ' ')


def add_header(model_id, model_name, page):
	""" <h1 class="capitalize">
			<span id='comp'>Compartments</span> of <a href="http://www.ebi.ac.uk/biomodels-main/model_id">model_name</a>
		</h1> """
	page.h1(class_='capitalize')
	page.span('Compartments', id='comp')
	page.span('&nbsp;of&nbsp;')
	page.a(model_name, href='http://www.ebi.ac.uk/biomodels-main/{0}'.format(model_id))
	page.h1.close()


def add_compartment_menu(url, organelles, page):
	page.ul(class_='menu margin centre')
	for organelle in organelles:
		page.li()
		page.a(denormalize(organelle), href='%s?name=%s' % (url, normalize(organelle)))
		page.li.close()
	page.ul.close()


def add_download_link(groups_sbml, page):
	if groups_sbml:
		page.div(class_='margin', id='download')
		page.p('Download the <a href=%s download>generalised model</a>.' % groups_sbml)
		page.div.close()


def add_search(page):
	""" <div>
			<form name="search_form" onclick="search(map, name2popup);">
				<label><input id="tags" type="text" name="search_input"></label>
				<input type="button" value="Search" >
			</form>
		</div> """
	page.div(class_='margin', id='search')
	page.form(name="search_form", onclick="search(map, name2popup);")
	page.label('  ')
	page.input(id="tags", type="text", name="search_input")
	page.label.close()
	page.input(type="button", value="Search")
	page.form.close()
	page.div.close()


def add_explanations(page):
	""" <div id="explanations" class="margin"><p>
			<span class="pant">Zoom in</span> to see the more detailed model.
			<span class="pant">Zoom out</span> to see the generalized model.
			<span class="pant">Click</span> on species and reactions to see their annotations.
		</p></div> """
	page.div(class_='margin', id='explanations')
	page.p()
	page.span('Zoom in', class_='pant')
	page.span(' to see the detailed model. ')
	page.span('Zoom out', class_='pant')
	page.span(' to see the generalized model. ')
	page.span('Click', class_='pant')
	page.span(' on elements to see their annotations. ')
	page.p.close()
	page.div.close()


def add_map(page):
	""" <div class="margin" id="map" style="width: 1024px; height: 1024px"></div> """
	page.div('', class_='margin', id='map', style="width: 1024px; height: 1024px")


def add_model_description(model, page):
	model_description = model.getNotes()
	if model_description:
		page.p(model_description.toXMLString(), class_='margin just', id='descr')


def add_js(default_organelle, org2scripts, page, tile):
	page.script('var comp2geojson = %s; var compartment = "%s";' % (org2scripts, normalize(default_organelle)) + '''
		var comp = gup('name');
		if (comp) {
			compartment = comp;
		}
		if (compartment) {
			var span = document.getElementById('comp');
			while (span.firstChild) {
				span.removeChild(span.firstChild);
			}
			span.appendChild(document.createTextNode(compartment.replace('_', ' ')));

			map = initializeMap(5);
			var name2popup = {};
			getGeoJson(map, comp2geojson[compartment], name2popup);


			L.tileLayer("''' + tile + '''", {
				continuousWorld: true,
				noWrap: true,
				tileSize: 512,
				maxZoom: 5,
				minZoom: 0,
				tms: true,
				updateWhenIdle: true,
				reuseTiles: true
			}).addTo(map);
		} '''
	)


def generate_html(model, directory, url, organelles, groups_sbml_url, scripts, css, fav, tile):
	page = markup.page()
	if not scripts:
		scripts = []
	default_organelle = normalize(organelles[0]) if organelles else ''
	org2scripts = '{'
	for organelle in organelles:
		organelle = normalize(organelle)
		scripts += ['./{0}_f.json'.format(organelle), './{0}.json'.format(organelle)]
		org2scripts += "'{0}': [gjsn__{0}, gjsn__{0}_full],".format(organelle)
	org2scripts += '}'

	if not css:
		css = ['http://code.jquery.com/ui/1.10.4/themes/smoothness/jquery-ui.css']
	else:
		css.append('http://code.jquery.com/ui/1.10.4/themes/smoothness/jquery-ui.css')

	model_id = model.getId()
	model_name = model.getName()
	if not model_name:
		model_name = model_id
	page.init(title=model_name, css=css, script=scripts, fav=fav)

	add_header(model_id, model_name, page)

	page.div(class_='centre', id='all')
	add_compartment_menu(url, organelles, page)

	add_download_link(groups_sbml_url, page)

	add_explanations(page)

	add_search(page)

	add_map(page)

	add_model_description(model, page)

	page.div.close()

	add_js(default_organelle, org2scripts, page, tile)

	with open('%s/comp.html' % directory, 'w+') as f:
		f.write(str(page))
	generate_redirecting_index(url, directory)


def generate_redirecting_index(url, directory):
	page = '''Content-Type: text/html
	Location: %s

	<html lang="en">
	<head>
	<link media="all" href="http://mimoza.bordeaux.inria.fr/lib/modelmap/modelmap.css" type="text/css" rel="stylesheet" />
	<link href="http://mimoza.bordeaux.inria.fr/lib/modelmap/fav.ico" type="image/x-icon" rel="shortcut icon" />
	<meta http-equiv="refresh" content="0;url=%s" />
	<title>You are going to be redirected</title>
	</head>
	<body>
	Redirecting... <a href="%s">Click here if you are not redirected</a>
	</body>
	</html>''' % (url, url, url)
	with open('%s/index.html' % directory, 'w+') as f:
		f.write(page)


def generate_simple_html(model, html_file, groups_sbml, scripts, css, fav):
	page = markup.page()
	model_id = model.getId()
	model_name = model.getName()
	if not model_name:
		model_name = model_id
	page.init(title=model_name, css=css if css else [], script=scripts if scripts else [], fav=fav)

	add_header(model_id, model_name, page)

	add_download_link(groups_sbml, page)

	add_model_description(model, page)

	page.div.close()

	with open(html_file, 'w+') as f:
		f.write(str(page))


def generate_thanks_for_uploading_html(m_id, m_name, directory_prefix, m_dir_id, url, url_end, css, fav, img):
	directory = '%s/%s' % (directory_prefix, m_dir_id)
	page = markup.page()
	if not m_name:
		m_name = m_id
	if not css:
		css = ['http://code.jquery.com/ui/1.10.4/themes/smoothness/jquery-ui.css']
	else:
		css.append('http://code.jquery.com/ui/1.10.4/themes/smoothness/jquery-ui.css')

	page.init(title='%s uploaded' % m_name, css=css, fav=fav)

	page.h1("Uploaded, time to visualise!", class_='capitalize')

	page.div(class_='indent', id='all')
	url = '%s/%s/%s' % (url, m_dir_id, url_end)
	page.p(
		'Thank you for uploading your model <span class="pant">%s</span>!' % m_name)
	page.p('Now let\'s visualise it. It might take some time (up to 2-4 hours for genome-scale models), so, please, be patient and do not lose hope :)')
	page.p('When the visualisation is done, it will become available at <a href="%s">%s</a>.' % (url, url))
	page.p('To start the visualisation press the button below.')

	sbml = '%s/%s.xml' % (directory, m_id)

	page.div(class_='centre margin', id='visualize_div')
	page.form(name="input_form", enctype="multipart/form-data", action="/cgi-bin/visualise.py", method="POST")
	page.input(type="hidden", name="sbml", value=sbml)
	page.input(type="hidden", name="dir", value=m_dir_id)
	page.input(class_="ui-button", id="bb", type="submit", value="Visualise", onclick="progress()")
	page.form.close()
	page.div.close()

	# page.div(class_='centre margin', id='visualize_div')
	# page.img(id="img", src=fav, style="visibility:hidden")
	# page.div.close()



	page.div.close()

	# page.script('''function progress() {
	# 	document.getElementById("img").style.visibility="visible";
	# }''')

	with open('%s/index.html' % directory, 'w+') as f:
		f.write(str(page))