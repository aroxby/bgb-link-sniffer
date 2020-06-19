#!/usr/bin/env python3
from socketserver import ForkingTCPServer, StreamRequestHandler


class EchoHandler(StreamRequestHandler):
    def handle(self):
        self.data = b''
        line = self.rfile.readline()
        while line.strip():
            self.data += line
            line = self.rfile.readline()
        print("{} wrote: ".format(self.client_address[0]))
        print(self.data.decode('utf-8'))
        self.wfile.write(self.data)


class EchoServer(ForkingTCPServer):
    def __init__(self, server_address):
        super().__init__(server_address, EchoHandler)


def main():
    server = EchoServer(('127.0.0.1', 8080))
    server.serve_forever()


if __name__ == '__main__':
    main()