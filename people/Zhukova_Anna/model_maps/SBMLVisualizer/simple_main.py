import sys

from runner.mod_gen_helper import html_model
from runner.os_helper import process_args, Usage


__author__ = 'anna'
help_message = '''
Generalizes the model.
usage: simple_main.py --model model.xml --verbose'''


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		sbml, directory, scripts, css, fav, tile, verbose = process_args(argv, help_message)
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2
	html_model(directory, sbml, scripts, css, fav, verbose)


if __name__ == "__main__":
	sys.exit(main())