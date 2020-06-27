from socketserver import ForkingTCPServer, StreamRequestHandler
import struct

from network import ready_to_read


class BGBMessage(object):
    """
    BGB 1.4 link protocol
    https://bgb.bircd.org/bgblink.html
    """

    SIZE = 8
    _STRUCT_FORMAT = '=BBBBL'
    CMD_HANDSHAKE = 1
    CMD_MASTER_SYNC = 104
    CMD_SLAVE_SYNC = 105
    CMD_TIME_SYNC = 106
    CMD_STATUS = 108

    @classmethod
    def unpack(cls, data):
        values = struct.unpack(cls._STRUCT_FORMAT, data)
        return cls(*values)

    @classmethod
    def for_value(cls, value):
        return cls(cls.CMD_SLAVE_SYNC, value, 0x80, 0, 0)

    def __init__(self, b1, b2, b3, b4, i1):
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
        self.b4 = b4
        self.i1 = i1

    def __str__(self):
        return str((self.b1, self.b2, self.b3, self.b4, self.i1))

    def get_value(self):
        if self.b1 in [self.CMD_MASTER_SYNC, self.CMD_SLAVE_SYNC]:
            value = self.b2
        else:
            value = None
        return value

    def to_data(self):
        data = struct.pack(
            self._STRUCT_FORMAT, self.b1, self.b2, self.b3, self.b4, self.i1
        )
        return data


class StandardBGBMessages(object):
    HANDSHAKE = BGBMessage(BGBMessage.CMD_HANDSHAKE, 1, 4, 0, 0)
    OPEN_STATUS = BGBMessage(BGBMessage.CMD_STATUS, 5, 0, 0, 0)


class BGBChannel(object):
    def __init__(self, socket):
        self.socket = socket
        self.closed = False

    def recv_messages(self):
        while not self.closed and ready_to_read(self.socket):
            data = self.socket.recv(BGBMessage.SIZE)
            if data:
                msg = BGBMessage.unpack(data)

                # Every sync3 message must get another sync3 in reply.
                # Otherwise, the client locks up waiting.
                if msg.b1 == BGBMessage.CMD_TIME_SYNC:
                    self.send_message(BGBMessage(
                        BGBMessage.CMD_TIME_SYNC, 0, 0, 0, msg.i1
                    ))

                yield msg
            else:
                self.closed = True

    def send_message(self, msg):
        self.socket.sendall(msg.to_data())


class BGBLinkFile(object):
    def __init__(self, channel):
        self.channel = channel

    def read(self):
        data = []
        msgs = self.channel.recv_messages()
        data += [
            msg.get_value() for msg in msgs if msg.get_value() != None
        ]
        return bytes(data)

    def write(self, data):
        for byte in data:
            msg = BGBMessage.for_value(byte)
            self.channel.send_message(msg)

    @property
    def closed(self):
        return self.channel.closed


# TODO: Remove
class ExampleLinkHandler(object):
    @staticmethod
    def hex_dump(bytes):
        hex = ''.join('x{:02x}'.format(byte) for byte in bytes)
        return hex

    def handle(self, link):
        print('Client connected!')
        while not link.closed:
            data = link.read()
            if data:
                print("Read: " + self.hex_dump(data))
                if data == b'\x00':     # Link established
                    link.write(b'\x00')
                elif data == b'\x01':     # Client keeps the clock
                    link.write(b'\x02')
                elif data == b'\x02':     # Server keeps the clock
                    link.write(b'\x01')
                elif data == b'\x60':     # We have both saved the game?
                    link.write(b'\x60')
                elif data in [b'\xd0', b'\xd1', b'\xd2']:  # Trade/Battle/Cancel
                    link.write(b'\xd0')
                else:   # This is serial line.  We have to send something.
                    link.write(data)


class BGBConnectionHandler(StreamRequestHandler):
    def accept_client(self):
        client = BGBChannel(self.request)
        client.send_message(StandardBGBMessages.HANDSHAKE)

        # Must wait for client to send status before proceeding
        msgs = []
        while not msgs:
            msgs = [
                msg for msg in client.recv_messages()
                if msg.b1 == BGBMessage.CMD_STATUS
            ]

        client.send_message(StandardBGBMessages.OPEN_STATUS)
        return client

    def handle(self):
        handler = ExampleLinkHandler()
        handler.handle(BGBLinkFile(self.accept_client()))


class BGBRelayServer(ForkingTCPServer):
    def __init__(self, server_address):
        super().__init__(server_address, BGBConnectionHandler)
        print('Server ready!')
