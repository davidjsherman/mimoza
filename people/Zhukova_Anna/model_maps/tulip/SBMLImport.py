from tulip import *
import tulipplugins
import traceback
from libsbml import *
from sbml_generalization.generalization.sbml_helper import parse_group_sbml, GrPlError, check_names, check_compartments
from sbml_generalization.utils.compartment_positioner import nest_compartments, get_comp2go, sort_comps
from sbml_generalization.utils.obo_ontology import parse, get_chebi, get_go
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.generalization.reaction_filters import getGeneAssociation
from model_utils import cloneNode

class SBMLImport(tlp.ImportModule):
	def __init__(self, context):
		tlp.ImportModule.__init__(self, context)
		self.addStringParameter("file::filename", "SBML model to import")

	def create_props(self):
		self.graph.getLayoutProperty("viewLayout")
		self.graph.getStringProperty("ancestor_chebi_id")
		self.graph.getStringProperty("ancestor_id")
		self.graph.getStringProperty("ancestor_name")
		self.graph.getStringProperty("chebi_id")
		self.graph.getBooleanProperty("clone")
		self.graph.getStringProperty("compartment")
		self.graph.getStringProperty("real_compartment")
		self.graph.getStringProperty("geneAssociation")
		self.graph.getStringProperty("id")
		self.graph.getStringProperty("name")
		self.graph.getIntegerProperty("nbClones")
		self.graph.getStringProperty("type")
		self.graph.getBooleanProperty("reversible")
		self.graph.getBooleanProperty("ubiquitous")
		self.graph.getColorProperty("viewBorderColor")
		self.graph.getDoubleProperty("viewBorderWidth")
		self.graph.getColorProperty("viewColor")
		self.graph.getStringProperty("viewLabel")
		self.graph.getColorProperty("viewLabelColor")
		self.graph.getBooleanProperty("viewSelection")
		self.graph.getIntegerProperty("viewShape")
		self.graph.getSizeProperty("viewSize")
		self.graph.getIntegerProperty("viewSrcAnchorShape")
		self.graph.getSizeProperty("viewSrcAnchorSize")
		self.graph.getIntegerProperty("viewTgtAnchorShape")
		self.graph.getSizeProperty("viewTgtAnchorSize")
		self.graph.getDoubleProperty("viewRotation")
		self.graph.getDoubleProperty("stoichiometry")


	def duplicate_nodes(self):
		for n in (n for n in self.graph.getNodes() if self.graph["ubiquitous"][n]):
			cloneNode(self.graph, n)


	def clean(self):
		for n in (n for n in self.graph.getNodes() if not self.graph.deg(n)):
			self.graph.delNode(n)


	def mark_ancestors(self, r_eq2clu, r_ch2clu, s2clu):
		id_ = self.graph.getStringProperty("id")
		anc_id = self.graph.getStringProperty("ancestor_id")
		anc_name = self.graph.getStringProperty("ancestor_name")
		anc_ch_id = self.graph.getStringProperty("ancestor_chebi_id")
		type_ = self.graph.getStringProperty("type")
		for n in self.graph.getNodes():
			gr_id, gr_name, term = None, None, None
			if 'reaction' == type_[n]:
				if id_[n] in r_eq2clu:
					gr_id, gr_name = r_eq2clu[id_[n]]
				elif id_[n] in r_ch2clu:
					gr_id, gr_name = r_ch2clu[id_[n]]
					if gr_id in r_eq2clu:
						clu = r_eq2clu[gr_id]
						gr_id += ":" + clu[0]
						gr_name += ":" + clu[1]
			elif id_[n] in s2clu:
				gr_id, gr_name, term = s2clu[id_[n]]
			if gr_name:
				anc_name[n] = gr_name
			if gr_id:
				anc_id[n] = gr_id
			if term:
				anc_ch_id[n] = term.getId()


	def importGraph(self):
		try:
			# get the absolute path to the user selected sbml file
			sbml_file = self.dataSet["file::filename"]
			dot = sbml_file.find(".sbml")
			if dot == -1:
				dot = sbml_file.find(".xml")
			chebi = parse(get_chebi())

			r_id2g_id, r_id2ch_id, s_id2gr_id, ub_sps, species_id2chebi_id = {}, {}, {}, set(), {}
			try:
				r_id2g_id, r_id2ch_id, s_id2gr_id, ub_sps = parse_group_sbml(sbml_file, chebi)
			except GrPlError:
				pass
			if not r_id2g_id and not ub_sps:
				groups_sbml = "{0}_with_groups.xml".format(sbml_file[0:dot] if dot != -1 else sbml_file)
				out_sbml = "{0}_generalized.xml".format(sbml_file[0:dot] if dot != -1 else sbml_file)
				r_id2g_id, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_sps = \
					generalize_model(groups_sbml, out_sbml, sbml_file, chebi, cofactors=None, sh_chains=False,
					                 verbose=False, using_compartments=True)

			# do your custom processing on the sbml file here
			reader = SBMLReader()
			input_document = reader.readSBML(sbml_file)
			input_model = input_document.getModel()
			check_names(input_model)
			check_compartments(input_model)

			onto = parse(get_go())
			comp_go = get_comp2go(input_model, onto)
			part2org, cyto, others = sort_comps(onto, comp_go)

			r_c2c = {}
			cytoplasm = input_model.getCompartment(list(cyto)[0]).getName() if cyto else 'cytoplasm'
			extracellular = 'extracellular'
			organelles = set()

			def get_comp(c_id):
				if c_id in r_c2c:
					return r_c2c[c_id]
				if c_id in part2org:
					c = input_model.getCompartment(part2org[c_id]).getName()
					organelles.add(c)
				elif c_id in others:
					c = cytoplasm
				else:
					c = extracellular
				r_c2c[c_id] = c
				return c

			def get_r_comp(all_comps):
				if len(all_comps) == 1:
					return all_comps.pop()
				if extracellular in all_comps:
					return extracellular
				return cytoplasm

			dark_gray = tlp.Color(100, 100, 100)
			light_red = tlp.Color(255, 100, 100)
			light_blue = tlp.Color(100, 100, 255)
			self.graph.setName(input_model.getId())
			self.create_props()
			id2n = {}
			for s in input_model.getListOfSpecies():
				n = self.graph.addNode()
				comp = input_model.getCompartment(s.getCompartment())
				self.graph["real_compartment"][n] = '{0}, {1}, {2}'.format(comp.getName(), comp.getId(),
				                                                           comp_go[comp.getId()])
				self.graph["compartment"][n] = get_comp(comp.getId())

				_id = s.getId()
				self.graph["id"][n] = _id
				id2n[_id] = n
				name = s.getName()
				self.graph["name"][n] = name
				self.graph["type"][n] = 'species'

				ub = _id in ub_sps
				self.graph["ubiquitous"][n] = ub
				if _id in species_id2chebi_id:
					self.graph["chebi_id"][n] = species_id2chebi_id[_id]

				self.graph["viewShape"][n] = 14
				self.graph["viewColor"][n] = dark_gray if ub else light_red
				self.graph["viewSize"][n] = tlp.Size(2, 2, 2) if ub else tlp.Size(3, 3, 3)
				
				indx = name.find("[{0}]".format(comp.getName()))
				if indx != -1: 
					name = name[:indx]
				self.graph["viewLabel"][n] = name

			get_sp_comp = lambda _id: self.graph["compartment"][id2n[_id]]
			arrowShape = 50
			for r in input_model.getListOfReactions():
				name = r.getName()
				# do not add fake isa reactions
				if name.find("isa ") != -1 and 1 == r.getNumReactants() == r.getNumProducts() \
					and get_sp_comp(r.getListOfReactants().get(0).getSpecies()) == get_sp_comp(
								r.getListOfProducts().get(0).getSpecies()):
					continue

				n = self.graph.addNode()
				self.graph["geneAssociation"][n] = getGeneAssociation(r)
				self.graph["id"][n] = r.getId()
				self.graph["name"][n] = name
				self.graph["type"][n] = 'reaction'
				self.graph["reversible"][n] = r.getReversible()

				self.graph["viewShape"][n] = 7
				self.graph["viewColor"][n] = light_blue
				self.graph["viewSize"][n] = tlp.Size(2, 2, 2)
				self.graph["viewLabel"][n] = name

				all_comps = set()
				for spRef in r.getListOfReactants():
					_id = spRef.getSpecies()
					all_comps.add(get_sp_comp(_id))
					e = self.graph.addEdge(id2n[_id], n)
					self.graph["viewSrcAnchorShape"][e] = arrowShape if r.getReversible() else -1
					self.graph["viewTgtAnchorShape"][e] = -1 if r.getReversible() else arrowShape
					self.graph["viewColor"][e] = dark_gray if _id in ub_sps else light_blue
					st = spRef.getStoichiometry()
					if not st:
						st = spRef.getStoichiometryMath()
					if not st:
						st = 1
					self.graph["stoichiometry"][e] = st
					self.graph["name"][e] = input_model.getSpecies(_id).getName()

				for spRef in r.getListOfProducts():
					_id = spRef.getSpecies()
					all_comps.add(get_sp_comp(_id))
					e = self.graph.addEdge(n, id2n[_id])
					self.graph["viewSrcAnchorShape"][e] = arrowShape
					self.graph["viewTgtAnchorShape"][e] = -1
					self.graph["viewColor"][e] = dark_gray if _id in ub_sps else light_blue
					st = spRef.getStoichiometry()
					if not st:
						st = spRef.getStoichiometryMath()
					if not st:
						st = 1
					self.graph["stoichiometry"][e] = st
					self.graph["name"][e] = input_model.getSpecies(_id).getName()

				self.graph["compartment"][n] = get_r_comp(all_comps)

			self.graph.setAttribute("organelles", ";".join(organelles))
			self.graph.setAttribute("cytoplasm", cytoplasm)

			self.duplicate_nodes()
			self.clean()

			self.mark_ancestors(r_id2g_id, r_id2ch_id, s_id2gr_id)

			return True
		# this is a workaround to avoid a crash from Tulip when an exception is raised
		# in the import code
		except:
			if self.pluginProgress:
				self.pluginProgress.setError(traceback.format_exc())
			return False


# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPlugin("SBMLImport", "SBMLImport", "anna", "06/12/2013", "", "1.0")
