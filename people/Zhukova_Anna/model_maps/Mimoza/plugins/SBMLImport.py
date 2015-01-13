from os.path import dirname, abspath
import traceback

from libsbml import SBMLReader
import tulipplugins

from tulip import *
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.generalization.sbml_helper import check_for_groups, SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS
import sbml_vis
from sbml_generalization.utils.obo_ontology import get_chebi, parse


class SBMLImport(tlp.ImportModule):
    def __init__(self, context):
        tlp.ImportModule.__init__(self, context)
        self.addStringParameter("file::filename", "SBML model to import")

    def importGraph(self):
        try:
            sbml_file = self.dataSet["file::filename"]
            reader = SBMLReader()
            input_document = reader.readSBML(sbml_file)
            input_model = input_document.getModel()
            if not check_for_groups(sbml_file, SBO_CHEMICAL_MACROMOLECULE, GROUP_TYPE_UBIQUITOUS):
                m_id = input_model.getId()
                sbml_directory = dirname(abspath(sbml_file))
                groups_sbml = "%s/%s_with_groups.xml" % (sbml_directory, m_id)
                chebi = parse(get_chebi())
                gen_sbml = "%s/%s_generalized.xml" % (sbml_directory, m_id)
                r_id2g_id, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_sps = generalize_model(groups_sbml, gen_sbml,
		                                                                                  sbml_file, chebi,
		                                                                                  cofactors=None,
		                                                                                  verbose=False)
                sbml_file = groups_sbml
                reader = SBMLReader()
                input_document = reader.readSBML(sbml_file)
                input_model = input_document.getModel()
            self.graph = sbml_vis.converter.sbml2tlp.import_sbml(input_model, sbml_file)
            return True
                # this is a workaround to avoid a crash from Tulip when an exception is raised
                # in the import code
        except:
            if self.pluginProgress:
                self.pluginProgress.setError(traceback.format_exc())
            return False  # The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPlugin("SBMLImport", "SBMLImport", "anna", "06/12/2013", "", "1.0")
