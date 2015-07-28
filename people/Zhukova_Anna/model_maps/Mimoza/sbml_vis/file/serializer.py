from collections import defaultdict
import logging
import os
from shutil import copytree
import shutil

import geojson
from sbml_vis.graph.graph_properties import ALL_COMPARTMENTS
from sbml_vis.converter.tlp2geojson import DEFAULT_LAYER2MASK
from sbml_vis.html.html_t_generator import create_html

from sbml_vis.file.combine_archive_creator import archive


__author__ = 'anna'


def serialize(directory, m_dir_id, input_model, c_id2level2features, c_id2out_c_id, groups_sbml, main_url, map_id=None,
              layer2mask=DEFAULT_LAYER2MASK, tab2html=None, title=None):
    if not map_id:
        map_id = m_dir_id

    if layer2mask:
        layer2mask = [[l, layer2mask[l]] for l in sorted(layer2mask.iterkeys())]

    c_id2geojson_files, c_id2geojson_names = defaultdict(list), defaultdict(list)
    for c_id, level2features in c_id2level2features.iteritems():
        for level in [0, 1, 2]:
            features = level2features[level] if level in level2features \
                else geojson.FeatureCollection([], geometry=geojson.Polygon([[0, 0], [0, 0], [0, 0], [0, 0]]))
            json_name = "level_%s_%s_%d" % (map_id, c_id, level)
            json_file = os.path.join(directory, '%s.json' % json_name)
            json_url = '%s.json' % json_name
            with open(json_file, 'w+') as f:
                f.write("var %s = %s" % (json_name, geojson.dumps(features, allow_nan=True).replace('"id": null', '')))
            c_id2geojson_files[c_id].append(json_url)
            c_id2geojson_names[c_id].append(json_name)

    logging.info('create html')
    groups_sbml_url = os.path.basename(groups_sbml)

    embed_url = '%s/%s/comp_min.html' % (main_url, m_dir_id)
    archive_url = "%s.zip" % m_dir_id

    geojson_files = reduce(lambda l1, l2: l1 + l2, c_id2geojson_files.itervalues(), [])
    logging.info(input_model)
    model_id = input_model.getId()
    model_name = input_model.getName()
    if not model_name:
        model_name = model_id if model_id else 'an anonymous model'
    non_empty = input_model.getNumReactions() > 0
    model_notes = input_model.getNotes().toXMLString().decode('utf-8')\
        if input_model.getNotes() and input_model.getNotes().toXMLString().strip() else False

    c_id2name = {c.getId(): c.getName() for c in input_model.getListOfCompartments() if c.getId() in c_id2geojson_names}
    if ALL_COMPARTMENTS in c_id2geojson_names:
        c_id2name[ALL_COMPARTMENTS] = "All compartment view"
    create_html(non_empty=non_empty, notes=model_notes, model_name=model_name, model_id=model_id, c_id2name=c_id2name,
                directory=directory, embed_url=embed_url,
                json_files=geojson_files, c_id2json_vars=c_id2geojson_names, groups_sbml_url=groups_sbml_url,
                archive_url=archive_url, map_id=map_id, c_id2out_c_id=c_id2out_c_id, layer2mask=layer2mask,
                tab2html=tab2html, title=title)

    temp_copy = os.path.join(directory, m_dir_id)
    archive_path = os.path.join(directory, "%s.zip" % m_dir_id)
    if not os.path.exists(temp_copy):
        copytree(directory, temp_copy)
    if os.path.exists(temp_copy):
        archive(temp_copy, archive_path)
        shutil.rmtree(temp_copy)
    return c_id2geojson_files, c_id2geojson_names
