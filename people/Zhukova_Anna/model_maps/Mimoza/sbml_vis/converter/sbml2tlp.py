import logging
from tulip import tlp

from sbml_generalization.sbml.sbml_helper import check_names, check_compartments, parse_group_sbml, GrPlError
from sbml_generalization.sbml.compartment.compartment_positioner import get_comp2go, comp2level
from mod_sbml.onto import parse_simple
from mod_sbml.onto.term import Term
from mod_sbml.annotation.chebi.chebi_serializer import get_chebi
from mod_sbml.annotation.gene_ontology.go_serializer import get_go
from mod_sbml.sbml.sbml_manager import get_gene_association
from mod_sbml.annotation.chebi.chebi_annotator import get_species_to_chebi
from sbml_vis.graph.node_cloner import clone_node
from sbml_vis.graph.graph_properties import *
from sbml_vis.graph.resize import get_n_size

__author__ = 'anna'

SKIP_UBS = False


def get_short_name(name, ch_id, onto, comp_name):
    short_name = name

    # remove compartment from the name,
    # e.g. H2O [peroxisome] --> H2O
    if comp_name:
        short_name.replace("[%s]" % comp_name, '').strip()

    # replace with a chebi name
    # if it is shorter
    if ch_id:
        term = onto.get_term(ch_id)
        if term:
            alts = [term.get_name()]
            # alts.extend(term.get_synonyms())
            if not short_name:
                short_name = term.get_name()
            for alt in alts:
                if alt and len(alt) < len(short_name):
                    short_name = alt
    return short_name


def species2nodes(graph, input_model, species_id2chebi_id, ub_sps, chebi=None):
    id2n = {}
    for s in input_model.getListOfSpecies():
        _id = s.getId()
        ub = (_id in ub_sps)

        # todo
        if SKIP_UBS and ub:
            continue

        n = graph.addNode()
        comp = input_model.getCompartment(s.getCompartment())
        graph[COMPARTMENT_ID][n] = comp.getId()
        graph[ID][n] = _id
        id2n[_id] = n
        chebi_id = None

        if _id in species_id2chebi_id:
            chebi_id = species_id2chebi_id[_id]
            graph[TERM][n] = chebi_id
        name = s.getName()
        if chebi:
            name = get_short_name(name, chebi_id, chebi, comp.getName())
        graph[NAME][n] = name
        graph[TYPE][n] = TYPE_SPECIES
        graph[UBIQUITOUS][n] = ub
        graph[VIEW_SHAPE][n] = SPECIES_SHAPE
        graph[VIEW_SIZE][n] = get_n_size(graph, n)
    return id2n


def reactions2nodes(get_r_comp, graph, id2n, input_model):
    # get_sp_comp = lambda _id: graph[COMPARTMENT][id2n[_id]]
    get_sp_comp = lambda _id: input_model.getSpecies(_id).getCompartment()

    def link_reaction_to_species(reaction_node, sp_ref, all_comps, is_reactant=True, reversible=False):
        s_id = sp_ref.getSpecies()

        all_comps.add(get_sp_comp(s_id))

        # todo:
        if SKIP_UBS and s_id not in id2n:
            return
        species_node = id2n[s_id]
        e = graph.addEdge(species_node, reaction_node) if is_reactant else graph.addEdge(reaction_node, species_node)
        stoich = sp_ref.getStoichiometry()
        if not stoich:
            stoich = sp_ref.getStoichiometryMath()
        if not stoich:
            stoich = 1
        graph[STOICHIOMETRY][e] = stoich
        graph[NAME][e] = input_model.getSpecies(s_id).getName()
        ub = graph[UBIQUITOUS][species_node]
        graph[UBIQUITOUS][e] = ub
        graph[REVERSIBLE][e] = reversible and not ub

    for r in input_model.getListOfReactions():
        name = r.getName()
        # do not add fake isa reactions
        # if name.find("isa ") != -1 and 1 == r.getNumReactants() == r.getNumProducts() and get_sp_comp(
        # r.getListOfReactants().get(0).getSpecies()) == get_sp_comp(
        # 		r.getListOfProducts().get(0).getSpecies()):
        # 	continue

        n = graph.addNode()
        graph[TERM][n] = get_gene_association(r)
        graph[ID][n] = r.getId()
        graph[NAME][n] = name
        graph[TYPE][n] = TYPE_REACTION
        graph[REVERSIBLE][n] = r.getReversible()

        graph[VIEW_SHAPE][n] = REACTION_SHAPE
        graph[VIEW_SIZE][n] = get_n_size(graph, n)

        all_comps = set()
        for sp_ref in r.getListOfReactants():
            link_reaction_to_species(n, sp_ref, all_comps, is_reactant=True, reversible=r.getReversible())
        for sp_ref in r.getListOfProducts():
            link_reaction_to_species(n, sp_ref, all_comps, is_reactant=False, reversible=r.getReversible())

        graph[TRANSPORT][n] = len(all_comps) > 1
        graph[COMPARTMENT_ID][n] = get_r_comp(all_comps)


def get_quotient_maps(chebi, input_model, sbml_file):
    try:
        r_id2g_id, s_id2gr_id, ub_sps = parse_group_sbml(sbml_file, chebi)
        species_id2chebi_id = get_species_to_chebi(input_model, chebi, False) if (r_id2g_id or ub_sps) else {}
        return r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps
    except GrPlError as e:
        logging.error("Could not parse the groups SBML %s: %s" % (sbml_file, e.msg))
        return None, None, None, None


def compute_c_id2info(c_id2level, comp2go_term, input_model):
    c_id2info = {}
    for comp in input_model.getListOfCompartments():
        c_id = comp.getId()
        c_name = comp.getName()
        if not c_name:
            c_name = c_id
        c_id2info[c_id] = (c_name, comp2go_term[c_id] if c_id in comp2go_term else None, c_id2level[c_id])

    c_id2outs = {}
    for c_id in c_id2info.iterkeys():
        _, _, (_, out_c_id) = c_id2info[c_id]
        outs = []
        while out_c_id:
            outs.append(out_c_id)
            _, _, (_, out_c_id) = c_id2info[out_c_id]
        c_id2outs[c_id] = outs

    return c_id2info, c_id2outs


def import_sbml(input_model, sbml_file):
    logging.info('parsing ChEBI')
    chebi = parse_simple(get_chebi())

    logging.info('reading generalized model from %s' % sbml_file)
    r_id2g_id, s_id2gr_id, species_id2chebi_id, ub_sps = get_quotient_maps(chebi, input_model, sbml_file)

    logging.info('fixing labels and compartments')
    check_names(input_model)
    check_compartments(input_model)

    logging.info('annotating with GO')
    go = parse_simple(get_go())
    comp2go_term = get_comp2go(input_model, go)
    c_id2level = comp2level(input_model, go)
    c_id2info, c_id2outs = compute_c_id2info(c_id2level, comp2go_term, input_model)

    def get_r_comp(all_comp_ids):
        if len(all_comp_ids) == 1:
            return all_comp_ids.pop()
        get_level = lambda c_id: c_id2level[c_id][0]
        outer_most = min(all_comp_ids, key=get_level)
        inner_most = max(all_comp_ids, key=get_level)
        outer_level, inner_level = get_level(outer_most), get_level(inner_most)
        if outer_level == inner_level or (not outer_most in c_id2outs[inner_most]):
            return max(set(c_id2outs[inner_most]) & set(c_id2outs[outer_most]), key=get_level)
        if inner_level - outer_level > 1:
            return max(c_id2outs[inner_most], key=get_level)
        return outer_most

    logging.info('initialising the graph')
    graph = tlp.newGraph()
    graph.setName(input_model.getId())
    create_props(graph)

    logging.info('adding species nodes')
    id2n = species2nodes(graph, input_model, species_id2chebi_id, ub_sps, chebi)

    logging.info('adding reaction nodes')
    reactions2nodes(get_r_comp, graph, id2n, input_model)

    # for n in (n for n in graph.getNodes() if TYPE_SPECIES == graph[TYPE][n] and graph.deg(n) > 5 \
    # and not graph[ID][n] in s_id2gr_id):
    # 	graph[UBIQUITOUS][n] = True

    logging.info('duplicating nodes')
    duplicate_nodes(graph)

    logging.info('marking species/reaction groups')
    mark_ancestors(graph, r_id2g_id, s_id2gr_id, c_id2info)
    return graph, c_id2info, c_id2outs, chebi, ub_sps


def create_props(graph):
    graph.getStringProperty(ANCESTOR_TERM)
    graph.getStringProperty(ANCESTOR_ID)
    graph.getStringProperty(ANCESTOR_NAME)

    graph.getStringProperty(TERM)

    graph.getStringProperty(COMPARTMENT_ID)

    graph.getStringProperty(ID)
    graph.getStringProperty(NAME)

    graph.getIntegerProperty(TYPE)

    graph.getBooleanProperty(REVERSIBLE)
    graph.getDoubleProperty(STOICHIOMETRY)
    graph.getBooleanProperty(TRANSPORT)

    graph.getBooleanProperty(UBIQUITOUS)

    graph.getLayoutProperty(VIEW_LAYOUT)
    graph.getIntegerProperty(VIEW_SHAPE)
    graph.getSizeProperty(VIEW_SIZE)

    graph.getBooleanProperty(FAKE)

    graph.getStringProperty(CLONE_ID)

    graph.getStringVectorProperty(RELATED_COMPARTMENT_IDS)


def duplicate_nodes(graph):
    root = graph.getRoot()
    duplicate_ub_nodes(graph, root)
    # duplicate_tr_nodes(graph, root)


def duplicate_tr_nodes(graph, root):
    for n in (n for n in graph.getNodes() if TYPE_SPECIES == root[TYPE][n] and not root.isMetaNode(n) and
            not root[UBIQUITOUS][n] and next((r for r in root.getInOutNodes(n) if root[TRANSPORT][r]), False)):
        clone_node(graph, n, get_neighbour_nodes=lambda m, gr: (t for t in gr.getInOutNodes(m) if gr[TRANSPORT][t]))


def duplicate_ub_nodes(graph, root):
    for n in (n for n in graph.getNodes() if root[UBIQUITOUS][n]):
        clone_node(graph, n)


def mark_ancestors(graph, r_eq2clu, s2clu, c_id2info):
    root = graph.getRoot()
    id_ = root.getStringProperty(ID)
    anc_id = root.getStringProperty(ANCESTOR_ID)
    anc_name = root.getStringProperty(ANCESTOR_NAME)
    anc_ch_id = root.getStringProperty(ANCESTOR_TERM)
    type_ = root.getIntegerProperty(TYPE)
    for n in graph.getNodes():
        gr_id, gr_name, term = None, None, None
        if TYPE_REACTION == type_[n]:
            if id_[n] in r_eq2clu:
                gr_id, gr_name, el_num = r_eq2clu[id_[n]]
                gr_name = "%s (%d)" % (gr_name, el_num)
        elif id_[n] in s2clu:
            gr_id, term, el_num = s2clu[id_[n]]
            if term:
                if isinstance(term, Term):
                    gr_name = term.get_name()
                else:
                    gr_name = term
                    term = None
                c_name, _, _ = c_id2info[root[COMPARTMENT_ID][n]]
                gr_name = "%s (%d) [%s]" % (gr_name, el_num, c_name)
        if gr_name:
            anc_name[n] = gr_name
        if gr_id:
            anc_id[n] = gr_id
        if term:
            anc_ch_id[n] = term.get_id()

