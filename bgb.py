from socketserver import ForkingTCPServer, StreamRequestHandler
import struct

from network import ready_to_read, TCPClient


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


class BGBRelayHandler(StreamRequestHandler):
    def handle(self):
        client = BGBChannel(self.request)
        with TCPClient(self.server.upstream_address) as upstream_socket:
            upstream = BGBChannel(upstream_socket)
            while not client.closed and not upstream.closed:
                for client_msg in client.recv_messages():
                    if client_msg.is_interesting():
                        print("{}:{} wrote: ".format(*self.client_address))
                        print(client_msg)
                    upstream.send_message(client_msg)

                for upstream_msg in upstream.recv_messages():
                    if upstream_msg.is_interesting():
                        print("{}:{} wrote: ".format(*self.server.upstream_address))
                        print(upstream_msg)
                    client.send_message(upstream_msg)


class BGBRelayServer(ForkingTCPServer):
    def __init__(self, server_address, upstream_address):
        super().__init__(server_address, BGBRelayHandler)
        self.upstream_address = upstream_address
