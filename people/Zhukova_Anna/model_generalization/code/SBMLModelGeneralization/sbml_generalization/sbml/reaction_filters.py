__author__ = 'anna'

GENE_ASSOCIATION_PREFIX = 'GENE_ASSOCIATION:'
PATHWAY_ASSOCIATION_PREFIX = 'SUBSYSTEM:'
EC_ASSOCIATION_PREFIX = "PROTEIN_CLASS:"
FORMULA_PREFIX = "FORMULA:"


def get_formula(species):
    result = set()
    node = species.getNotes()
    _get_prefixed_notes_value(node, result, FORMULA_PREFIX)
    return result


# -------------------------REACTION-FILTERS-----------------------------


# by genes
def matches_genes(gene_collection, reaction):
    genes = get_genes(reaction)
    return set(genes) & set(gene_collection)


# by pathway
def matches_pathway(pathway_name, reaction):
    if not pathway_name:
        return False
    pathway_name = pathway_name.lower()
    pathways = get_pathway_expression(reaction)
    for pathway in pathways:
        if pathway and pathway.lower().find(pathway_name) != -1:
            return True
    return False


# by reaction attributes
def matches_ids(id_collection, reaction):
    return reaction.getId() in id_collection


def matches_name(name, reaction):
    if not name:
        return False
    name = name.lower()
    r_name = reaction.getName()
    return r_name and r_name.lower().find(name) != -1


# by compartment
def matches_compartment_id_weakly(compartment_ids, reaction, model):
    for speciesId in get_participants(reaction):
        species = model.getSpecies(speciesId)
        if compartment_ids == species.getCompartment():
            return True
    return False


def matches_compartment_id(compartment_ids, reaction, model):
    for species_id in get_participants(reaction):
        species = model.getSpecies(species_id)
        if not (species.getCompartment() in compartment_ids):
            return False
    return True


def matches_compartment_name_weakly(comp_name, reaction, model):
    if not comp_name:
        return False
    comp_name = comp_name.lower()
    for speciesId in get_participants(reaction):
        species = model.getSpecies(speciesId)
        compartment_id = species.getCompartment()
        if not compartment_id:
            continue
        compartment = model.getCompartment(compartment_id)
        if not compartment:
            continue
        compartment_name = compartment.getName()
        if compartment_name and compartment_name.lower().find(comp_name) != -1:
            return True
    return False


def matches_compartment_name(comp_name, reaction, model):
    if not comp_name:
        return False
    comp_name = comp_name.lower()
    for speciesId in get_participants(reaction):
        species = model.getSpecies(speciesId)
        compartment_id = species.getCompartment()
        if not compartment_id:
            return False
        compartment = model.getCompartment(compartment_id)
        if not compartment:
            return False
        compartment_name = compartment.getName()
        if not compartment_name or compartment_name.lower().find(comp_name) == -1:
            return False
    return True


def is_not_transport(reaction, model):
    c_id = None
    participants = get_reactants(reaction) | get_products(reaction)
    for speciesId in participants:
        species = model.getSpecies(speciesId)
        compartment_id = species.getCompartment()
        if not compartment_id:
            return False
        if not c_id:
            c_id = compartment_id
        if compartment_id != c_id:
            return False
    return True


# by species
def matches_species_id(species_ids, reaction):
    return set(species_ids) & set(get_participants(reaction))


def matches_species_name(name, reaction, model):
    if not name:
        return False
    name = name.lower()
    for speciesId in get_participants(reaction):
        species = model.getSpecies(speciesId)
        if not species:
            continue
        species_name = species.getName()
        if species_name and species_name.lower().find(name) != -1:
            return True
    return False


def matches_reactant_id(s_id, reaction):
    return s_id in get_reactants(reaction)


def matches_product_id(s_id, reaction):
    return s_id in get_products(reaction)


def matches_modifier_id(s_id, reaction):
    return s_id in get_modifiers(reaction)


def matches_reactant_product_pair(reaction, s_id1, s_id2):
    reactants = get_reactants(reaction)
    products = get_products(reaction)
    if s_id1 in reactants:
        return s_id2 in products
    elif s_id2 in reactants:
        return s_id1 in products
    return False


# -------------------------REACTION-INFO-----------------------------


def get_genes(reaction):
    return gene_association2genes(get_gene_association(reaction))


def gene_association2genes(gene_association):
    genes = []
    if gene_association:
        for g0 in gene_association.split('('):
            for g1 in g0.split(')'):
                for g2 in g1.split('and'):
                    for g3 in g2.split('or'):
                        for g4 in g3.split('xor'):
                            for g5 in g4.split('not'):
                                g5 = g5.replace(' ', '')
                                if g5:
                                    genes.append(g5)
    genes.sort()
    return genes


def get_gene_association(reaction):
    result = set()
    node = reaction.getNotes()
    _get_prefixed_notes_value(node, result, GENE_ASSOCIATION_PREFIX)
    return " or ".join(result)


def get_pathway_expression(reaction):
    result = set()
    node = reaction.getNotes()
    _get_prefixed_notes_value(node, result, PATHWAY_ASSOCIATION_PREFIX)
    return result


def get_ec_numbers(reaction):
    result = set()
    node = reaction.getNotes()
    _get_prefixed_notes_value(node, result, EC_ASSOCIATION_PREFIX)
    return result


def get_participants(reaction):
    result = get_reactants(reaction)
    result |= get_products(reaction)
    result |= get_modifiers(reaction)
    return result


def get_stoichiometry(species_ref):
    result = species_ref.getStoichiometry()
    if not result:
        result = species_ref.getStoichiometryMath()
    if not result:
        return 1
    return result


def get_reactants(reaction, stoichiometry=False):
    if stoichiometry:
        return {(species_ref.getSpecies(), get_stoichiometry(species_ref)) for species_ref in
                reaction.getListOfReactants()}
    else:
        return {species_ref.getSpecies() for species_ref in reaction.getListOfReactants()}


def get_products(reaction, stoichiometry=False):
    if stoichiometry:
        return {(species_ref.getSpecies(), get_stoichiometry(species_ref)) for species_ref in
                reaction.getListOfProducts()}
    else:
        return {species_ref.getSpecies() for species_ref in reaction.getListOfProducts()}


def get_modifiers(reaction):
    return {species_ref.getSpecies() for species_ref in reaction.getListOfModifiers()}


def _get_prefixed_notes_value(notes, result, prefix):
    if not notes:
        return
    for i in xrange(0, notes.getNumChildren()):
        child = notes.getChild(i)
        note = child.getCharacters()
        if note:
            start = note.find(prefix)
            if start != -1:
                start += len(prefix)
                result.add(note[start:len(note)].strip())
        _get_prefixed_notes_value(child, result, prefix)


def get_r_formula(model, r):
    format_m = lambda m_id, st: "%s%s(%s)" % ("%g " % st if st != 1 else "", model.getSpecies(m_id).getName(), m_id)
    formula = " + ".join([format_m(m_id, st) for (m_id, st) in sorted(get_reactants(r, True), key=lambda (m_id, st): m_id)]) + \
              (" <=> " if r.getReversible() else "=>") + \
              " + ".join([format_m(m_id, st) for (m_id, st) in sorted(get_products(r, True), key=lambda (m_id, st): m_id)])
    return formula


# ----------------------INFIX-TO-POSTFIX-NOTATION-CONVERSION--------------------------

_is_operator = lambda s: s in ['&', '|']
_is_parentheses = lambda s: s in ['(', ')']
_is_empty = lambda s: s is ' '
_is_operand = lambda s: not _is_operator(s) and not _is_parentheses(s) and not _is_empty(s)


def infix2postfix(s):
    operator_hierarchy = lambda op: 1 if op is '&' else (0 if op is '|' else -1)
    s = s.replace(' and ', ' & ').replace(' or ', ' | ')
    operand_stack = []
    operator_stack = []
    i = 0
    while i < len(s):
        token, i = _next_token(s, i)
        if _is_operand(token):
            operand_stack.append(token)
        elif token is '(' or not operator_stack \
                or operator_hierarchy(token) > operator_hierarchy(operator_stack[len(operator_stack) - 1]):
            operator_stack.append(token)
        elif token is ')':
            operator = operator_stack.pop()
            while operator is not '(':
                right = operand_stack.pop()
                left = operand_stack.pop()
                operand = [operator, left, right]
                operand_stack.append(operand)
                operator = operator_stack.pop()
        else:
            while operand_stack and operator_stack \
                    and operator_hierarchy(token) <= operator_hierarchy(operator_stack[len(operator_stack) - 1]):
                operator = operator_stack.pop()
                right = operand_stack.pop()
                left = operand_stack.pop()
                operand = [operator, left, right]
                operand_stack.append(operand)
            operator_stack.append(token)
    while operator_stack:
        operator = operator_stack.pop()
        right = operand_stack.pop()
        left = operand_stack.pop()
        operand = [operator, left, right]
        operand_stack.append(operand)
    return operand_stack.pop() if len(operand_stack) == 1 else operand_stack


def _next_token(s, start):
    i = start
    while i < len(s):
        while _is_empty(s[i]):
            i += 1
        if _is_operand(s[i]):
            begin = i
            while i < len(s) and _is_operand(s[i]):
                i += 1
            return s[begin:i], i
        else:
            return s[i], i + 1
    return None, None