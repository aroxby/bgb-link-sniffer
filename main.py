#!/usr/bin/env python3
import socket
from socketserver import ForkingTCPServer, StreamRequestHandler


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


class RelayHandler(StreamRequestHandler):
    def handle(self):
        data = b''
        blanks = 0
        while blanks < 1:
            line = self.rfile.readline()
            data += line
            if not line.strip():
                blanks += 1
        print("{}:{} wrote: ".format(*self.client_address))
        print(data.decode('utf-8'))

        with TCPClient(self.server.upstream_address) as client:
            MAX_RECV = 4096
            MAX_RESP = MAX_RECV * MAX_RECV
            client.sendall(data)
            resp = b''
            while len(resp) < MAX_RESP:
                more_resp = client.recv(MAX_RECV)
                resp += more_resp
                if len(more_resp) < MAX_RECV:
                    break

        print("{}:{} wrote: ".format(*self.server.upstream_address))
        print(resp.decode('utf-8'))
        self.wfile.write(resp)


class RelayServer(ForkingTCPServer):
    def __init__(self, server_address, upstream_address):
        super().__init__(server_address, RelayHandler)
        self.upstream_address = upstream_address


def main():
    listen_address = ('127.0.0.1', 8080)
    upstream_address = ('www.example.com', 80)
    with RelayServer(listen_address, upstream_address) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()