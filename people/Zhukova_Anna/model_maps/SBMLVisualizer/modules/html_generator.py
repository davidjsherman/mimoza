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


def create_html(model, directory, url, organelles, groups_sbml_url, scripts, css, fav, tile):
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
	with open('%s/index.html' % directory, 'w+') as f:
		f.write(generate_redirecting_html(url, css[0] if css else '', fav))


def generate_redirecting_html(url, css, ico):
	return '''Content-Type: text/html;charset=utf-8


		Location: %s

		<html lang="en">

	        <head>
				<link media="all" href="%s" type="text/css" rel="stylesheet" />
				<link href="%s" type="image/x-icon" rel="shortcut icon" />
	            <meta http-equiv="refresh" content="0;url=%s" />
	            <title>Redirecting...</title>
	        </head>

	        <body>
	            <div class="indent" id="all">
	                <p>Redirecting to <a href="%s">%s</a></p>
		        </div>
	        </body>

		</html>''' % (url, css, ico, url, url, url)


def generate_generalization_error_html(url, css, ico, msg, contact):
	return generate_error_html(css, ico, 'Processing Error', 'Oops, something went wrong...',
	                           '''We tried hard, but did not manage to visualize your model. Sorry!
	                           <br>%s''' % ('The reason is: %s' % msg) if msg else '',
	                           '''May be, try to <a href="%s">visualize another one</a>?
	                           <br>Or contact %s to complain about this problem.''' % (url, generate_contact(contact)))


def generate_contact(contact):
	return '<a href="mailto:%s">%s</a>' % (contact, contact)


def generate_error_html(css, ico, title, h1, short_explanation, further_explanation):
	return '''Content-Type: text/html;charset=utf-8


		<html lang="en">

		  <head>
		    <link media="all" href="%s" type="text/css" rel="stylesheet" />
			<link href="%s" type="image/x-icon" rel="shortcut icon" />
		    <title>%s</title>
		  </head>

		  <body>
		    <h1 class="capitalize">%s</h1>
		    <div class="indent" id="all">
		      <p>%s</p>
		      <p>%s</p>
		    </div>
		  </body>

		</html>''' % (css, ico, title, h1, short_explanation, further_explanation)


def a_blank(href, text):
	return '<a href="%s" target="_blank">%s</a>' % (href, text)


def generate_exists_html(css, ico, model_id, existing_m_url, url, sbml, m_dir_id, progress_icon):
	return generate_model_html("%s Exists" % model_id, "Already at Mimoza",
	                           'There is already %s with this identifier, check it out!' % a_blank(existing_m_url, 'a processed model'),
	                           'If you prefer to carry on with your model instead, press the button below.',
	                           css, ico, model_id, url, sbml, m_dir_id, progress_icon)


def generate_uploaded_html(css, ico, m_name, model_id, url, sbml, m_dir_id, progress_icon):
	return generate_model_html("%s Uploaded" % model_id, "Uploaded, time to visualise!", '',
	                           'Now let\'s visualise it: To start the visualisation press the button below.',
	                           css, ico, m_name, url, sbml, m_dir_id, progress_icon, False)


def generate_model_html(title, h1, text, expl, css, ico, model_id, url, sbml, m_dir_id, progress_icon, header=True):
	h = '''Content-Type: text/html;charset=utf-8


	''' if header else "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01 Transitional//EN'>"
	return '''%s
	<html lang="en">
		<head>
		    <link media="all" href="%s" type="text/css" rel="stylesheet" />
			<link href="%s" type="image/x-icon" rel="shortcut icon" />
		    <title>%s</title>
		</head>
		<body>
	        <h1 class="capitalize">%s</h1>
	        <div class="indent" id="all">
	            <p>Thank you for uploading your model <span class="pant">%s</span>!</p>
	            <p>%s</p>
	            <p>
		            <span id="expl">%s</span>
		            <br>When the visualisation is done, it will become available at <a href="%s">%s</a>.
		            <br>It might take some time (up to 2-4 hours for genome-scale models), so, please, be patient and do not lose hope :)
		        </p>

				%s
			</div>
		</body>
	</html>''' % (h, css, ico, title, h1, model_id, text, expl, url, url, generate_visualisation_button(sbml, m_dir_id, progress_icon))


def generate_visualisation_button(sbml, m_dir_id, progress_icon):
	return '''
		<div class="centre margin" id="visualize_div">
			<form action="/cgi-bin/visualise.py" method="POST" name="input_form" enctype="multipart/form-data">
				<input type="hidden" name="sbml" value="%s" />
				<input type="hidden" name="dir" value="%s" />
				<input class="ui-button" type="submit" id="bb" value="Visualise" onclick="progress()"/>
			</form>
		</div>

		<div class="centre margin" id="visualize_div">
			<img src="%s" style="visibility:hidden" id="img" />
		</div>

		<script>
			function progress() {
				document.getElementById("img").style.visibility="visible";
				document.getElementById("visualize_div").style.visibility="hidden";
				var span = document.getElementById('expl');
				while (span.firstChild) {
					span.removeChild(span.firstChild);
				}
				span.appendChild(document.createTextNode("We are currently visualising your model..."));
			}
		</script>''' % (sbml, m_dir_id, progress_icon)



def create_thanks_for_uploading_html(m_id, m_name, directory_prefix, m_dir_id, url, url_end, css, fav, img):
	directory = '%s/%s' % (directory_prefix, m_dir_id)
	url = '%s/%s/%s' % (url, m_dir_id, url_end)
	sbml = '%s/%s.xml' % (directory, m_id)

	with open('%s/index.html' % directory, 'w+') as f:
		f.write(generate_uploaded_html(css, fav, m_name, m_id, url, sbml, m_dir_id, img))