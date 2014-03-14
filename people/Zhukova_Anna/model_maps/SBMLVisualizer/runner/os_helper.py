import getopt
import os
from shutil import copyfile


__author__ = 'anna'


def create_dir(directory):
	if not os.path.exists(directory):
		os.makedirs(directory)


def copy_sbml_file(directory, sbml_file, model_id):
	create_dir(directory)
	new_sbml_file = '%s%s.xml' % (directory, model_id)
	if sbml_file != new_sbml_file:
		copyfile(sbml_file, new_sbml_file)
		os.remove(sbml_file)
	return new_sbml_file


def process_args(argv, help_message):
	try:
		opts, args = getopt.getopt(argv[1:], "m:d:h:s:c:f:t:v",
		                           ["help", "dir=", "model=", "scripts=", "css=", "fav=", "tile=", "verbose"])
	except getopt.error, msg:
		raise Usage(msg)
	sbml, directory, scripts, css, fav, tile, verbose = None, None, [], [], None, None, False
	# option processing
	for option, value in opts:
		if option in ("-h", "--help"):
			raise Usage(help_message)
		if option in ("-m", "--model"):
			sbml = value
		if option in ("-s", "--scripts"):
			scripts = value.split(',')
		if option in ("-c", "--css"):
			css = value.split(',')
		if option in ("-f", "--fav"):
			fav = value
		if option in ("-t", "--tile"):
			tile = value
		if option in ("-d", "--dir"):
			directory = value
		if option in ("-v", "--verbose"):
			verbose = True
	if not sbml or not directory:
		raise Usage(help_message)
	return sbml, directory, scripts, css, fav, tile, verbose


class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg
