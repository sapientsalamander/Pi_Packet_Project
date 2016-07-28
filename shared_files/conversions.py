def convert_packet_int_array(pac):
    """Converts a Scapy packet into an array of integers."""
    tmp = str(pac).encode('hex')
    tmp = [x + y for x, y in zip(tmp[0::2], tmp[1::2])]
    return map(lambda x: int(x, 16), tmp)


def convert_MAC_addr(address):
    """Converts a MAC address from form ffffff-ffffff to ff:ff:ff:ff:ff:ff"""
    mac = []
    address = address.replace('-', '')
    for i in xrange(0, len(address), 2):
        mac.append(address[i:i+2])
    return ':'.join(mac)


def convert_packet_delay(pps):
    """Calculates a delay between packets given the desired number of packets
    per second.

    Args:
        pps - desired number of packets per second

    Returns:
        tuple (int, int): The number of whole seconds and microseconds
        between packets as a tuple.
    """
    seconds = 0
    useconds = (1.0 / pps) * 1000000
    while useconds >= 1000000:
        useconds -= 1000000
        seconds += 1
    return (int(seconds), int(useconds))


def convert_bandwidth_bits_per_second(d_bytes, d_time, sys_err=0):
    """Calculates the bandwidth, taking in delta bytes and delta time and
    outputting bandwidth in bits per second.

    Args:
        d_bytes: Delta bytes.
        d_time: Delta time.

    Returns:
        float: Bandwidth in bits per second.
    """
    # TODO: Instead of relying on system info (which is apparently
    # error-prone), receive number of bytes from C side, using SEASIDE.
    d_bytes = rx_cur - rx_prev
    d_time = time_cur - time_prev
    try:
        num_packets = d_bytes / (len(packet) + sys_err)
    except (ZeroDivisionError):
        num_packets = 0

    # Bandwidth (bits/s) = (packets * size packet / delta time) * 8 bits / byte
    bandwidth = (num_packets * len(packet))/(d_time) * 8


def convert_bandwidth_unit(bandwidth):
    """Calculate the most appropriate unit for a given number of bps.

    Args:
        bandwidth: Current bandwidth in bits per second.

    Returns:
        tuple(float, str): The adjusted number and appropriate unit as a tuple.
    """
    BDWTH_ABBRS = ('bps', 'Kbps', 'Mbps', 'Gbps')

    bw_unit = 0
    while bandwidth >= 1000:
        bandwidth /= 1000.0
        bw_unit += 1
    return (bandwidth, BDWTH_ABBRS[bw_unit])
