from select import select
import socket
from socketserver import ForkingTCPServer, StreamRequestHandler

from bgb import BGBChannel


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
