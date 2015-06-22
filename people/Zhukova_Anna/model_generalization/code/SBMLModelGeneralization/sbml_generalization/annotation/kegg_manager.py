from sbml_generalization.annotation.rdf_annotation_helper import get_is_annotations

__author__ = 'anna'


def get_kegg_r_id(r):
    for annotation in get_is_annotations(r):
        if annotation.find("kegg.reaction") != -1:
            return annotation.replace("kegg.reaction:", '')
    return None


def get_kegg_m_id(m):
    for annotation in get_is_annotations(m):
        if annotation.find("kegg.compound") != -1:
            return annotation.replace("kegg.compound:", '')
    return None
