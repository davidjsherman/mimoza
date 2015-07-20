from sbml_vis.graph.graph_properties import *


def get_short_name(graph, n, onto):
    graph = graph.getRoot()
    short_name = graph[NAME][n] if graph[NAME][n] else graph[ID][n]

    # remove compartment from the name,
    # e.g. H2O [peroxisome] --> H2O
    short_name.replace("[%s]" % graph[COMPARTMENT_ID][n], '').strip()
    if graph.isMetaNode(n) and TYPE_COMPARTMENT != graph[TYPE][n]:
        num = " ({0})".format(graph[VIEW_META_GRAPH][n].numberOfNodes())
        short_name = short_name.replace(num, '').replace('generalized ', '').strip()
    min_len = len(short_name)

    formula = graph[FORMULA][n]
    if formula and (len(formula) < min_len or formula.lower() == short_name.lower()):
        min_len = len(formula)
        short_name = convert_formula_to_html(formula)

    # replace with a chebi name
    # if it is shorter
    ch_id = graph[TERM][n]
    if ch_id and onto:
        term = onto.get_term(ch_id)
        if term:
            if not formula:
                formulas = term.get_formulas()
                if formulas:
                    formula = next(iter(formulas))
                    if len(formula) < min_len:
                        min_len = len(formula)
                        short_name = convert_formula_to_html(formula)
            t_name = term.get_name()
            if t_name and len(t_name) < min_len:
                min_len = len(t_name)
                short_name = t_name
            for alt in term.get_synonyms():
                if alt and len(alt) < min_len:
                    min_len = len(alt)
                    short_name = alt

    if graph.isMetaNode(n) and TYPE_COMPARTMENT != graph[TYPE][n]:
        short_name += " ({0})".format(graph[VIEW_META_GRAPH][n].numberOfNodes())
    return short_name


def convert_formula_to_html(formula):
    return ''.join(((('<sub>%s</sub>' % e) if e.isdigit() else e) for e in formula))


def split_into_parts(name):
    short_name = name.replace('(', ' (').replace('  ', ' ').replace('-', '- ').replace(' )', ')').replace('  ', ' ')
    parts = short_name.split(' ')
    new_parts = []
    prefix = ''
    max_ = max(len(short_name) / 4, 7)
    if parts:
        for part in parts:
            prefix, ps = treat(prefix, part, max_)
            new_parts += ps
        if prefix:
            new_parts.append(prefix)
    return '\n'.join(new_parts)


def treat(prefix, part, max_):
    if len(prefix + part) <= 4:
        return prefix + part, []
    border = max_ - len(prefix)
    if len(prefix + part) <= max_ or len(part[border:]) == 1:
        return '', [prefix + part]
    if len(prefix) <= 4:
        if prefix and not prefix.endswith('-'):
            prefix += ' '
        return part[border:], [prefix + part[:border] + '-']
    p, ps = treat('', part, max_)
    return p, [prefix] + ps
