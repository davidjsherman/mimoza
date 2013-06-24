__author__ = 'anna'


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg