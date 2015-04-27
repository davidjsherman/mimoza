from collections import defaultdict
from itertools import chain

from sbml_generalization.sbml.reaction_filters import get_reactants, get_products


__author__ = 'anna'


def get_vertical_key(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
    ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes = \
        get_key_elements(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids)
    if r.getReversible() and need_to_reverse(
            (ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes,)):
        return ubiquitous_products, ubiquitous_reactants, specific_product_classes, specific_reactant_classes
    return ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes


def need_to_reverse((ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes, )):
    return (ubiquitous_reactants > ubiquitous_products) or (
        not ubiquitous_reactants and not ubiquitous_products and (
            len(specific_reactant_classes) > len(specific_product_classes) or (
                len(specific_reactant_classes) == len(
                    specific_product_classes) and specific_reactant_classes > specific_product_classes)))


def get_r_compartments(model, r):
    return tuple({model.getSpecies(s_id).getCompartment()
                  for s_id in chain((species_ref.getSpecies() for species_ref in r.getListOfReactants()),
                                    (species_ref.getSpecies() for species_ref in r.getListOfProducts()))})


def vk2s_vk(vk):
    (u_rs, u_ps, rs, ps), comps = vk
    s_rs = u_rs, len(rs)
    s_ps = u_ps, len(ps)
    if s_rs > s_ps:
        s_rs, s_ps = s_ps, s_rs
    return s_rs, s_ps, comps


def get_vk2r_ids(model, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
    vk2r = defaultdict(set)
    for r in model.getListOfReactions():
        vk2r[(get_vertical_key(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids),
              get_r_compartments(model, r))].add(
            r.getId())
    return vk2r


def is_reactant(t_id, r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
    ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes = \
        get_key_elements(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids)
    if r.getReversible() and need_to_reverse(
            (ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes,)):
        return t_id in {s_id2term_id[s_id] if s_id in s_id2term_id else s_id for s_id in get_products(r)}
    else:
        return t_id in {s_id2term_id[s_id] if s_id in s_id2term_id else s_id for s_id in get_reactants(r)}


def get_key_elements(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
    reactants, products = get_reactants(r), get_products(r)

    def classify(s_ids):
        specific, ubiquitous = [], []
        for s_id in s_ids:
            if ubiquitous_chebi_ids and s_id in s_id2term_id and s_id2term_id[s_id] in ubiquitous_chebi_ids:
                ubiquitous.append(s_id2term_id[s_id])
            else:
                specific.append(s_id2clu[s_id] if s_id in s_id2clu
                                else (s_id2term_id[s_id] if s_id in s_id2term_id else s_id))
        transform = lambda collection: tuple(sorted(collection))
        return transform(specific), transform(ubiquitous)

    specific_reactant_classes, ubiquitous_reactants = classify(reactants)
    specific_product_classes, ubiquitous_products = classify(products)
    return ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes

