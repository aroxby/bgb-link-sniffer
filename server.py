from select import select
import socket
from socketserver import ForkingTCPServer, StreamRequestHandler

from bgb import BGBMessage


class SelfBufferingSocket(object):
    def __init__(self, socket):
        self.socket = socket

    def send(self, data):
        self.socket.sendall(data)

    def recv(self, max_data=16384, buffer_size=4096):
        data = b''
        while len(data) < max_data:
            max_recv = min(buffer_size, max_data - len(data))
            more_data = self.socket.recv(max_recv)
            data += more_data
            if len(more_data) < max_recv:
                break
        return data

    def would_block(self):
        rtr, rtw, err = select([self.socket], [], [], 0)
        return not bool(rtr)


class TCPClient(object):
    def __init__(self, server_address):
        self.server_address = server_address
        self.socket = None

    def __enter__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.__enter__()
        self.socket.connect(self.server_address)
        return SelfBufferingSocket(self.socket)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.socket.__exit__(exc_type, exc_value, exc_traceback)
        self.socket = None


class BGBRelayHandler(StreamRequestHandler):
    def handle(self):
        client = SelfBufferingSocket(self.request)
        quit = False
        with TCPClient(self.server.upstream_address) as upstream:
            while not quit:
                while not quit and not client.would_block():
                    data = client.recv(BGBMessage.SIZE)
                    if not data:
                        quit = True
                        break
                    client_msg = BGBMessage(data)
                    if client_msg.is_interesting():
                        print("{}:{} wrote: ".format(*self.client_address))
                        print(client_msg)
                    upstream.send(data)

                while not quit and not upstream.would_block():
                    resp = upstream.recv(BGBMessage.SIZE)
                    if not resp:
                        quit = True
                        break
                    upstream_msg = BGBMessage(data)
                    if upstream_msg.is_interesting():
                        print("{}:{} wrote: ".format(*self.server.upstream_address))
                        print(upstream_msg)
                    client.send(resp)


class BGBRelayServer(ForkingTCPServer):
    def __init__(self, server_address, upstream_address):
        super().__init__(server_address, BGBRelayHandler)
        self.upstream_address = upstream_address
