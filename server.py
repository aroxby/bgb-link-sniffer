from select import select
import socket
from socketserver import ForkingTCPServer, StreamRequestHandler

from bgb import BGBMessage


def _recv_would_block(socket):
    rtr, rtw, err = select([socket], [], [], 0)
    return not bool(rtr)


class TCPClient(object):
    def __init__(self, server_address):
        self.server_address = server_address
        self.socket = None

    def __enter__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.__enter__()
        self.socket.connect(self.server_address)
        return self.socket

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.socket.__exit__(exc_type, exc_value, exc_traceback)
        self.socket = None


class BGBRelayHandler(StreamRequestHandler):
    def handle(self):
        client = self.request
        quit = False
        with TCPClient(self.server.upstream_address) as upstream:
            while not quit:
                while not quit and not _recv_would_block(client):
                    data = client.recv(BGBMessage.SIZE)
                    if not data:
                        quit = True
                        break
                    client_msg = BGBMessage(data)
                    if client_msg.is_interesting():
                        print("{}:{} wrote: ".format(*self.client_address))
                        print(client_msg)
                    upstream.sendall(data)

                while not quit and not _recv_would_block(upstream):
                    resp = upstream.recv(BGBMessage.SIZE)
                    if not resp:
                        quit = True
                        break
                    upstream_msg = BGBMessage(data)
                    if upstream_msg.is_interesting():
                        print("{}:{} wrote: ".format(*self.server.upstream_address))
                        print(upstream_msg)
                    client.sendall(resp)


class BGBRelayServer(ForkingTCPServer):
    def __init__(self, server_address, upstream_address):
        super().__init__(server_address, BGBRelayHandler)
        self.upstream_address = upstream_address
