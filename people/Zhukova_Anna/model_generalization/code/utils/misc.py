__author__ = 'anna'


def add2map(m, key, value):
    if key in m:
        m[key].add(value)
    else:
        m[key] = {value}