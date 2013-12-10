from tulip import *
import tulipplugins
from sbml_generalization.utils.obo_ontology import parse, get_chebi

class SBMLRenamer(tlp.Algorithm):
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)

	def check(self):
		return (True, "")

	def run(self):
		onto = parse(get_chebi())
		shorten(self.graph, onto)
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("SBMLRenamer", "SBMLRenamer", "anna", "09/12/2013", "", "1.0", "Metabolic")


def get_short_name(graph, n, onto):
	short_name = graph["name"][n]
	
	# remove compartment from the name,
	# e.g. H2O [peroxisome] --> H2O
	indx = short_name.find("[{0}]".format(graph["real_compartment"][n].split(',')[0]))
	if indx != -1: 
		short_name = short_name[:indx]
		
	# replace with a chebi name 
	# if it is shorter 
	ch_id = graph["chebi_id"][n]
	if ch_id:
		term = onto.getTerm(ch_id)
		if term:
			alts = [term.getName()]
			alts.extend(term.getSynonyms())
			if not short_name: 
				short_name = term.getName()
			for alt in alts:
				if len(alt) < len(short_name):
					short_name = alt
					
	# number of factored entities
	# if this one is a generalized one
	num = ''
	if graph.isMetaNode(n) and 'compartment' != graph['type'][n]:
		num = " ({0})".format(graph["viewMetaGraph"][n].numberOfNodes())
		short_name = short_name.replace(num, '').replace('generalized ', '').strip()
		
	short_name = short_name.replace('(', ' (').replace('  ', ' ').replace('-', '- ').replace(' )', ')')
	short_name += num
	
	
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
	
def shorten(graph, onto):		
	for n in graph.getNodes():
		graph["viewLabel"][n] = get_short_name(graph, n, onto)
		
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
