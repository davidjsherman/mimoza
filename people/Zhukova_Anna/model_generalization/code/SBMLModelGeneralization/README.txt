====================
Model Generalization
====================

**Model Generalization** is a python library that provides a higher-level view of a metabolic model, by masking inessential details while preserving its essential structure. 

It groups biochemical species in the model into semantically equivalent classes and generalizes them into their common parent in the `ChEBI ontology <http://www.ebi.ac.uk/chebi/>`_. The reactions between the same generalized species are factored together into generalized reactions.

Model generalization takes a model in `SBML format <http://sbml.org/>`_ as input, and produces two SBML files as an output:
* SBML containing the generalized model
* SBML file with `groups extension <http://sbml.org/Documents/Specifications/SBML_Level_3/Packages/groups>`_ containing the initial model plus the groups representing quotient species and reaction sets.


Installing libSBML
==================

*Model Generalization* uses *libSBML* library for python with the groups extension. To install it, please download and extract the source files for *libSBML with extensions*, e.g. from `https://sourceforge.net/projects/sbml/files/libsbml/5.8.0/experimental/src/ <https://sourceforge.net/projects/sbml/files/libsbml/5.8.0/experimental/src/>`_. Make sure you have the following libraries installed:
* libxml2-dev 
* xml2 
* libxml2 
* cmake

Then, build and install *libsbml* for python:
* cd where_you_have_extracted_libsbml_archive
* mkdir build
* cd build
* cmake -DENABLE_GROUPS=ON -DWITH_PYTHON=ON ..
* make
* export PYTHONPATH=where_you_have_extracted_libsbml_archive/build/src/bindings/python:$PYTHONPATH


Installing Model Generalization
===============================

From the directory where you have extracted this archive, execute:
* python setup.py


Running Model Generalization
============================

Execute:
* python ./main.py --model path_to_your_model.xml --verbose

For example:
python ./main.py --model ./MODEL1111190000.xml --verbose

The script will produce two SBML files, containing the generalized model:
* path_to_your_model_generalized.xml
* path_to_your_model_with_groups.xml