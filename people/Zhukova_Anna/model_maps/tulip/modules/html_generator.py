__author__ = 'anna'
import markup


def normalize(organelle):
	return organelle.lower().replace(' ', '_')


def add_header(model_id, model_name, page):
	""" <h1 class="capitalize">
			<span id='comp'>Compartments</span> of <a href="http://www.ebi.ac.uk/biomodels-main/model_id">model_name</a>
		</h1> """
	page.h1(class_='capitalize')
	page.span('Compartments', id='comp')
	page.span('&nbsp;of&nbsp;')
	page.a(model_name, href='http://www.ebi.ac.uk/biomodels-main/{0}'.format(model_id))
	page.h1.close()


def add_compartment_menu(html_file, organelles, page):
	page.ul(class_='menu')
	for organelle in organelles:
		page.li()
		page.a(organelle, href='{0}?name={1}'.format(html_file, normalize(organelle)))
		page.li.close()
	page.ul.close()


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
	""" <div class="nomargin" id="map" style="width: 1024px; height: 1024px"></div> """
	page.div('', class_='nomargin', id='map', style="width: 1024px; height: 1024px")


def add_model_description(model, page):
	model_description = model.getNotes()
	if model_description:
		page.p(model_description.toXMLString(), class_='margin', id='descr')


def add_js(default_organelle, org2scripts, page):
	page.script('var comp2geojson = {0}; var compartment = "{1}";'.format(org2scripts, default_organelle) + '''
		var comp = gup('name');
		if (comp) {
			compartment = comp;
		}
		if (compartment) {
			var span = document.getElementById('comp');
			while (span.firstChild) {
				span.removeChild(span.firstChild);
			}
			span.appendChild(document.createTextNode(compartment));

			map = initializeMap(5);
			var name2popup = {};
			getGeoJson(map, comp2geojson[compartment], name2popup);


			L.tileLayer('./white.jpg', {
				continuousWorld: true,
				noWrap: true,
				tileSize: 256,
				maxZoom: 4,
				minZoom: 1,
				tms: true,
				unloadInvisibleTiles: false,
				updateWhenIdle: true,
				reuseTiles: true
			}).addTo(map);
		} '''
	)


def generate_html(model, html_file, organelles):
	page = markup.page()
	scripts = ['http://cdn.leafletjs.com/leaflet-0.7.1/leaflet.js', 'http://code.jquery.com/jquery-2.0.3.min.js',
			   './maptools.js']
	default_organelle = ''
	org2scripts = '{'
	for organelle in organelles:
		organelle = normalize(organelle)
		default_organelle = organelle
		scripts += ['./{0}_f.json'.format(organelle), './{0}.json'.format(organelle)]
		org2scripts += "'{0}': [gjsn__{0}, gjsn__{0}_full],".format(organelle)
	org2scripts += '}'

	model_id = model.getId()
	model_name = model.getName()
	if not model_name:
		model_name = model_id
	page.init(title=model_name, css=['./modelmap.css', './leaflet.css'], script=scripts, fav='./fav.ico')

	add_header(model_id, model_name, page)

	add_compartment_menu(html_file, organelles, page)

	add_explanations(page)

	add_map(page)

	add_model_description(model, page)

	add_js(default_organelle, org2scripts, page)

	with open(html_file, 'w+') as f:
		f.write(str(page))