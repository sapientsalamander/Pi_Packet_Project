import shared_functions
import struct
from enum import Enum

SEASIDE_FLAGS = Enum('PACKET', 'START', 'STOP', 'DELAY', 'NUM_PACKETS')


def send_SEASIDE(socket, SEASIDE_flag, data=None):
    """Sends a SEASIDE packet through the socket.

    Converts the packet to an int array and the int array of data (including
    flag and size information) to a byte array, and then sends it through the
    provided socket.

    socket -- the socket to send the data to

    SEASIDE_flag - indicator for the type of data to be sent.
        0 - Packet. Requires a packet be passed also
        1 - Start signal. Begins packet transmission.
        2 - Stop signal. Ends packet transmission.
        3 - Set delay. If no delay is passed, it will remove the delay.
        4 - Number of packets. Data contains the number of packets sent.

    data -- the data contained in the packet, if any.

    """
    if data is None:
        data = []
    # TODO: Ensure that len(data) will work for all inputs.
    SEASIDE_header = struct.pack('=bh', SEASIDE_flag, len(data))
    if type(data) is not list:
        data = shared_functions.int_array(*data)
    SEASIDE_packet = bytearray(data)
    socket.send(SEASIDE_header + SEASIDE_packet)