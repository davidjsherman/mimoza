from sbml_generalization.generalization.reaction_filters import getReactants, getProducts

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


def is_reactant(t_id, r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids, model):
	ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes = \
		get_key_elements(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids)
	if r.getReversible() and need_to_reverse(
			(ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes,)):
		return t_id in {(s_id2term_id[s_id] if s_id in s_id2term_id else s_id, model.getSpecies(s_id).getCompartment()) for s_id in getProducts(r)}
	else:
		return t_id in {(s_id2term_id[s_id] if s_id in s_id2term_id else s_id, model.getSpecies(s_id).getCompartment()) for s_id in getReactants(r)}


def get_key_elements(r, s_id2clu, s_id2term_id, ubiquitous_chebi_ids):
	reactants, products = getReactants(r), getProducts(r)

	def classify(s_ids):
		specific, ubiquitous = [], []
		for s_id in s_ids:
			if not s_id in s_id2term_id:
				specific.append(s_id)
			else:
				t_id = s_id2term_id[s_id]
				if t_id in ubiquitous_chebi_ids:
					ubiquitous.append(t_id)
				elif s_id in s_id2clu:
					specific.append(s_id2clu[s_id])
				else:
					specific.append(s_id)
		transform = lambda collection: tuple(sorted(collection))
		return transform(specific), transform(ubiquitous)

	specific_reactant_classes, ubiquitous_reactants = classify(reactants)
	specific_product_classes, ubiquitous_products = classify(products)
	return ubiquitous_reactants, ubiquitous_products, specific_reactant_classes, specific_product_classes

