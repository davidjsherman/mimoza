from libsbml import SBMLReader
from sbml_generalization.generalization.sbml_helper import save_as_comp_generalized_sbml, remove_is_a_reactions, \
    remove_unused_elements
from sbml_generalization.utils.logger import log
from sbml_generalization.generalization.mark_ubiquitous import get_cofactors
from sbml_generalization.generalization.model_generalizer import map2chebi, generalize_species, generalize_reactions, \
    EQUIVALENT_TERM_RELATIONSHIPS
from sbml_generalization.utils.annotate_with_chebi import get_species_to_chebi
from sbml_generalization.utils.obo_ontology import filter_ontology


__author__ = 'anna'


def generalize_model(groups_sbml, out_sbml, in_sbml, onto, cofactors=None, verbose=False, log_file=None, ub_s_ids=None):
    # input_model
    input_doc = SBMLReader().readSBML(in_sbml)
    input_model = input_doc.getModel()

    remove_is_a_reactions(input_model)
    remove_unused_elements(input_model)

    log(verbose, "mapping species to ChEBI...")
    if not cofactors:
        cofactors = get_cofactors(onto)
    species_id2chebi_id = get_species_to_chebi(input_model, onto)
    terms = (onto.get_term(t_id) for t_id in species_id2chebi_id.itervalues())
    filter_ontology(onto, terms, relationships=EQUIVALENT_TERM_RELATIONSHIPS, min_deepness=11)
    if not ub_s_ids:
        ubiquitous_chebi_ids = map2chebi(species_id2chebi_id, cofactors, input_model, onto)
        ub_s_ids = {s.getId() for s in input_model.getListOfSpecies() if
                  s.getId() in species_id2chebi_id and species_id2chebi_id[s.getId()] in ubiquitous_chebi_ids}
    else:
        ubiquitous_chebi_ids = {species_id2chebi_id[s_id] for s_id in ub_s_ids if s_id in species_id2chebi_id}

    r_id2g_eq, r_id2ch_id, s_id2gr_id = {}, {}, {}

    # generalize
    s_id2clu = generalize_species(input_model, species_id2chebi_id, ubiquitous_chebi_ids, onto, verbose)
    r_id2clu = generalize_reactions(input_model, s_id2clu, species_id2chebi_id, ubiquitous_chebi_ids)
    r_id2g_eq, s_id2gr_id = save_as_comp_generalized_sbml(input_model, out_sbml, groups_sbml, r_id2clu, s_id2clu,
                                                          ub_s_ids,
                                                          verbose)
    log(verbose, "generalization done...")
    return r_id2g_eq, r_id2ch_id, s_id2gr_id, species_id2chebi_id, ub_s_ids
