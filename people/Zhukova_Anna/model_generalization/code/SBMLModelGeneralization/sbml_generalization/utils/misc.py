__author__ = 'anna'


def add_to_map(m, key, value):
    if key in m:
        m[key].add(value)
    else:
        m[key] = {value}


def remove_from_map(mp, key, value):
    if key in mp:
        mp[key] -= {value}
        if not mp[key]:
            del mp[key]


def invert_map(key2value):
    value2keys = {}
    for key, value in key2value.iteritems():
        add_to_map(value2keys, value, key)
    return value2keys