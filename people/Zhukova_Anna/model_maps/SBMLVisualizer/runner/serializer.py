import os
from shutil import copyfile

import geojson

from modules.combine_archive_creator import archive
from modules.html_generator import create_html, create_embedded_html
from sbml_generalization.utils.logger import log

__author__ = 'anna'


def serialize(directory, m_dir_id, input_model, features, root_compartment, groups_sbml, url, main_url, scripts, css, fav, verbose):
	json = '%s/%s.json' % (directory, root_compartment)
	with open(json, 'w+') as f:
		f.write("var gjsn__{1} = {0}\n".format(geojson.dumps(features).replace('"id": null', ''), root_compartment))

	comp_names = [root_compartment]

	log(verbose, 'create html')
	groups_sbml_url = os.path.basename(groups_sbml)

	embed_url = '%s/%s/comp_min.html' % (main_url, m_dir_id)
	redirect_url = 'comp.html'
	archive_url = "%s.zip" % m_dir_id
	create_html(input_model, directory, url, embed_url, redirect_url, comp_names, groups_sbml_url, archive_url, scripts,
	            css, fav)

	create_embedded_html(input_model, directory, comp_names, scripts, css, fav)

	archive_path = "%s/../../uploads/%s.zip" % (directory, m_dir_id)
	archive(directory, archive_path)
	if os.path.exists(archive_path):
		copyfile(archive_path, "%s/%s.zip" % (directory, m_dir_id))
		os.remove(archive_path)

	log(verbose, 'returning url: %s' % url)
	return url
