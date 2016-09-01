"""The Python side of SEASIDE communication.

Contains the enum of SEASIDE flags, including unimplemented ones, as 
well as two functions for sending SEASIDE communications. One function sends
without expecting a response and is used to send instructions to the C-side.
The other waits for a response and is used to request statistical information
such as bandwidth usage.

SEASIDE_FLAGS: The enum of SEASIDE flags.
send_SEASIDE: sends a SEASIDE message without waiting for a response.
request_SEASIDE: sends a SEASIDE message and returns the C-side's response.
"""

import conversions
import struct
from enum import Enum

SEASIDE_FLAGS = Enum('SEASIDE_FLAGS',
                     'PACKET START STOP DELAY NUM_PACKETS SINGLE_PACKET\
                     GET_PACKET GET_BANDWIDTH GET_PACKET_SIZE START_SEQUENCE\
                     STOP_SEQUENCE',
                     start=0)


def send_SEASIDE(socket, socket_lock, SEASIDE_flag, data=None):
    """Sends a SEASIDE packet through the socket.

    Converts the packet and the int array of data (including flag and size
    information) to a byte array, and then sends it through the
    provided socket. The header consists of a one-byte flag and two bytes
    indicating the size of the data. Following the header is the data, if any.

    Args:
        socket (socket object): the socket to send the data to.

        socket_lock (RLock object): the lock associated with the socket, for
                                   multithreading safety.

        SEASIDE_flag (int): indicator for the type of data to be sent:
            0  - Packet. Requires a packet be passed also
            1  - Start signal. Begins packet transmission.
            2  - Stop signal. Ends packet transmission.
            3  - Set delay. Data contains the number of seconds and
                 microseconds to sleep between packets.
            4  - Number of packets. Requests the number of packets sent since
                 startup from the C-side. Currently unimplemented.
            5  - Single Packet. Instructs the C-side to send a single packet.
            6  - Get Packet. Requests the currently buffered packet from the
                 C-side.
            7  - Get Bandwidth. Requests the current bandwidth use from the
                 C-side.
            8  - Get Packet Size. Requests the size of the currently 
                 buffered packet from the C-side.
            9  - Start Sequence. Currently unimplemented.
            10 - Stop Sequence. Currently unimplemented.

        data (bytearray or int array): the data contained in the packet,
                                       if any.
    """

    if data is None:
        data = []

    SEASIDE_header = struct.pack('=BH', SEASIDE_flag, len(data))

    SEASIDE_packet = bytearray(data)
    with socket_lock:
        socket.send(SEASIDE_header + SEASIDE_packet)

def request_SEASIDE(socket, socket_lock, SEASIDE_flag):
    """Sends a request for information C-side and returns the response.

    Args:
        socket (socket object): the socket to send the data to.

        socket_lock (RLock object): the lock associated with the socket, for
                                   multithreading safety.

        SEASIDE_flag: indicator for the type of request. Request flags are:
            6  - Get Packet. Requests the currently buffered packet from the
                 C-side.
            7  - Get Bandwidth. Requests the current bandwidth use from the
                 C-side.
            8  - Get Packet Size. Requests the size of the currently buffered
                 packet from the C-side.
    Returns:
        bytearray: The response from the C-side.

    """
    SEASIDE_header = struct.pack('=BH', SEASIDE_flag, 0)
    data = ''
    with socket_lock:
        socket.send(SEASIDE_header)
        while True:
            data += (socket.recv(4096))
            print repr(data), len(data)
            if len(data) < 3:
                continue
            print repr(data), len(data), struct.unpack('=H', data[1:3])[0] + 3
            if len(data) >= struct.unpack('=H', data[1:3])[0] + 3:
                break
    print repr(data)
    return data[3:]
