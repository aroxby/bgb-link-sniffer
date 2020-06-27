from select import select
import socket


def ready_to_read(socket):
    rtr, rtw, err = select([socket], [], [], 0)
    return bool(rtr)
