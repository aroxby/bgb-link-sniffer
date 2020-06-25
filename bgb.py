from socketserver import ForkingTCPServer, StreamRequestHandler
import struct

from network import ready_to_read, TCPClient


class BGBMessage(object):
    """
    BGB 1.4 link protocol
    https://bgb.bircd.org/bgblink.html
    """

    SIZE = 8
    _STRUCT_FORMAT = '=BBBBL'
    CMD_MASTER_SYNC = 104
    CMD_SLAVE_SYNC = 105

    @classmethod
    def unpack(cls, data):
        values = struct.unpack(cls._STRUCT_FORMAT, data)
        return cls(*values)

    @classmethod
    def for_value(cls, value):
        return cls(cls.CMD_SLAVE_SYNC, value, 0x80, 0, 0)

    def __init__(self, b1, b2, b3, b4, i1):
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
        self.b4 = b4
        self.i1 = i1

    def __str__(self):
        return str((self.b1, self.b2, self.b3, self.b4, self.i1))

    def get_value(self):
        if self.b1 in [self.CMD_MASTER_SYNC, self.CMD_SLAVE_SYNC]:
            value = self.b2
        else:
            value = None
        return value

    def to_data(self):
        data = struct.pack(
            self._STRUCT_FORMAT, self.b1, self.b2, self.b3, self.b4, self.i1
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
                yield BGBMessage.unpack(data)
            else:
                self.closed = True

    def send_message(self, msg):
        self.socket.sendall(msg.to_data())


class BGBRelayHandler(StreamRequestHandler):
    def handle(self):
        client = BGBChannel(self.request)
        with TCPClient(self.server.upstream_address) as upstream_socket:
            upstream = BGBChannel(upstream_socket)
            while not client.closed and not upstream.closed:
                client_values = []
                for client_msg in client.recv_messages():
                    client_value = client_msg.get_value()
                    if client_value is not None:
                        client_values.append(client_value)
                    upstream.send_message(client_msg)
                if client_values:
                    print('Client write: {}'.format(client_values))

                upstream_values = []
                for upstream_msg in upstream.recv_messages():
                    upsteam_value = upstream_msg.get_value()
                    if upsteam_value is not None:
                        upstream_values.append(upsteam_value)
                    client.send_message(upstream_msg)
                if upstream_values:
                    print('Upstream write: {}'.format(upstream_values))


class BGBRelayServer(ForkingTCPServer):
    def __init__(self, server_address, upstream_address):
        super().__init__(server_address, BGBRelayHandler)
        self.upstream_address = upstream_address
