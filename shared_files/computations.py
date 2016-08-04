"""Functions that read from various system files / diagnostic tools.

Computations, in our project, are defined as functions retrieve various
info that are scattered around the system. These can be files located in
os wide dirs, like /sys/, or from user files, like /home/pi/. These can also
have a layer of indirection, so we don't have to read the files ourselves,
but use a library as an interface. As examples, various computations can be
getting the bandwidth on an interface, cpu usage, MAC address, etc.

TODO: Find a better name than computations?
TODO: Error checking!
"""
import os

import psutil
import netifaces
import scapy.all as scapy

def read_interface_bytes(interface, io):
    """Return the total number of rx_bytes or tx_bytes since startup.

    On Linux machines, there is a directory (/sys/class/net/...) that
    contains networking information about different interfaces, and we just
    pull the number of bytes received / sent over eth0 since startup.

    Returns:
        The number of bytes received / sent over eth0 since startup.
    """
    try:
        with open('/sys/class/net/%s/statistics/%s_bytes' % (interface, io),
                  'r') as file:
            return int(file.read())
    except (IOError):
        return None


def read_cpu_usage():
    """Calculates cpu usage using the psutil library.

    Returns:
        tuple (float, list): The first return value is the average
        cpu usage, while the second argument is the cpu usage
        per core.
        """
    return (psutil.cpu_percent(), psutil.cpu_percent(percpu=True))


def read_pcap_file(fname):
    """Reads a pcap file and returns the first packet in the file.

    Args:
        fname (str): Name of the file located in packet_files/.

    Returns:
        Packet: The first packet found in the file, as a scapy packet.
    """
    p = scapy.rdpcap('/home/pi/Sender/sender_files/packet_files/%s' % fname)
    return p[0]


def read_MAC():
    """Returns the MAC address of the eth0 interface.

    Returns:
        str: MAC address of the eth0 interface, or all 0s if there's an error.

    TODO: Generalized so it can get the MAC address of any interface.
    """
    try:
        with open('/sys/class/net/eth0/address') as file:
            return file.read().strip()
    except:
        print 'Error, cannot read MAC address'
        return '00:00:00:00:00:00'


def read_defaults():
    """Reads in the packet defaults from packet_config.

    Returns:
        dict: A dictionary of mappings of different layers to a list of
            dictionaries of layer fields to their default values.
            Example:

    TODO: Once the default list is done, make sure that we change this
    function, and update any relevant documentation.
    """
    defaults = {}
    with open('/home/pi/Sender/sender_files/packet_files/packet_config.txt',
              'r') as conf:
        fields = [val for val in conf.read().split('\n')
                  if len(val) > 0 and val[0] != '#']
    for field in fields:
        name, value = field.split(' = ')
        defaults[name] = value
    defaults['src_MAC'] = read_MAC()
    defaults['src_IP'] = get_ip_addr('eth0')
    defaults['dst_IP'] = '.'.join(['%03d' % int(octal)
                         for octal in defaults['dst_IP'].split('.')])
    return defaults


def get_ip_addr(ifname):
    """Gets the ip address of an interface.

    Args:
        ifname (str): Name of an interface (eth0, wlan1, etc.)

    Returns:
        str: IP address of the interface, in standard IP format.

    TODO: Change name of ifname. Plus error checking.
    """
    ip = netifaces.ifaddresses(ifname)[2][0]['addr']
    return '.'.join(['%03d' % int(octal) for octal in ip.split('.')])

