from libsbml import SBMLReader
from tulip import *
from sbml_generalization.generalization.sbml_helper import parse_group_sbml, GrPlError, check_names, check_compartments
from sbml_generalization.utils.compartment_positioner import get_comp2go, sort_comps
from sbml_generalization.utils.obo_ontology import parse, get_chebi, get_go
from sbml_generalization.generalization.sbml_generalizer import generalize_model
from sbml_generalization.generalization.model_generalizer import map2chebi
from sbml_generalization.generalization.reaction_filters import getGeneAssociation
from sbml_generalization.generalization.mark_ubiquitous import getCofactors
from modules.model_utils import cloneNode

__author__ = 'anna'

arrowShape = 50


def process_generalized_entities(chebi, input_model, sbml_file):
	r_id2g_id, r_id2ch_id, s_id2gr_id, ub_sps, species_id2chebi_id = {}, {}, {}, set(), {}
	try:
		r_id2g_id, r_id2ch_id, s_id2gr_id, ub_sps = parse_group_sbml(sbml_file, chebi)
		cofactors = getCofactors(chebi)
		species_id2chebi_id, ubiquitous_chebi_ids = map2chebi(cofactors, input_model, chebi)
	except GrPlError:
		pass
	if not r_id2g_id and not ub_sps:
		dot = sbml_file.find(".sbml")
		if dot == -1:
			dot = sbml_file.find(".xml")
		groups_sbml = "{0}_with_groups.xml".format(sbml_file[0:dot] if dot != -1 else sbml_file)
		out_sbml = "{0}_generalized.xml".format(sbml_file[0:dot] if dot != -1 else sbml_file)
		r_id2g_id, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_sps = generalize_model(groups_sbml, out_sbml,
		                                                                                  sbml_file, chebi,
		                                                                                  cofactors=None,
		                                                                                  sh_chains=False,
		                                                                                  verbose=True)

	return r_id2ch_id, r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps


def species2nodes(comp2go_term, get_comp, graph, input_model, species_id2chebi_id, ub_sps):
	id2n = {}
	for s in input_model.getListOfSpecies():
		n = graph.addNode()
		comp = input_model.getCompartment(s.getCompartment())
		graph["real_compartment"][n] = '{0}, {1}, {2}'.format(comp.getName(), comp.getId(),
		                                                      comp2go_term[comp.getId()])
		graph["compartment"][n] = get_comp(comp.getId())

		_id = s.getId()
		graph["id"][n] = _id
		id2n[_id] = n
		name = s.getName()
		graph["name"][n] = name
		graph["type"][n] = 'species'

		ub = _id in ub_sps
		graph["ubiquitous"][n] = ub
		if _id in species_id2chebi_id:
			graph["chebi_id"][n] = species_id2chebi_id[_id]

		graph["viewShape"][n] = 14
		#graph["viewColor"][n] = dark_gray if ub else light_red
		graph["viewSize"][n] = tlp.Size(2, 2, 2) if ub else tlp.Size(3, 3, 3)

		indx = name.find("[{0}]".format(comp.getName()))
		if indx != -1:
			name = name[:indx]
		graph["viewLabel"][n] = name
	return id2n


def reactions2nodes(get_r_comp, graph, id2n, input_model, ub_sps):
	get_sp_comp = lambda _id: graph["compartment"][id2n[_id]]
	for r in input_model.getListOfReactions():
		name = r.getName()
		# do not add fake isa reactions
		if name.find("isa ") != -1 and 1 == r.getNumReactants() == r.getNumProducts() \
			and get_sp_comp(r.getListOfReactants().get(0).getSpecies()) == get_sp_comp(
						r.getListOfProducts().get(0).getSpecies()):
			continue

		n = graph.addNode()
		graph["geneAssociation"][n] = getGeneAssociation(r)
		graph["id"][n] = r.getId()
		graph["name"][n] = name
		graph["type"][n] = 'reaction'
		graph["reversible"][n] = r.getReversible()

		graph["viewShape"][n] = 7
		#graph["viewColor"][n] = light_blue
		graph["viewSize"][n] = tlp.Size(2, 2, 2)
		graph["viewLabel"][n] = name

		all_comps = set()
		for spRef in r.getListOfReactants():
			_id = spRef.getSpecies()
			all_comps.add(get_sp_comp(_id))
			e = graph.addEdge(id2n[_id], n)
			graph["viewSrcAnchorShape"][e] = arrowShape if r.getReversible() else -1
			graph["viewTgtAnchorShape"][e] = -1 if r.getReversible() else arrowShape
			#graph["viewColor"][e] = dark_gray if _id in ub_sps else light_blue
			st = spRef.getStoichiometry()
			if not st:
				st = spRef.getStoichiometryMath()
			if not st:
				st = 1
			graph["stoichiometry"][e] = st
			graph["name"][e] = input_model.getSpecies(_id).getName()

		for spRef in r.getListOfProducts():
			_id = spRef.getSpecies()
			all_comps.add(get_sp_comp(_id))
			e = graph.addEdge(n, id2n[_id])
			graph["viewSrcAnchorShape"][e] = arrowShape
			graph["viewTgtAnchorShape"][e] = -1
			#graph["viewColor"][e] = dark_gray if _id in ub_sps else light_blue
			st = spRef.getStoichiometry()
			if not st:
				st = spRef.getStoichiometryMath()
			if not st:
				st = 1
			graph["stoichiometry"][e] = st
			graph["name"][e] = input_model.getSpecies(_id).getName()

		graph["compartment"][n] = get_r_comp(all_comps)


def import_sbml(graph, input_model, sbml_file):
	chebi = parse(get_chebi())

	r_id2ch_id, r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps = process_generalized_entities(chebi,
	                                                                                              input_model,
	                                                                                              sbml_file)
	check_names(input_model)
	check_compartments(input_model)

	onto = parse(get_go())
	comp2go_term = get_comp2go(input_model, onto)
	part2org, cyto, others = sort_comps(onto, comp2go_term)

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

	graph.setName(input_model.getId())
	create_props(graph)
	id2n = species2nodes(comp2go_term, get_comp, graph, input_model, species_id2chebi_id, ub_sps)

	reactions2nodes(get_r_comp, graph, id2n, input_model, ub_sps)

	graph.setAttribute("organelles", ";".join(organelles))
	graph.setAttribute("cytoplasm", cytoplasm)

	duplicate_nodes(graph)
	clean(graph)

	mark_ancestors(graph, r_id2g_id, r_id2ch_id, s_id2gr_id)
	return graph


def create_props(graph):
	graph.getLayoutProperty("viewLayout")
	graph.getStringProperty("ancestor_chebi_id")
	graph.getStringProperty("ancestor_id")
	graph.getStringProperty("ancestor_name")
	graph.getStringProperty("chebi_id")
	graph.getBooleanProperty("clone")
	graph.getStringProperty("compartment")
	graph.getStringProperty("real_compartment")
	graph.getStringProperty("geneAssociation")
	graph.getStringProperty("id")
	graph.getStringProperty("name")
	graph.getIntegerProperty("nbClones")
	graph.getStringProperty("type")
	graph.getBooleanProperty("reversible")
	graph.getBooleanProperty("ubiquitous")
	graph.getColorProperty("viewBorderColor")
	graph.getDoubleProperty("viewBorderWidth")
	graph.getColorProperty("viewColor")
	graph.getStringProperty("viewLabel")
	graph.getColorProperty("viewLabelColor")
	graph.getBooleanProperty("viewSelection")
	graph.getIntegerProperty("viewShape")
	graph.getSizeProperty("viewSize")
	graph.getIntegerProperty("viewSrcAnchorShape")
	graph.getSizeProperty("viewSrcAnchorSize")
	graph.getIntegerProperty("viewTgtAnchorShape")
	graph.getSizeProperty("viewTgtAnchorSize")
	graph.getDoubleProperty("viewRotation")
	graph.getDoubleProperty("stoichiometry")


def duplicate_nodes(graph):
	for n in (n for n in graph.getNodes() if graph["ubiquitous"][n]):
		cloneNode(graph, n)


def clean(graph):
	for n in (n for n in graph.getNodes() if not graph.deg(n)):
		graph.delNode(n)


def mark_ancestors(graph, r_eq2clu, r_ch2clu, s2clu):
	id_ = graph.getStringProperty("id")
	anc_id = graph.getStringProperty("ancestor_id")
	anc_name = graph.getStringProperty("ancestor_name")
	anc_ch_id = graph.getStringProperty("ancestor_chebi_id")
	type_ = graph.getStringProperty("type")
	for n in graph.getNodes():
		gr_id, gr_name, term = None, None, None
		if 'reaction' == type_[n]:
			if id_[n] in r_eq2clu:
				gr_id, gr_name = r_eq2clu[id_[n]]
			# elif id_[n] in r_ch2clu:
			# 	gr_id, gr_name = r_ch2clu[id_[n]]
			# 	if gr_id in r_eq2clu:
			# 		clu = r_eq2clu[gr_id]
			# 		gr_id += ":" + clu[0]
			# 		gr_name += ":" + clu[1]
		elif id_[n] in s2clu:
			gr_id, term = s2clu[id_[n]]
			if term:
				gr_name = term.getName()
		if gr_name:
			anc_name[n] = gr_name
		if gr_id:
			anc_id[n] = gr_id
		if term:
			anc_ch_id[n] = term.getId()

