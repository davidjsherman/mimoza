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
		page.p()
		page.span('Download the&nbsp;')
		page.a('generalised model', href=groups_sbml, download=None)
		page.span('.')
		page.p.close()
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
	page.script('var comp2geojson = {0}; var compartment = "{1}";'.format(org2scripts, normalize(default_organelle)) + '''
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