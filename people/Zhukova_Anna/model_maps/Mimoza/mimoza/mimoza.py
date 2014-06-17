__author__ = 'anna'

CONTACT_EMAIL = 'anna.zhukova@inria.fr'

MIMOZA_URL = 'http://mimoza.bordeaux.inria.fr'

MIMOZA_ERROR_URL = '%s/error.html' % MIMOZA_URL
MIMOZA_UPLOAD_ERROR_URL = '%s/upload_error.html' % MIMOZA_URL

MIMOZA_JS = 'lib/modelmap/maptools.js'
MIMOZA_POPUP_JS = 'lib/modelmap/popup_formatter.js'
MIMOZA_GEOJSON_JS = 'lib/modelmap/geojson_manager.js'
MIMOZA_CSS = 'lib/modelmap/modelmap.css'
MIMOZA_FAVICON = 'lib/modelmap/fav.ico'

JQUERY_JS = 'lib/jquery/jquery-2.1.1.min.js'
JQUERY_UI_JS = 'lib/jquery/jquery-ui-1.10.4.custom.min.js'
JQUERY_UI_CSS = 'lib/jquery/jquery-ui-1.10.4.custom.min.css'

LEAFLET_LABEL_JS = 'lib/leaflet_label/leaflet.label.js'
LEAFLET_JS = 'lib/leaflet/leaflet.js'
LEAFLET_LABEL_CSS = 'lib/leaflet_label/leaflet.label.css'
LEAFLET_CSS = 'lib/leaflet/leaflet.css'

PROGRESS_ICON = 'lib/modelmap/ajax-loader.gif'
LOADER_ICON = 'lib/modelmap/loader.gif'

SBML_ORG = "http://sbml.org"

JS_SCRIPTS = [LEAFLET_JS, LEAFLET_LABEL_JS, JQUERY_JS, MIMOZA_JS, MIMOZA_POPUP_JS, MIMOZA_GEOJSON_JS, JQUERY_UI_JS]
CSS_SCRIPTS = [MIMOZA_CSS, LEAFLET_CSS, LEAFLET_LABEL_CSS, JQUERY_UI_CSS]
