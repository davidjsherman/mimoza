====================
Mimoza
====================

**Mimoza** is a a Python library for metabolic model visualization and navigation that allows you
to explore your metabolic models in a semantically zoomable manner.

**Mimoza** combines the `model generalization method <http://metamogen.gforge.inria.fr>`_
with the `zooming user interface (ZUI) <http://en.wikipedia.org/wiki/Zooming_user_interface>`_
paradigm and allows a human expert to explore metabolic network models in a semantically zoomable manner.

**Mimoza** takes a metabolic model in `SBML <http://sbml.org/>`_ format, generalizes it to detect similar metabolites
and similar reactions, and automatically creates a 3-level zoomable map:
  (1) the most detailed view represents the initial network with the generalization-based layout
  (similar metabolites and reactions are placed next to each other).
  (2) the intermediate view shows the generalized versions of reactions and metabolites in each compartment;
  (3) the general view represents the compartments and the transport reactions between them.

**Mimoza** highlights the general model structure and the divergences from it, such as alternative paths or missing reactions,
and allows a user to analyse it in a top-down manner.

The network map can be browsed online or downloaded as a `COMBINE archive <http://co.mbine.org/documents/archive>`_, containing:
  * all the files needed for offline browsing;
  * SBML files with the groups and layout extensions, representing the initial and generalized versions of your model
  and their layout;
  * `SBGN <http://www.sbgn.org/>`_ representation of your model.


Article
=======

**Mimoza** is described in `Zhukova, A., Sherman, D. J. (2015).
Mimoza: Web-Based Semantic Zooming and Navigation in Metabolic Networks. BMC Systems Biology, 9:10
<http://identifiers.org/doi/10.1186/s12918-015-0151-5>`_.


Dependencies
==================

*Mimoza* uses `libSBML <http://sbml.org/Software/libSBML>`_ library for python with the groups and layout extensions.
Install it:
  * sudo pip install python-libsbml-experimental

*Mimoza* uses *Model Generalization* library for python to produce generalized views of the model.
To install it, please download and extract the source files from `gforge.inria.fr <http://metamogen.gforge.inria.fr>`_.
From the directory where you have extracted it, execute:
  * sudo python setup.py

*Mimoza* uses *Tulip 4.4* library for python to layout metabolic networks.
To install it, please download and extract the source files from `sourceforge.net <https://sourceforge.net/projects/auber/files/tulip/tulip-4.4.0/>`_.
From the directory where you have extracted it, execute:
  * mkdir build
  * cd build
  * cmake ..
  * make
  * sudo make install

*Mimoza* uses `SymPy <http://www.sympy.org/>`_ and `Python bindings for geojson <https://pypi.python.org/pypi/geojson/>`_:
  * sudo pip install sympy
  * sudo pip install geojson

If you want to have export of your maps in `SBGN PD<http://www.sbgn.org/>`_, install `libSBGN bindings for Python <https://github.com/matthiaskoenig/libsbgn-python>`_:
  * sudo pip install libsbgnpy

*Mimoza* also uses `markup.py <http://markup.sourceforge.net/>`_, `Leaflet <http://leafletjs.com/>`_,
`ChEBI Ontology <http://www.ebi.ac.uk/chebi/>`_, and `the Gene Ontology <http://geneontology.org/>`_,
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

This will produce a `COMBINE archive <http://co.mbine.org/documents/archive>`_, containing:
  * the visualized model (You can see the result in your browser (index.html file inside the COMBINE archive));
  * SBML files with the groups and layout extensions, representing the initial and generalized versions of your model
  and their layout;
  * SBGN representation of your model (if the SBGN bindings are installed, see Dependencies).