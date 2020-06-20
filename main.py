#!/usr/bin/env python3
from server import MessageRelayServer


def text_formatter(data):
    return data.decode('utf-8')


def main():
    listen_address = ('127.0.0.1', 8080)
    upstream_address = ('www.example.com', 80)
    with MessageRelayServer(
        listen_address, upstream_address, text_formatter
    ) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()