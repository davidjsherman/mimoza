from collections import defaultdict
import logging
import os
from shutil import copytree
import shutil

import geojson

from sbml_vis.file.combine_archive_creator import archive
from sbml_vis.html.html_generator import create_html, create_embedded_html


__author__ = 'anna'


def serialize(directory, m_dir_id, input_model, c_id2level2features, c_id2out_c_id, groups_sbml, main_url, scripts, css,
              fav, map_id=None):
    if not map_id:
        map_id = m_dir_id

    c_id2geojson_files, c_id2geojson_names = defaultdict(list), defaultdict(list)
    for c_id, level2features in c_id2level2features.iteritems():
        for level in [0, 1, 2]:
            features = level2features[level] if level in level2features else geojson.FeatureCollection([],
                geometry=geojson.Polygon([[0, 0], [0, 0], [0, 0], [0, 0]]))
            json_name = "level_%s_%s_%d" % (map_id, c_id, level)
            json_file = '%s/%s.json' % (directory, json_name)
            json_url = '%s.json' % json_name
            with open(json_file, 'w+') as f:
                f.write("var %s = %s" % (json_name, geojson.dumps(features).replace('"id": null', '')))
            c_id2geojson_files[c_id].append(json_url)
            c_id2geojson_names[c_id].append(json_name)

    logging.info('create html')
    groups_sbml_url = os.path.basename(groups_sbml)

    embed_url = '%s/%s/comp_min.html' % (main_url, m_dir_id)
    redirect_url = 'comp.html'
    archive_url = "%s.zip" % m_dir_id

    geojson_files = reduce(lambda l1, l2: l1 + l2, c_id2geojson_files.itervalues(), [])
    create_html(input_model, directory, embed_url, redirect_url, geojson_files, c_id2geojson_names, groups_sbml_url,
                archive_url, scripts,
                css, fav, map_id, c_id2out_c_id)

    create_embedded_html(input_model, directory, geojson_files, c_id2geojson_names, scripts, css, fav, map_id)

    temp_copy = '%s/%s' % (directory, m_dir_id)
    archive_path = "%s/%s.zip" % (directory, m_dir_id)
    if not os.path.exists(temp_copy):
        copytree(directory, temp_copy)
    if os.path.exists(temp_copy):
        archive(temp_copy, archive_path)
        shutil.rmtree(temp_copy)
    return c_id2geojson_files, c_id2geojson_names
