import os
import logging
import sys
from runner.tulip_helper import visualize_model

__author__ = 'anna'
help_message = '''
Generalizes and visualizes the model.
usage: main.py --model model.xml --verbose
'''

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

import sys
import os
from instant import inline, check_and_set_swig_binary


def main(argv=None):
	# if argv is None:
	# 	argv = sys.argv
	# try:
	# 	sbml, directory, scripts, css, fav, tile, verbose = process_args(argv, help_message)
	# except Usage, err:
	# 	print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
	# 	print >> sys.stderr, "\t for help use --help"
	# 	return 2
	sbml = '/Users/anna/Documents/PhD/magnome/model_generalization/code/MODEL1111190000_golgi.xml'
	# sbml = '/Users/anna/Downloads/yeast_7.11/yeast_7.11_recon_with_groups.xml'
	# sbml = '/Users/anna/Downloads/BMID000000095830.xml'
	# this is a hack to prevent Tulip from printing stuff and producing 500
	# stdout = os.fdopen(os.dup(sys.stdout.fileno()), 'w')
	# stderr = os.fdopen(os.dup(sys.stderr.fileno()), 'w')
	# check_and_set_swig_binary(binary="swig", path="/opt/local/bin/")
	# args = {'modulename': 'inline', 'cache_dir': '/Users/anna/.ins/cache/', 'generate_setup': False}
	# redirect = inline("""
	# void redirect(void) {
     #    freopen("/Users/anna/log.log", "w", stdout);
     #    freopen("/Users/anna/log.log", "w", stderr);
	# }
	# """, **(args))
	# redirect()
	# os.system("at now <<< '/Users/anna/Documents/PhD/magnome/model_maps/SBMLVisualizer/test.py'")

	visualize_model('/Users/anna/Documents/PhD/magnome/', 'mm', 'http://mimoza.bordeaux.inria.fr', 'comp.html', sbml,
	                JS_SCRIPTS, CSS_SCRIPTS, FAVIICON, False)  # visualize_model(directory, sbml, scripts, css, fav, tile, verbose)
	#
	# redirect_back = inline("""
	# void redirect(void) {
     #    fclose(stdout);
     #    fclose(stderr);
	# }
	# """, **(args))
	# redirect_back()

	print "Hello world!"

if __name__ == "__main__":
	sys.exit(main())