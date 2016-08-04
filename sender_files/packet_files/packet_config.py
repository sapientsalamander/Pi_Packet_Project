DEFAULTS = {

'Ether': {
    'dst': 'b8:27:eb:61:1b:d4',
    'ethtype': 0x0800,
},

'IP': {
    'dst': '10.0.24.243',
    'ttl': 64,
},

'TCP': {
    'sport': 4321,
    'dport': 4321,
},

'UDP': {
    'sport': 4321,
    'dport': 4321,
},

# VLAN tagging
'Dot1Q': {
    'vlan': 1,
    'id': 1,
    'prio': 0,
    'type': 0,
}

}

