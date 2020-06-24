from select import select
import socket


def ready_to_read(socket):
    rtr, rtw, err = select([socket], [], [], 0)
    return bool(rtr)


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
