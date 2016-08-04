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

    Converts the packet to an int array and the int array of data (including
    flag and size information) to a byte array, and then sends it through the
    provided socket.

    socket -- the socket to send the data to

    SEASIDE_flag -- indicator for the type of data to be sent.
        0 - Packet. Requires a packet be passed also
        1 - Start signal. Begins packet transmission.
        2 - Stop signal. Ends packet transmission.
        3 - Set delay. If no delay is passed, it will remove the delay.
        4 - Number of packets. Data contains the number of packets sent.
        5 - Single Packet. Instructs the C-side to send a single packet.

    data -- the data contained in the packet, if any. Must be an array.
    """
    # TODO Add other flag values

    if data is None:
        data = []

    # TODO: Ensure that len(data) will work for all inputs.
    SEASIDE_header = struct.pack('=BH', SEASIDE_flag, len(data))

    SEASIDE_packet = bytearray(data)
    with socket_lock:
        socket.send(SEASIDE_header + SEASIDE_packet)

def request_SEASIDE(socket, socket_lock, SEASIDE_flag):
    SEASIDE_header = struct.pack('=BH', SEASIDE_flag, 0)
    with socket_lock:
        socket.send(SEASIDE_header)
        data = socket.recv(4096)
    return data
