import struct


class BGBMessage(object):
    SIZE = 8

    def __init__(self, data):
        msg = struct.unpack('=BBBBL', data)
        self.b1, self.b2, self.b3, self.b4, self.li = msg

    def is_interesting(self):
        # Used to skip some packets while debugging
        return self.b1 not in [101, 106];

    def __str__(self):
        return str((self.b1, self.b2, self.b3, self.b4, self.li))