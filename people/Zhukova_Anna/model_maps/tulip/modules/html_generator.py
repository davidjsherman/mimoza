__author__ = 'anna'
import markup


def normalize(organelle):
	return organelle.lower().replace(' ', '_')


def generate_html(model_id, html_file, organelles):
	page = markup.page()
	scripts = ['http://cdn.leafletjs.com/leaflet-0.7.1/leaflet.js', 'http://code.jquery.com/jquery-2.0.3.min.js', './maptools.js']
	org2scripts = '{'
	for organelle in organelles:
		organelle = normalize(organelle)
		scripts += ['./{0}_f.json'.format(organelle), './{0}.json'.format(organelle)]
		org2scripts += "'{0}': [gjsn__{0}, gjsn__{0}_full],".format(organelle)
	org2scripts += '}'

	page.init(title=model_id, css=['./modelmap.css', './leaflet.css'],
	          script=scripts, fav='./fav.ico')

	# <h1 class="capitalize"><span id='comp'>Compartments</span> of <a href="http://www.ebi.ac.uk/biomodels-main/MODEL1111190000">MODEL1111190000</a></h1>
	page.h1(class_='capitalize')
	page.span('Compartments', id='comp')
	page.span('&nbsp;of&nbsp;')
	page.a(model_id, href='http://www.ebi.ac.uk/biomodels-main/{0}'.format(model_id))
	page.h1.close()

	page.ul(class_='menu')
	for organelle in organelles:
		page.li()
		page.a(organelle, href='{0}?name={1}'.format(html_file, normalize(organelle)))
		page.li.close()
	page.ul.close()

	# <div id="explanations" class="margin">
	#   <p><span class="pant">Zoom in</span> to see the more detailed
	#   model. <span class="pant">Zoom out</span> to see the generalized
	#   model. <span class="pant">Click</span> on species and reactions to see
	#   their annotations.</p>
	# </div>
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

	# <div class="nomargin" id="map" style="width: 1024px; height: 1024px"></div>
	page.div('', class_='nomargin', id='map', style="width: 1024px; height: 1024px")

	page.script('var comp2geojson = {0};'.format(org2scripts) + '''

	    var compartment = gup('name');
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
		}'''
	)
	# page.p( paras )
	# page.img( src=images, width=100, height=80, alt="Thumbnails" )

	with open(html_file, 'w+') as f:
		f.write(str(page))