from shared_files import computations
import scapy.all as scapy
import data_sanitization as ds
from functools import partial

DEFAULTS = computations.read_defaults()

# TODO Stop duplicating sanitization function lists 

LAYER = {

    scapy.Ether: {
        'src': '%h%h%h%h%h%h-%h%h%h%h%h%h',
        'dst': '%h%h%h%h%h%h-%h%h%h%h%h%h',
        'type': '0x%h%h%h%h',
    },

    scapy.IP: {
        'src': '%i%i%i.%i%i%i.%i%i%i.%i%i%i',
        'dst': '%i%i%i.%i%i%i.%i%i%i.%i%i%i',
        'ttl': '%i%i%i',
    },

    scapy.TCP: {
        'sport': '%i%i%i%i',
        'dport': '%i%i%i%i',
        # TODO Flags
    },

    scapy.UDP: {
        'sport': '%i%i%i%i',
        'dport': '%i%i%i%i',
    },

    scapy.Dot1Q: {
        'vlan': '%i%i%i%i',
        'prio': '%i',
        'type': '0x%h%h%h%h',
        'id': '%i',
    },

}



# LCD to Scapy/Config
SAN_SCAPY = {

    scapy.Ether: { # TODO Add support for other formats instead of removing ':'
        'src': [partial(ds.remove_char, char='-'), partial(ds.remove_char, char=':'), partial(ds.add_mult, char=':', step=2)],
        'dst': [partial(ds.remove_char, char='-'), partial(ds.remove_char, char=':'), partial(ds.add_mult, char=':', step=2)],
        'type': [partial(int, base=16)]
                           
    },

    scapy.IP: {
        'src': [partial(ds.split, char='.'), partial(map, partial(ds.strip, minimum='0', chars='0')), partial(ds.join, char='.')],
        'dst': [partial(ds.split, char='.'), partial(map, partial(ds.strip, minimum='0', chars='0')), partial(ds.join, char='.')],
        'ttl': [int]
    },

    scapy.TCP: {
        'sport': [int],
        'dport': [int]
        # TODO Flags
    },

    scapy.UDP: {
        'sport': [int],
        'dport': [int]
    },

    scapy.Dot1Q: {
        'vlan': [int],
        'prio': [int],
        'type': [partial(int, base=16)],
        'id': [int]
    }

}



# Scapy/Config to LCD
SAN_LCD = {

    scapy.Ether: {
        'src': [partial(ds.remove_char, char=':'), partial(ds.add_single, char='-', index=6)],
        'dst': [partial(ds.remove_char, char=':'), partial(ds.add_single, char='-', index=6)],
        'type': [partial(int, base=0), hex, partial(ds.trim, length=2), partial(ds.pad, length=4, char='0')]
    },

    scapy.IP: {
        'src': [partial(ds.split, char='.'), partial(map, partial(ds.pad, length=3, char='0')), partial(ds.join, char='.')],
        'dst': [partial(ds.split, char='.'), partial(map, partial(ds.pad, length=3, char='0')), partial(ds.join, char='.')],
        'ttl': [partial(ds.pad, length=3, char='0')]
    },

    scapy.TCP: {
        'sport': [partial(ds.pad, length=4, char='0')],
        'dport': [partial(ds.pad, length=4, char='0')]
        # TODO Flags
    },

    scapy.UDP: {
        'sport': [partial(ds.pad, length=4, char='0')],
        'dport': [partial(ds.pad, length=4, char='0')]
    },

    scapy.Dot1Q: {
        'vlan': [partial(ds.pad, length=4, char='0')],
        'prio': [partial(ds.pad, length=1, char='0')],
        'type': [partial(int, base=0), hex, partial(ds.trim, length=2), partial(ds.pad, length=4, char='0')],
        'id': [partial(ds.pad, length=1, char='0')]
    }

}

