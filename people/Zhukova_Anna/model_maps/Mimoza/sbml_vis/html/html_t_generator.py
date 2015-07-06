import io
import os

from jinja2 import Environment, PackageLoader
import libsbml
from sbml_vis.graph.graph_properties import ALL_COMPARTMENTS

__author__ = 'anna'

def create_html(model, directory, embed_url, json_files, c_id2json_vars, groups_sbml_url, archive_url,
                map_id, c_id2out_c_id):

    c_id2name = {c.getId(): c.getName() for c in model.getListOfCompartments() if c.getId() in c_id2json_vars}
    if ALL_COMPARTMENTS in c_id2json_vars:
        c_id2name[ALL_COMPARTMENTS] = "All compartment view"

    env = Environment(loader=PackageLoader('sbml_vis.html', 'templates'))
    template = env.get_template('comp.html')
    c_id2json_vars = '{%s}' % ", ".join(
        ("'%s':[%s]" % (c_id, ", ".join(json_vars)) for (c_id, json_vars) in c_id2json_vars.iteritems()))
    page = template.render(model=model,
                           notes=model.getNotes().toXMLString().decode('utf-8')
                           if model.getNotes() and model.getNotes().toXMLString() else '',
                           json_files=json_files,
                           c_id2json_vars=c_id2json_vars,
                           groups_sbml_url=groups_sbml_url, archive_url=archive_url, map_id=map_id,
                           c_id2out_c_id=c_id2out_c_id, embed_url=embed_url,
                           comp_c_id2name=sorted(c_id2name.iteritems(), key=lambda (_, c_name): c_name)
                           if len(c_id2name) > 1 else None,
                           c_id2name=c_id2name)
    with io.open(os.path.join(directory, 'comp.html'), 'w+', encoding='utf-8') as f:
        f.write(page)

    template = env.get_template('index.html')
    page = template.render()
    with open(os.path.join(directory, 'index.html'), 'w+') as f:
        f.write(page)

    template = env.get_template('comp_min.html')
    page = template.render(model=model, json_files=json_files, c_id2json_vars=c_id2json_vars,
                           map_id=map_id, c_id2out_c_id=c_id2out_c_id, c_id2name=c_id2name)
    with io.open(os.path.join(directory, 'comp_min.html'), 'w+', encoding='utf-8') as f:
        f.write(page)


def create_multi_html(model_data, title, description, directory):
    model_data = [(t,
                   {ALL_COMPARTMENTS: "All compartment view"} if ALL_COMPARTMENTS in c_id2json_vars
                   else {c.getId(): c.getName()
                         for c in libsbml.SBMLReader().readSBML(sbml).getModel().getListOfCompartments()
                         if c.getId() in c_id2json_vars},
                   json_files,
                   '{%s}' % ", ".join(("'%s':[%s]" % (c_id, ", ".join(json_vars))
                                       for (c_id, json_vars) in c_id2json_vars.iteritems())),
                   c_id2out_c_id, map_id, descr)
                  for (t, sbml, json_files, c_id2json_vars, c_id2out_c_id, map_id, descr) in model_data]

    env = Environment(loader=PackageLoader('sbml_vis.html', 'templates'))
    template = env.get_template('multi_comp.html')
    page = template.render(model_data=model_data, title=title, description=description)
    with io.open(os.path.join(directory, 'index.html'), 'w+', encoding='utf-8') as f:
        f.write(page)


def generate_model_html(title, h1, text, expl, more_expl, model_id, sbml, gen_sbml, sbgn, gen_sbgn,
                        m_dir_id, progress_icon, action):
    env = Environment(loader=PackageLoader('sbml_vis.html', 'templates'))
    template = env.get_template('action.html')
    return template.render(title=title, h1=h1, text=text, expl=expl, more_expl=more_expl, model_id=model_id,
                           sbml=sbml, gen_sbml=gen_sbml, sbgn=sbgn, gen_sbgn=gen_sbgn,
                           m_dir_id=m_dir_id, progress_icon=progress_icon, action=action)



def generate_uploaded_sbml_html(m_name, m_id, m_url, sbml, gen_sbml, sbgn, gen_sbgn, m_dir_id, progress_icon):
    return generate_model_html("%s Uploaded" % m_id, "Uploaded, time to generalize!", '',
                               'Now let\'s generalize it: To start the generalization press the button below.',
                               '''<br>When the generalization is done, it will become available at <a href="%s">%s</a>.
                               <br>It might take some time (up to an hour for genome-scale models), so, please, be patient and do not lose hope :)'''
                               % (m_url, m_url),
                               m_name, sbml, gen_sbml, sbgn, gen_sbgn, m_dir_id, progress_icon, 'generalize.py')


def generate_uploaded_generalized_sbml_html(m_name, m_id, m_url, sbml, gen_sbml, sbgn, gen_sbgn, m_dir_id, progress_icon):
    return generate_model_html("%s Uploaded" % m_id, "Uploaded, time to visualize!", '',
                               '''Your model seems to be already generalized. Now let\'s visualize it: To start the visualization press the button below.<br>
                               <i>(If your model contains <a href="http://sbml.org/Documents/Specifications/SBML_Level_3/Packages/Layout_%28layout%29" target="_blank">SBML layout</a> information,
                               it will be used during the visualization.)</i>''',
                               '<br>When the visualization is done, it will become available at <a href="%s">%s</a>.'
                               % (m_url, m_url),
                               m_name, sbml, gen_sbml, sbgn, gen_sbgn, m_dir_id, progress_icon,
                               'visualise.py')


def generate_generalization_finished_html(m_name, m_id, m_url, sbml, gen_sbml, sbgn, gen_sbgn, m_dir_id, progress_icon):
    return generate_model_html("%s Generalized" % m_id, "Generalized, time to visualize!", '',
                               '''Your model is successfully generalized. Now let\'s visualize it: To start the visualization press the button below.<br>
                               <i>(If your model contained <a href="http://sbml.org/Documents/Specifications/SBML_Level_3/Packages/Layout_%28layout%29" target="_blank">SBML layout</a> information,
                               it will be used during the visualization.)</i>''',
                               '<br>When the visualization is done, it will become available at <a href="%s">%s</a>.'
                               % (m_url, m_url),
                               m_name, sbml, gen_sbml, sbgn, gen_sbgn, m_dir_id, progress_icon,
                               'visualise.py')

def create_thanks_for_uploading_html(m_id, m_name, directory_prefix, m_dir_id, url, url_end, img,
                                     generate_html=generate_uploaded_sbml_html):
    directory = os.path.join(directory_prefix, m_dir_id)
    m_url = '%s/%s/%s' % (url, m_dir_id, url_end)
    sbml = os.path.join(directory, '%s.xml' % m_id)
    gen_sbml = os.path.join(directory, '%s_generalized.xml' % m_id)
    sbgn = os.path.join(directory, '%s_initial_model.sbgn' % m_id)
    gen_sbgn = os.path.join(directory, '%s_generalized.sbgn' % m_id)

    with open(os.path.join(directory, 'index.html'), 'w+') as f:
        page = generate_html(gen_sbgn, gen_sbml if os.path.exists(gen_sbml) else '',
                             img, m_dir_id, m_id, m_name, m_url, sbgn, sbml)
        f.write(page)


def create_thanks_for_uploading_generalized_html(m_id, m_name, directory_prefix, m_dir_id, url, url_end, css, js, fav,
                                                 img, generate_html=generate_uploaded_generalized_sbml_html):
    directory = os.path.join(directory_prefix, m_dir_id)
    m_url = '%s/%s/%s' % (url, m_dir_id, url_end)
    sbml = os.path.join(directory, '%s.xml' % m_id)
    gen_sbml = os.path.join(directory, '%s_generalized.xml' % m_id)
    sbgn = os.path.join(directory, '%s_initial_model.sbgn' % m_id)
    gen_sbgn = os.path.join(directory, '%s_generalized.sbgn' % m_id)

    with open('%s/index.html' % directory, 'w+') as f:
        f.write(generate_html(css, js, fav, m_name, m_id, m_url, sbml, gen_sbml if os.path.exists(gen_sbml) else '',
                              sbgn, gen_sbgn, m_dir_id, img))
