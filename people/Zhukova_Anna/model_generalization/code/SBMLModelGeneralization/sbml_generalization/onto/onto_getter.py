import logging

__author__ = 'anna'

import sbml_generalization

import os


def get_chebi():
    return "%s/data/chebi.obo" % os.path.dirname(os.path.abspath(sbml_generalization.__file__))


def get_go():
    return "%s/data/gene_ontology_ext.obo" % os.path.dirname(os.path.abspath(sbml_generalization.__file__))