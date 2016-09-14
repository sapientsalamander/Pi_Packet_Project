"""Functions for converting various things from one form to another.

These functions convert the parameter to a different type or convert
units.

convert_packet_int_array: Converts a Scapy packet to an array of ints.
convert_bandwidth_units: Calculate the unit for a given bps.
convert_delay_bytes: Converts time in seconds and microseconds to a bytearray.
"""
import struct


def convert_packet_int_array(pac):
    """Converts a Scapy packet into an array of integers."""
    tmp = str(pac).encode('hex')
    tmp = [x + y for x, y in zip(tmp[0::2], tmp[1::2])]
    return map(lambda x: int(x, 16), tmp)


# TODO Remove, unused
def convert_packet_delay(pps):
    """Calculates a delay between packets given the desired number of
    packets per second.

    Args:
        pps: desired number of packets per second

    Returns:
        int: The number of whole seconds and microseconds
        between packets as a tuple.
    """
    try:
        useconds = (1.0 / pps) * 1000000
    except (ZeroDivisionError):
        useconds = 0
    return int(useconds)


# TODO Remove, unused
def convert_bandwidth_bits_per_second(d_bytes, d_time,
                                      pac_len=0, sys_err=0):
    """Calculates the bandwidth, taking in delta bytes and delta time and
    outputting bandwidth in bits per second.

    Args:
        d_bytes: Delta bytes.
        d_time: Delta time.

    Returns:
        float: Bandwidth in bits per second.
    """
    try:
        num_packets = d_bytes / (pac_len + sys_err)
    except (ZeroDivisionError):
        num_packets = 0

    # Bandwidth (bits/s) = (packets * size packet / delta time) * 8 bits / byte
    return (num_packets * pac_len) / (d_time) * 8


def convert_bandwidth_units(bandwidth):
    """Calculate the most appropriate unit for a given number of bps.

    Args:
        bandwidth: Current bandwidth in bits per second.

    Returns:
        tuple(float, str): The adjusted number and unit as a tuple.
    """
    BDWTH_ABBRS = ('bps', 'Kbps', 'Mbps', 'Gbps')

    bw_unit = 0
    while bandwidth >= 1000:
        bandwidth /= 1000.0
        bw_unit += 1
    return (bandwidth, BDWTH_ABBRS[bw_unit])


def convert_delay_bytes(delay_seconds, delay_useconds):
    """Takes in the delay, and returns it in SEASIDE compatible form.

    Args:
        delay_seconds (int): The number of seconds in between each packet sent.
        delay_useconds (int): The number of microseconds in between packets.

    Returns:
        str: The bytes of sleep time formatted to SEASIDE specifications.
            i.e. It returns it so seconds takes one byte while useconds takes
            four bytes.
    """
    return struct.pack('=BI', delay_seconds, delay_useconds)
