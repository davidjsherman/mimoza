import sys
from runner.os_helper import process_args, Usage
from runner.tulip_helper import visualize_model


__author__ = 'anna'
help_message = '''
Generalizes and visualizes the model.
usage: main.py --model model.xml --verbose
'''


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		sbml, directory, scripts, css, fav, tile, verbose = process_args(argv, help_message)
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2
	visualize_model(directory, sbml, scripts, css, fav, tile, verbose)


if __name__ == "__main__":
	sys.exit(main())