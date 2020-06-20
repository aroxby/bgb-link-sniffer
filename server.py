import socket
from socketserver import ForkingTCPServer, StreamRequestHandler


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


class MessageRelayHandler(StreamRequestHandler):
    def handle(self):
        with TCPClient(self.server.upstream_address) as upstream:
            while True:
                data = self.rfile.read1()
                if not data:
                    break
                print("{}:{} wrote: ".format(*self.client_address))
                print(self.server.message_formatter(data))

                upstream.send(data)
                resp = upstream.recv()
                print("{}:{} wrote: ".format(*self.server.upstream_address))
                print(self.server.message_formatter(resp))
                self.wfile.write(resp)


class MessageRelayServer(ForkingTCPServer):
    def __init__(self, server_address, upstream_address, message_formatter):
        super().__init__(server_address, MessageRelayHandler)
        self.upstream_address = upstream_address
        self.message_formatter = message_formatter
