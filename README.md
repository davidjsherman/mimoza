# Mimoza

*Mimoza* combines the [model generalization method](http://metamogen.gforge.inria.fr/) with the [zooming user interface (ZUI)](http://en.wikipedia.org/wiki/Zooming_user_interface) paradigm and allows a human expert to explore metabolic network models in a semantically zoomable manner.

## Overview
*Mimoza* takes a metabolic model in [SBML](http://sbml.org/) format, [generalizes](http://metamogen.gforge.inria.fr/) it to detect similar metabolites and similar reactions, and automatically creates a 3-level zoomable map:

*   *the most detailed view* represents the initial network with the generalization-based layout (similar metabolites and reactions are placed next to each other).
*   *the intermediate view* shows the [generalized](http://metamogen.gforge.inria.fr/) versions of reactions and metabolites in each compartment;
*   *the general view* represents the compartments and the transport reactions between them.

The network map can be browsed online or downloaded as a [COMBINE archive](http://co.mbine.org/documents/archive) containing:

*   all the files needed for offline browsing;
*   [SBML](http://sbml.org/) files with the [groups](http://sbml.org/Documents/Specifications/SBML_Level_3/Packages/groups) and [layout](http://sbml.org/Documents/Specifications/SBML_Level_3/Packages/layout) extensions, representing the initial and generalized versions of the model and their layouts;
*   [SBGN](http://www.sbgn.org/) representation of the model.

To learn more about or to cite *Mimoza*, see:
* Zhukova, A., Sherman, D. J. (2015). **Mimoza: Web-Based Semantic Zooming and Navigation in Metabolic Networks.** _BMC Systems Biology_, **9**:10 [doi:10.1186/s12918-015-0151-5](http://identifiers.org/doi/10.1186/s12918-015-0151-5).

*Mimoza* was developed by the [MAGNOME](https://team.inria.fr/magnome/) team at the [Inria Bordeaux](http://www.inria.fr/en/centre/bordeaux) research center. For any questions and comments please contact [zhutchok@gmail.com](mailto:zhutchok@gmail.com).

## Examples
*   the consensus [yeast](http://mimoza.bordeaux.inria.fr/yeast7) network [[Aung _et al._ (2013)](http://dx.doi.org/10.1089/ind.2013.0013)]
*   the genome-scale model of [_Y. lipolytica_](http://mimoza.bordeaux.inria.fr/yali) [[Loira _et al._ (2013)](http://www.biomedcentral.com/1752-0509/6/35)]
*   the consensus [_E. coli_](http://mimoza.bordeaux.inria.fr/ecoli1_2) network [[Smallbone _et al._ (2013)](http://arxiv.org/abs/1304.2960)]

## Acknowledgements
*Mimoza* is powered by [Leaflet](http://leafletjs.com/), [Model generalization library](http://metamogen.gforge.inria.fr/), [ChEBI](http://www.ebi.ac.uk/chebi/), [Tulip](http://tulip.labri.fr/), [GeoJSON](http://geojson.org/), [jQuery](http://jquery.com/), [Python](http://www.python.org/), [libSBML](http://sbml.org/Software/libSBML), [Python API for libSBGN](https://github.com/matthiaskoenig/libsbgn-python), [Codrops](http://www.codrops.com), [IcoMoon](https://icomoon.io), and [PyCharm](http://www.jetbrains.com/pycharm/).