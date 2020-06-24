import struct
# HACK: This networking stuff can't live in this module
# To be removed when I resolved the circular import
from select import select


def ready_to_read(socket):
    rtr, rtw, err = select([socket], [], [], 0)
    return bool(rtr)


class BGBMessage(object):
    SIZE = 8
    _STRUCT_FORMAT = '=BBBBL'

    def __init__(self, data):
        msg = struct.unpack(self._STRUCT_FORMAT, data)
        self.b1, self.b2, self.b3, self.b4, self.li = msg

    def __str__(self):
        return str((self.b1, self.b2, self.b3, self.b4, self.li))

    def is_interesting(self):
        # Used to skip some packets while debugging
        return self.b1 not in [101, 106]

    def to_data(self):
        data = struct.pack(
            self._STRUCT_FORMAT, self.b1, self.b2, self.b3, self.b4, self.li
        )
        return data


class BGBChannel(object):
    def __init__(self, socket):
        self.socket = socket
        self.closed = False

    def recv_messages(self):
        while not self.closed and ready_to_read(self.socket):
            data = self.socket.recv(BGBMessage.SIZE)
            if data:
                yield BGBMessage(data)
            else:
                self.closed = True

    def send_message(self, msg):
        self.socket.sendall(msg.to_data())
