#!/usr/bin/env python3
import struct
import sys
import argparse

from server import MessageRelayServer


def parse_bgb(data):
    msg = struct.unpack('=BBBBL', data)
    return msg


class AddressArgAction(argparse.Action):
    @staticmethod
    def parse_address(addr):
        host, port = addr.split(':')
        port = int(port)
        return host, port

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            address = self.parse_address(values)
        except ValueError:
            parser.error('Invalid address "{}", use the HOST:PORT form'.format(values))
        setattr(namespace, self.dest, address)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Sniff TCP Data')
    parser.add_argument(
        '--listen',
        action=AddressArgAction,
        help='Listen on this address (host:port)',
        metavar='LISTEN_ADDRESS',
        required=True,
    )
    parser.add_argument(
        '--connect',
        action=AddressArgAction,
        help='Relay data to this address (host:port)',
        metavar='UPSTREAM_ADDRESS',
        required=True,
    )

    args = parser.parse_args(argv)
    return args


def main(argv):
    args = parse_args(argv[1:])
    with MessageRelayServer(
        args.listen, args.connect, parse_bgb
    ) as server:
        server.serve_forever()


if __name__ == '__main__':
    main(sys.argv)
