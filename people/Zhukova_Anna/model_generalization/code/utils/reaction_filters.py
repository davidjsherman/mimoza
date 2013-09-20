__author__ = 'anna'

GENE_ASSOCIATION_PREFIX = 'GENE_ASSOCIATION:'
PATHWAY_ASSOCIATION_PREFIX = 'SUBSYSTEM:'
EC_ASSOCIATION_PREFIX = "PROTEIN_CLASS:"

# -------------------------REACTION-FILTERS-----------------------------


# by genes
def filterReactionByGeneCollection(geneCollection, reaction):
    genes = getGenesByReaction(reaction)
    return set(genes) & set(geneCollection)


# by pathway
def filterReactionByPathway(pathwayName, reaction):
    if not pathwayName:
        return False
    pathwayName = pathwayName.lower()
    pathways = getPathwayExpression(reaction)
    for pathway in pathways:
        if pathway and pathway.lower().find(pathwayName) != -1:
            return True
    return False


# by reaction attributes
def filterReactionByIdCollection(idCollection, reaction):
    return reaction.getId() in idCollection


def filterReactionByName(name, reaction):
    if not name:
        return False
    name = name.lower()
    r_name = reaction.getName()
    return r_name and r_name.lower().find(name) != -1


# by compartment
def filterReactionByCompartmentIdCollectionOfAnyParticipant(compartmentIdCollection, reaction, model):
    for speciesId in getReactionParticipants(reaction):
        species = model.getSpecies(speciesId)
        if compartmentIdCollection == species.getCompartment():
            return True
    return False


def filterReactionByCompartmentIdCollectionOfAllParticipants(compartmentIdCollection, reaction, model):
    for speciesId in getReactionParticipants(reaction):
        species = model.getSpecies(speciesId)
        if not (species.getCompartment() in compartmentIdCollection):
            return False
    return True


def filterReactionByCompartmentNameOfAnyParticipant(compartmentName, reaction, model):
    if not compartmentName:
        return False
    compartmentName = compartmentName.lower()
    for speciesId in getReactionParticipants(reaction):
        species = model.getSpecies(speciesId)
        compartment_id = species.getCompartment()
        if not compartment_id:
            continue
        compartment = model.getCompartment(compartment_id)
        if not compartment:
            continue
        compartment_name = compartment.getName()
        if compartment_name and compartment_name.lower().find(compartmentName) != -1:
            return True
    return False


def filterReactionByCompartmentNameOfAllParticipants(compartmentName, reaction, model):
    if not compartmentName:
        return False
    compartmentName = compartmentName.lower()
    for speciesId in getReactionParticipants(reaction):
        species = model.getSpecies(speciesId)
        compartment_id = species.getCompartment()
        if not compartment_id:
            return False
        compartment = model.getCompartment(compartment_id)
        if not compartment:
            return False
        compartment_name = compartment.getName()
        if not compartment_name or compartment_name.lower().find(compartmentName) == -1:
            return False
    return True


def filterReactionByCompartmentOfAllParticipants(c_id, reaction, model):
    if not c_id:
        return False
    for speciesId in getReactants(reaction) | getProducts(reaction):
        species = model.getSpecies(speciesId)
        compartment_id = species.getCompartment()
        if not compartment_id:
            return False
        if compartment_id != c_id:
            return False
    return True


def filterReactionByNotTransport(reaction, model):
    c_id = None
    participants = getReactants(reaction) | getProducts(reaction)
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
def filterReactionBySpeciesIdCollection(speciesIdList, reaction):
    return set(speciesIdList) & set(getReactionParticipants(reaction))


def filterReactionBySpeciesName(name, reaction, model):
    if not name:
        return False
    name = name.lower()
    for speciesId in getReactionParticipants(reaction):
        species = model.getSpecies(speciesId)
        if not species:
            continue
        species_name = species.getName()
        if species_name and species_name.lower().find(name) != -1:
            return True
    return False


def filterReactionByReactantId(speciesId, reaction):
    return speciesId in getReactants(reaction)


def filterReactionByProductId(speciesId, reaction):
    return speciesId in getProducts(reaction)


def filterReactionByModifierId(speciesId, reaction):
    return speciesId in getModifiers(reaction)


def filterReactionByBetweenSpecies(reaction, s_id1, s_id2):
    reactants = getReactants(reaction)
    products = getProducts(reaction)
    if s_id1 in reactants:
        return s_id2 in products
    elif s_id2 in reactants:
        return s_id1 in products
    return False

# -------------------------REACTION-INFO-----------------------------

def getGenesByReaction(reaction):
    return geneAssociation2genes(getGeneAssociation(reaction))


def geneAssociation2genes(geneAssociation):
    genes = []
    if geneAssociation:
        for g0 in geneAssociation.split('('):
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


def getGeneAssociation(reaction):
    result = set()
    node = reaction.getNotes()
    _getPrefixedNotesValue(node, result, GENE_ASSOCIATION_PREFIX)
    return " or ".join(result)


def getPathwayExpression(reaction):
    result = set()
    node = reaction.getNotes()
    _getPrefixedNotesValue(node, result, PATHWAY_ASSOCIATION_PREFIX)
    return result


def getECs(reaction):
    result = set()
    node = reaction.getNotes()
    _getPrefixedNotesValue(node, result, EC_ASSOCIATION_PREFIX)
    return result


def getReactionParticipants(reaction):
    result = getReactants(reaction)
    result |= getProducts(reaction)
    result |= getModifiers(reaction)
    return result


def getReactants(reaction):
    return {speciesRef.getSpecies() for speciesRef in reaction.getListOfReactants()}


def getProducts(reaction):
    return {speciesRef.getSpecies() for speciesRef in reaction.getListOfProducts()}


def getModifiers(reaction):
    return {speciesRef.getSpecies() for speciesRef in reaction.getListOfModifiers()}


def _getPrefixedNotesValue(notes, result, prefix):
    if not notes:
        return
    for i in range(0, notes.getNumChildren()):
        child = notes.getChild(i)
        note = child.getCharacters()
        if note:
            start = note.find(prefix)
            if start != -1:
                start += len(prefix)
                result.add(note[start:len(note)].strip())
        _getPrefixedNotesValue(child, result, prefix)


# ----------------------INFIX-TO-POSTFIX-NOTATION-CONVERSION--------------------------

_isOperator = lambda s: s in ['&', '|']
_isParentheses = lambda s: s in ['(', ')']
_isEmpty = lambda s: s is ' '
_isOperand = lambda s: not _isOperator(s) and not _isParentheses(s) and not _isEmpty(s)


def infix2postfix(s):
    operatorHierarchy = lambda op: 1 if op is '&' else (0 if op is '|' else -1)
    s = s.replace(' and ', ' & ').replace(' or ', ' | ')
    operand_stack = []
    operator_stack = []
    i = 0
    while i < len(s):
        token, i = _nextToken(s, i)
        if _isOperand(token):
            operand_stack.append(token)
        elif token is '(' or not operator_stack or operatorHierarchy(token) > operatorHierarchy(
                operator_stack[len(operator_stack) - 1]):
            operator_stack.append(token)
        elif token is ')':
            operator = operator_stack.pop()
            while not operator is '(':
                right = operand_stack.pop()
                left = operand_stack.pop()
                operand = [operator, left, right]
                operand_stack.append(operand)
                operator = operator_stack.pop()
        else:
            while operand_stack and operator_stack and operatorHierarchy(token) <= operatorHierarchy(
                    operator_stack[len(operator_stack) - 1]):
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


def _nextToken(s, start):
    i = start
    while i < len(s):
        while _isEmpty(s[i]):
            i += 1
        if _isOperand(s[i]):
            begin = i
            while i < len(s) and _isOperand(s[i]):
                i += 1
            return s[begin:i], i
        else:
            return s[i], i + 1
    return None, None