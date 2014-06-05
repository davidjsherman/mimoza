import os
from shutil import copyfile

import geojson

from modules.combine_archive_creator import archive
from modules.html_generator import create_html, create_embedded_html
from sbml_generalization.utils.logger import log

__author__ = 'anna'


def serialize(directory, m_dir_id, input_model, features, groups_sbml, url, main_url, scripts, css, fav, verbose,
              max_zoom, comps, map_id=None):
	json = '%s/gjson.json' % directory
	with open(json, 'w+') as f:
		f.write("var gjsn = %s" % geojson.dumps(features).replace('"id": null', ''))


	log(verbose, 'create html')
	groups_sbml_url = os.path.basename(groups_sbml)

	embed_url = '%s/%s/comp_min.html' % (main_url, m_dir_id)
	redirect_url = 'comp.html'
	archive_url = "%s.zip" % m_dir_id

	if not map_id:
		map_id = m_dir_id

	gjson_json = './gjson.json'
	create_html(input_model, directory, embed_url, redirect_url, gjson_json, groups_sbml_url, archive_url, scripts,
	            css, fav, map_id, max_zoom, comps)

	create_embedded_html(input_model, directory, gjson_json, scripts, css, fav, map_id, max_zoom)

	archive_path = "%s/../../uploads/%s.zip" % (directory, m_dir_id)
	archive(directory, archive_path)
	if os.path.exists(archive_path):
		copyfile(archive_path, "%s/%s.zip" % (directory, m_dir_id))
		os.remove(archive_path)

	log(verbose, 'returning url: %s' % url)
	return url
