from sbml_vis.tulip.graph_properties import *


def get_short_name(graph, n, onto):
	graph = graph.getRoot()
	short_name = graph[NAME][n]
	
	# remove compartment from the name,
	# e.g. H2O [peroxisome] --> H2O
	short_name.replace("[%s]" % graph[COMPARTMENT][n], '').strip()
		
	# replace with a chebi name 
	# if it is shorter 
	ch_id = graph[ANNOTATION][n]
	if ch_id:
		term = onto.getTerm(ch_id)
		if term:
			alts = [term.getName()]
			alts.extend(term.getSynonyms())
			if not short_name: 
				short_name = term.getName()
			for alt in alts:
				if alt and len(alt) < len(short_name):
					short_name = alt
					
	# number of factored entities
	# if this one is a generalized one
	num = ''
	if graph.isMetaNode(n) and TYPE_COMPARTMENT != graph[TYPE][n]:
		num = " ({0})".format(graph[VIEW_META_GRAPH][n].numberOfNodes())
		short_name = short_name.replace(num, '').replace('generalized ', '').strip()
		
	if TYPE_REACTION == graph[TYPE][n] and short_name.find('(') > 0:
		short_name = short_name[:short_name.find('(')]
		
	short_name += num
	return short_name
	
		
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
