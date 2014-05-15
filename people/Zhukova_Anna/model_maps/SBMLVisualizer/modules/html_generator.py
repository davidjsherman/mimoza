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
		page.a(denormalize(organelle), href='?name=%s' % (normalize(organelle)))
		page.li.close()
	page.ul.close()


def add_download_link(groups_sbml, archive_url, page):
	page.ul(class_='menu margin centre')
	if groups_sbml:
		page.li('Download the <a href=%s download>generalised model</a>.' % groups_sbml, id='download')
	if archive_url:
		page.li('Download the <a href=%s download>COMBINE archive</a>.' % archive_url)
	page.li('<a onclick="overlay()" href="#">Embed</a>')
	page.ul.close()


def add_search(page):
	""" <div>
            <form name="search_form" onclick="search(map, name2popup);">
                <label><input id="tags" type="text" name="search_input"></label>
                <input type="button" value="Search" >
            </form>
        </div> """
	page.div(class_='margin', id='search')
	page.form(name="search_form", id="search_form")
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

	page.p(
		'''%s - compartments; %s/%s/%s - generalised/specific/ubiquitous species; %s/%s/%s/%s - generalised transport/transport/generalised/other reactions.''' % (
			format_color("yellow", 255, 255, 179),
			format_color('orange', 253, 180, 98), format_color('red', 251, 128, 114),
			format_color('gray', 180, 180, 180),
			format_color('turquoise', 141, 211, 199), format_color('violet', 190, 186, 218),
			format_color('green', 179, 222, 105), format_color('blue', 128, 177, 211)))

	page.div.close()


def format_color(color_name, r, g, b, a=0.8):
	return '<span style="background-color:rgba(%d, %d, %d, %.2f)">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>' % (r, g, b, a)


def add_map(page):
	""" <div class="margin" id="map" style="width: 1024px; height: 1024px"></div> """
	page.div('', class_='margin map', id='map')


def add_model_description(model, page):
	model_description = model.getNotes()
	if model_description:
		page.p(model_description.toXMLString(), class_='margin just', id='descr')


def add_js(default_organelle, org2scripts, page):
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

            initializeMap(comp2geojson[compartment]);
        } '''
	)


def add_min_js(default_organelle, org2scripts, page):
	page.script('var comp2geojson = %s; var compartment = "%s";' % (org2scripts, normalize(default_organelle)) + '''
        var comp = gup('name');
        if (comp) {
            compartment = comp;
        }
        if (compartment) {
            initializeMap(comp2geojson[compartment]);
        } '''
	)


def add_embed_button(page):
	page.p(class_="margin")
	page.button("Embed", type="button", onclick='overlay()')
	page.p.close()


def add_embedding_dialog(page, url):
	page.div(id="overlay")
	page.div()
	page.a(class_="boxclose", id="boxclose", onclick='overlay()')
	page.a.close()
	page.span.close()
	page.p(class_="margin")
	page.span('Size: ')
	page.input(class_="embed_size", id="embed-size-width", type="text", name="width", value="800")
	page.span(" x ")
	page.input(class_="embed_size", id="embed-size-height", type="text", name="height", value="400")
	page.p.close()
	page.p(class_="margin")
	page.input(class_="embed_url", id="embed-html-snippet",
	           value='<iframe src="%s" width="800" height="400" frameborder="0" style="border:0"></iframe>' % url,
	           type="text", name="embedHtml")
	page.p.close()
	page.input(type="hidden", id="embed-url", name="url", value="%s" % url)
	page.div.close()
	page.div.close()


def create_html(model, directory, url, embed_url, redirect_url, organelles, groups_sbml_url, archive_url, scripts, css, fav):
	page = markup.page()
	if not scripts:
		scripts = []
	default_organelle = normalize(organelles[0]) if organelles else ''
	org2scripts = '{'
	for organelle in organelles:
		organelle = normalize(organelle)

		scripts.append('./%s.json' % organelle)
		org2scripts += "'{0}': gjsn__{0},".format(organelle)
	org2scripts += '}'

	if not css:
		css = []

	model_id = model.getId()
	model_name = model.getName()
	if not model_name:
		model_name = model_id
	page.init(title=model_name, css=css, script=scripts, fav=fav)

	add_header(model_id, model_name, page)

	page.div(class_='centre', id='all')
	add_compartment_menu(url, organelles, page)

	add_download_link(groups_sbml_url, archive_url, page)

	# add_embed_button(page)

	add_explanations(page)

	add_search(page)

	add_map(page)

	add_model_description(model, page)

	add_embedding_dialog(page, embed_url)

	page.div.close()

	add_js(default_organelle, org2scripts, page)

	with open('%s/comp.html' % directory, 'w+') as f:
		f.write(str(page))
	with open('%s/index.html' % directory, 'w+') as f:
		f.write(generate_redirecting_html(redirect_url, css[0] if css else '', fav))


def create_embedded_html(model, directory, organelles, scripts, css, fav):
	page = markup.page()
	if not scripts:
		scripts = []
	default_organelle = normalize(organelles[0]) if organelles else ''
	org2scripts = '{'
	for organelle in organelles:
		organelle = normalize(organelle)

		scripts.append('./%s.json' % organelle)
		org2scripts += "'{0}': gjsn__{0},".format(organelle)
	org2scripts += '}'

	if not css:
		css = []

	model_id = model.getId()
	page.init(title=model_id, css=css, script=scripts, fav=fav)

	add_map(page)

	add_min_js(default_organelle, org2scripts, page)

	with open('%s/comp_min.html' % directory, 'w+') as f:
		f.write(str(page))


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

          %s

        </html>''' % (css, ico, title, generate_error_html_body(h1, short_explanation, further_explanation))


def generate_error_html_body(h1, short_explanation, further_explanation):
	return '''<body>
            <h1 class="capitalize">%s</h1>
            <div class="indent" id="all">
              <p>%s</p>
              <p>%s</p>
            </div>
          </body>''' % (h1, short_explanation, further_explanation)


def a_blank(href, text):
	return '<a href="%s" target="_blank">%s</a>' % (href, text)


def generate_exists_html(css, js, ico, model_id, existing_m_url, url, sbml, m_dir_id, progress_icon):
	return generate_model_html("%s Exists" % model_id, "Already at Mimoza",
	                           'There is already %s with this identifier, check it out!' % a_blank(existing_m_url,
	                                                                                               'a processed model'),
	                           'If you prefer to carry on with your model instead, press the button below.',
	                           css, js, ico, model_id, url, sbml, m_dir_id, progress_icon, 'visualise.py', False)


def generate_uploaded_html(css, js, ico, m_name, model_id, url, sbml, m_dir_id, progress_icon):
	return generate_model_html("%s Uploaded" % model_id, "Uploaded, time to generalise!", '',
	                           'Now let\'s generalise it: To start the generalisation press the button below.',
	                           '''<br>When the generalisation is done, it will become available at <a href="%s">%s</a>.
                               <br>It might take some time (up to 2-4 hours for genome-scale models), so, please, be patient and do not lose hope :)''' % (url, url),
	                           css, js, ico, m_name, sbml, m_dir_id, progress_icon, 'generalize.py', False)


def generate_uploaded_generalized_html(css, js, ico, m_name, model_id, url, sbml, m_dir_id, progress_icon):
	return generate_model_html("%s Uploaded" % model_id, "Uploaded, time to visualise!", '',
	                           'Your model seems to be already generalised. Now let\'s visualise it: To start the visualisation press the button below.',
	                           '''<br>When the visualisation is done, it will become available at <a href="%s">%s</a>.''' % (url, url),
	                           css, js, ico, m_name, sbml, m_dir_id, progress_icon, 'visualise.py', False)


def generate_generalized_html(css, js, ico, m_name, model_id, url, sbml, m_dir_id, progress_icon):
	return generate_model_html("%s Generalised" % model_id, "Generalised, time to visualise!", '',
	                           'Your model is successfully generalised. Now let\'s visualise it: To start the visualisation press the button below.',
	                           '''<br>When the visualisation is done, it will become available at <a href="%s">%s</a>.''' % (url, url),
	                           css, js, ico, m_name, sbml, m_dir_id, progress_icon, 'visualise.py', False)


def generate_model_html(title, h1, text, expl, more_expl, css, js, ico, model_id, sbml, m_dir_id, progress_icon, action, header=True):
	scripts = '\n'.join(['<script src="%s" type="text/javascript"></script>' % it for it in js])
	h = "Content-Type: text/html;charset=utf-8" if header else "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01 Transitional//EN'>"
	return '''%s


    <html lang="en">
        <head>
            <link media="all" href="%s" type="text/css" rel="stylesheet" />
            <link href="%s" type="image/x-icon" rel="shortcut icon" />
            %s
            <title>%s</title>
        </head>
        <body>
            <h1 class="capitalize">%s</h1>
            <div class="indent" id="all">
                <p>Thank you for uploading your model <span class="pant">%s</span>!</p>
                <p>%s</p>
                <p>
                    <span id="expl">%s</span>
                    %s
                </p>
                %s
            </div>
        </body>
    </html>''' % (h, css, ico, scripts, title, h1, model_id, text, expl, more_expl,
	              generate_visualisation_button(sbml, m_dir_id, progress_icon, action))


def generate_visualisation_button(sbml, m_dir_id, progress_icon, action):
	return '''
        <div class="centre margin" id="visualize_div">
            <form action="/cgi-bin/%s" method="POST" name="input_form" enctype="multipart/form-data">
                <input type="hidden" name="sbml" value="%s" />
                <input type="hidden" name="dir" value="%s" />
                <input class="ui-button img-centre" type="submit" id="bb" value="Go!" onclick="progress()"/>
            </form>
        </div>

        <img class="img-centre" src="%s" style="visibility:hidden" id="img" />

        <script>
            function progress() {
                document.getElementById("img").style.visibility="visible";
                document.getElementById("visualize_div").style.visibility="hidden";
                var span = document.getElementById('expl');
                while (span.firstChild) {
                    span.removeChild(span.firstChild);
                }
                span.appendChild(document.createTextNode("We are currently processing your model..."));
            }

        </script>''' % (action, sbml, m_dir_id, progress_icon)


def create_thanks_for_uploading_html(m_id, m_name, directory_prefix, m_dir_id, url, url_end, css, js, fav, img):
	directory = '%s/%s' % (directory_prefix, m_dir_id)
	m_url = '%s/%s/%s' % (url, m_dir_id, url_end)
	sbml = '%s/%s.xml' % (directory, m_id)

	with open('%s/index.html' % directory, 'w+') as f:
		f.write(generate_uploaded_html(css, js, fav, m_name, m_id, m_url, sbml, m_dir_id, img))


def create_thanks_for_uploading_generalized_html(m_id, m_name, directory_prefix, m_dir_id, url, url_end, css, js, fav,
                                                 img, generate_html=generate_uploaded_generalized_html):
	directory = '%s/%s' % (directory_prefix, m_dir_id)
	m_url = '%s/%s/%s' % (url, m_dir_id, url_end)
	sbml = '%s/%s_with_groups.xml' % (directory, m_id)

	with open('%s/index.html' % directory, 'w+') as f:
		f.write(generate_html(css, js, fav, m_name, m_id, m_url, sbml, m_dir_id, img))


def create_exists_html(m_id, existing_m_dir_id, directory_prefix, m_dir_id, url, url_end, css, js, fav, img):
	directory = '%s/%s' % (directory_prefix, m_dir_id)
	m_url = '%s/%s/%s' % (url, m_dir_id, url_end)
	sbml = '%s/%s.xml' % (directory, m_id)
	existing_m_url = '%s/%s/%s' % (url, existing_m_dir_id, url_end)

	with open('%s/index.html' % directory, 'w+') as f:
		f.write(generate_exists_html(css, js, fav, m_id, existing_m_url, m_url, sbml, m_dir_id, img))