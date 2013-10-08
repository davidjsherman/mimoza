__author__ = 'anna'


def add2map(m, key, value):
    if key in m:
        m[key].add(value)
    else:
        m[key] = {value}


def removeFromMap(mp, key, value):
    if key in mp:
        mp[key] -= {value}
        if not mp[key]:
            del mp[key]


def invert(key2value):
    value2keys = {}
    for key, value in key2value.iteritems():
        add2map(value2keys, value, key)
    return value2keys