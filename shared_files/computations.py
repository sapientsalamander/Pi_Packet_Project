"""Functions that read from various system files / diagnostic tools.

Computations, in our project, are defined as functions retrieve various
info that are scattered around the system. These can be files located in
os wide dirs, like /sys/, or from user files, like /home/pi/. These can also
have a layer of indirection, so we don't have to read the files ourselves,
but use a library as an interface. As examples, various computations getthe
bandwidth on an interface, cpu usage, MAC address, etc.


read_cpu_usage: Calculates cpu usage using the psutil library.
read_pcap_file: Reads a pcap file and returns the first packet.
read_MAC: Returns the MAC address of the interface.
read_defaults: Reads in the packet defaults from packet_config.
get_ip_addr: Gets the ip address of an interface.

TODO: Find a better name than computations?
TODO: Error checking!
"""
import os
import re

import psutil
import netifaces
import scapy.all as scapy

PACKET_DIR = '/home/pi/Pi_Packet_Project/sender_files/packet_files/'


# TODO Remove, unused
# NOTE: Not currently used, may need to be utilized in the future, leaving it
# here for now.
def read_interface_bytes(interface, io):
    """Return the total number of rx_bytes or tx_bytes since startup.

    On Linux machines, there is a directory (/sys/class/net/...) that
    contains networking information about different interfaces, and we just
    pull the number of bytes received / sent over eth0 since startup.

    Args:
        interface (str): the name of the interface to gather information from.

        io (str): the direction to read from (tx or rx)

    Returns:
        int: Number of bytes received/sent over the interface since startup.
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
        tuple (float, [float, ..]): The first value is the average cpu usage,
        while the second value is the cpu usage per core.
        """
    return (psutil.cpu_percent(), psutil.cpu_percent(percpu=True))


def read_pcap_file(fname):
    """Reads a pcap file and returns the first packet in the file.

    Args:
        fname (str): Name of the file located in packet_files/.

    Returns:
        Packet: The first packet found in the file, as a scapy packet.
    """
    p = scapy.rdpcap(PACKET_DIR + '%s' % fname)
    return p[0]


def read_MAC(interface):
    """Returns the MAC address of the interface.

    Args:
        interface (str): the name of the interface.
    Returns:
        str: MAC address of the eth0 interface, or all 0s if there's an error.
    """
    try:
        with open('/sys/class/net/%s/address' % interface) as file:
            return file.read().strip()
    except (IOError):
        print 'Error, cannot read MAC address'
        return '00:00:00:00:00:00'


def read_defaults():
    """Reads in the packet defaults from packet_config.

    Returns:
        dict: A dictionary of mappings of layers to a list of dictionaries of
        layer fields to their default values. For an example,
        see the other dictionaries in python_files/dictionaries.py.
    """
    defaults = {}
    with open(PACKET_DIR + 'config.txt',
              'r') as configure_file:
        defaults_file = configure_file.read()
        matches = re.findall('^[ ]*([\w.]*?)\s*\\{\s*(.*?)\s*\\}',
                             defaults_file, re.MULTILINE | re.DOTALL)
        for layer in matches:
            layer_dict = {}
            for field in layer[1].splitlines():
                if field == '' or field.strip()[0] == '#':
                    continue
                field = field.split('=')
                field_values = [temp.strip() for temp in field]
                layer_dict[field_values[0]] = field_values[1]
            defaults[layer[0]] = layer_dict

    defaults['Ethernet']['src'] = read_MAC('eth0')
    defaults['IP']['src'] = get_ip_addr('eth0')
    return defaults


def get_ip_addr(interface):
    """Gets the ip address of an interface.

    Args:
        ifname (str): Name of an interface (eth0, wlan1, etc.)

    Returns:
        str: IP address of the interface, in standard IP format.

    TODO: Error checking.
    """
    return netifaces.ifaddresses(interface)[2][0]['addr']
