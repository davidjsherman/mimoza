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