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
    p = scapy.rdpcap('/home/pi/Sender/sender_files/packet_files/%s' % fname)
    return p[0]


def read_MAC():
    try:
        with open('/sys/class/net/eth0/address') as file:
            return file.read().strip()
    except:
        print 'Error, cannot read MAC address'
        return '00:00:00:00:00:00'


def read_defaults():
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
    ip = netifaces.ifaddresses(ifname)[2][0]['addr']
    return '.'.join(['%03d' % int(octal) for octal in ip.split('.')])
