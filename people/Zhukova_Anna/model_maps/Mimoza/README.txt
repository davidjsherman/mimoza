====================
Mimoza
====================

**Mimoza** is a python library that provides a multilevel zoomable web-based visualization of a metabolic model.
It takes a model in `SBML format <http://sbml.org/>`_ as input, and produces a `COMBINE archive <http://co.mbine.org/documents/archive>`_ as an output.

Dependencies
==================

*Mimoza* uses *libSBML* library for python with the groups extension.
To install it, please download and extract the source files for *libSBML with extensions*,
e.g. from `sourceforge.net <https://sourceforge.net/projects/sbml/files/libsbml/5.8.0/experimental/src/>`_.
Make sure you have the following libraries installed:
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

*Mimoza* uses *Model Generalization* library for python to produce generalized views of the model.
To install it, please download and extract the source files from `gforge.inria.fr <http://metamogen.gforge.inria.fr>`_.
(Make sure that libSBML is installed.)
From the directory where you have extracted it, execute:
* python setup.py

*Mimoza* uses *Tulip 4.4* library for python to layout metabolic networks.
To install it, please download and extract the source files from `sourceforge.net <https://sourceforge.net/projects/auber/files/tulip/tulip-4.4.0/>`_.
From the directory where you have extracted it, execute:
* mkdir build
* cd build
* cmake ..
* make
* sudo make install

*Mimoza* also uses `markup.py <http://markup.sourceforge.net/>`_, `Leaflet <http://leafletjs.com/>`_, `ChEBI Ontology <http://www.ebi.ac.uk/chebi/>`_,
but you do not need to install them.

*Mimoza* was developed using `PyCharm <http://www.jetbrains.com/pycharm/>`_.

Installing Mimoza
===============================

From the directory where you have extracted this archive, execute:
* python setup.py

Do not forget to install the dependencies (see above).


Running Mimoza
============================

Execute:
* python ./main.py --model path_to_your_model.xml --verbose

This will produce a `COMBINE archive <http://co.mbine.org/documents/archive>`_, containing the visualized model.