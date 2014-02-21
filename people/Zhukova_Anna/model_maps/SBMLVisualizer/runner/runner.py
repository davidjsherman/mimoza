import getopt
from shutil import copyfile
from libsbml import os


__author__ = 'anna'


def create_dir(directory, model_id):
	m_dir = '{0}/{1}'.format(directory, model_id)
	if not os.path.exists(m_dir):
		os.makedirs(m_dir)
	return m_dir


def log(msg, verbose=True):
	if verbose:
		print msg


def prepare_dir(directory, sbml_file, model_id):
	m_dir = create_dir(directory, model_id)
	new_sbml_file = '{0}/{1}.xml'.format(m_dir, model_id)
	if sbml_file != new_sbml_file:
		copyfile(sbml_file, new_sbml_file)
	os.remove(sbml_file)
	return m_dir, new_sbml_file


def process_args(argv, help_message):
	try:
		opts, args = getopt.getopt(argv[1:], "m:d:h:s:c:f:t:v", ["help", "dir=", "model=", "scripts=", "css=", "fav=", "tile=", "verbose"])
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
