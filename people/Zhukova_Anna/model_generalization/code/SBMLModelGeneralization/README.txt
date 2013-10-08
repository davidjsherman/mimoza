* About Model Generalization *

Model Generalization is a python library that provides a higher-level view of a metabolic model, by masking inessential details while preserving its essential structure. 

It groups biochemical species in the model into semantically equivalent classes and generalizes them into their common parent in the ChEBI (http://www.ebi.ac.uk/chebi/) ontology. The reactions between the same generalized species are factored together into generalized reactions.

Model generalization takes a model in SBML (http://sbml.org/) format as input, and produces a generalized SBML model as output.

* TO RUN Model Generalization *

- Model Generalization uses libSBML library.
To install libSBML, please visit: http://sbml.org/Software/libSBML/docs/python-api/libsbml-installation.html . You might need to install it from the source files, at http://sourceforge.net/projects/sbml/files/libsbml/5.8.0/stable/libSBML-5.8.0-src.zip/download . In this case, please make sure you have the 

	libxml2-dev 
	xml2 
	libxml2 

libraries installed. Then, build and install libsbml for python:

	./configure --with-python
	make
	make install

- Open the Makefile and specify the path to the model to be generalized in the MODEL variable

- Type (in terminal): make 

- The script will produce a new SBML file, containing the generalized model, named <your-model's-filename>_generalized.xml
