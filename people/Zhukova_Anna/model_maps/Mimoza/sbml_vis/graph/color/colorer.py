__author__ = 'anna'

from sbml_vis.graph.graph_properties import TYPE_BG_SPECIES, TYPE_BG_REACTION, TYPE_BG_COMPARTMENT

GREY = "#B4B4B4"

ORANGE = "#EDB337"

YELLOW = "#F0DA78"

RED = "#E37B6F"

BLUE = "#79A8C9"

GREEN = "#B1C95B"

VIOLET = "#A595BF"

TURQUOISE = "#76C29B"

WHITE = 'white'


def get_edge_color(ubiquitous, generalized, transport):
	if ubiquitous:
		return GREY
	if generalized:
		return TURQUOISE if transport else GREEN
	return VIOLET if transport else BLUE


def get_bg_color(type, transport):
	if TYPE_BG_SPECIES == type:
		return ORANGE
	if TYPE_BG_REACTION == type:
		return TURQUOISE if transport else GREEN
	if TYPE_BG_COMPARTMENT == type:
		return YELLOW
	return None


def get_species_color(ubiquitous, generalized):
	if ubiquitous:
		return GREY
	return ORANGE if generalized else RED


def get_reaction_color(generalized, transport):
	if generalized:
		return TURQUOISE if transport else GREEN
	return VIOLET if transport else BLUE


def get_compartment_color():
	return YELLOW