import datetime

__author__ = 'anna'

def log(verbose, msg):
    if verbose:
        print msg
        print datetime.datetime.now().time()
        print