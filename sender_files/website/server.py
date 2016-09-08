"""Cherrypy webserver.

This module provides the backend for a packet generation webserver, providing
you with all your packet generation needs in this easy-to-use web interface.

All you have to do to run this server is from the root directory (where
sender_files, shared_files, etc. are located) is run this command:

python -m sender_files.website.server

Probably gonna have to run it as root.

The idea behind the implementation of this server is we have a client, which
occasionally sends us different requests. Some of these requests are for a new
page, such as index, configure_packet, send, and so on. These are html files
that each represent a different page of the UI. When the request is received
on this end, we return the page that is requested.

Then, we have requests for things like retrieving the bandwidth from the
C side, setting a new packet on the C side, and sending a general command
to the C side (start, stop, etc.). These requests may or may not have a
return. For things like getting the bandwidth, we do return the bandwidth, as
an example. These do not take the user to a new page, but have varying other
side effects.

There is a comment splitting up these two different kinds of requests, with the
former called 'page requests' and the latter called 'side-effect requests'.

TODO: Any functions that deal with taking in input should do sanitization.
"""


import copy
import json
import os
import os.path
import socket
import string
import struct
import sys
import tempfile
import threading

import cherrypy
from scapy.all import *

from shared_files import SEASIDE
from shared_files import conversions
from shared_files import computations
from sender_files.python_files import data_sanitization as ds
from sender_files.python_files import dictionaries as dicts

# A socket for interaction with the C side, and a lock to ensure that no two
# web requests can write at the same time.
c_socket = None
c_socket_lock = threading.Lock()


def str_to_class(string):
    """Takes a string, and returns the class it refers to.

    Basically the same as doing an eval('Some class'), but without the eval.
    Because those are scary. It attempts to look up the name in global space,
    and returns a reference to the class.

    Args:
        string (str): A string containing the name of a class.

    Returns:
        class: A reference to the class the string names.
    """
    print '1:', string
    print '2:', scapy_class_names[string]
    print '3:', scapy_class_names[string]['class']
    return reduce(getattr, [scapy_class_names[string]['class']], sys.modules[__name__])


def configure_packet_layers(packet_layers):
    """Takes an array of packet layers, and returns the configured packet.

    Args:
        packet_layers (JSON): Takes an array of packet layers, encoded in JSON,
            in a dictionary format. Instead of trying to explain what this
            could or could not look like, here's an easy example:
            '[
                {
                    "layer_type": "Ether",
                    "src": "",
                    "dst": ""
                },
                {
                    "layer_type": "IP",
                    "src": "",
                    "dst": "10.0.24.230",
                    "ttl": "64"
                },
                {
                    "layer_type": "UDP",
                    "sport": "4321",
                    "dport": "4321"
                }
            ]'
            keep in mind that this is all encapsulated in a string. In the
            string is an array of dictionaries, each specifying a layer type
            (ordered from lowest layer to highest layer), and any optional
            fields to configure. Not all fields will be present, the rest
            will be auto-generated. And if a field is empty, it will also
            be auto-generated.

        Returns:
            Packet: A scapy packet, with all the layers and fields configured
            as specified.
        """
    packet_layers = json.loads(packet_layers)
    packet = Packet()

    for layer in packet_layers:
        # Gets the type of layer (IP, Ether, etc) and starts building it up.
        layer_type = str_to_class(layer['layer_type'])
        temp_layer = layer_type()
        # For each field specified (src, dst, ttl, etc.), set it in the
        # packet layer.
        for key in layer:
            if layer[key] != '' and key != 'layer_type':
                # Gets the type of the field (int, str), so we can cast it
                # to its appropriate type.
                print 'Value: ', layer[key], ' | ', layer_type, ' | ', key
                try:
                    sanitized_field = ds.sanitize(layer[key], dicts.SAN_SCAPY[layer_type][key])
                except KeyError:
                    sanitized_field = layer[key]
                setattr(temp_layer, key, sanitized_field)
        # Add the configured layer to the packet.
        packet /= temp_layer
    packet.show()
    return packet


class PacketServer(object):

    # PAGE REQUESTS START HERE

    """These probably don't need too much of an explanation, but basically
    these are the page requests, the requests that lead to a user redirection
    to another page. They request the page that they want, and we return the
    page from the corresponding html file.

    As a side note, this means that when the user requests a page, it'll be
    requested as the name of the method, not the name of the file. So if they
    want the index, they link it as ex. href="index", NOT href="index.html".
    """

    @cherrypy.expose
    def index(self):
        return open('index.html')

    @cherrypy.expose
    def construct_packet(self):
        return open('construct_packet.html')

    @cherrypy.expose
    def configure_speed(self):
        return open('configure_speed.html')

    @cherrypy.expose
    def send(self):
        return open('send.html')

    @cherrypy.expose
    def load_pcap(self):
        return open('load_pcap.html')

    # PAGE REQUESTS END HERE

    # SIDE-EFFECT REQUESTS START HERE

    @cherrypy.expose
    def get_configurable_layers(self):
        """Reads the packet configuration file and returns the different
        layers that we support, along with the configurable fields.

        Returns:
            JSON: Dictionary of layers to their fields and default values.
                As an example:
                {
                    'UDP':
                    {
                        'dport': '4321',
                        'sport': '4321'
                    },

                    '802.1Q':
                    {
                        'vlan': '1',
                        'id': '0',
                        'prio': '0'
                    }
                }
        """
        return json.dumps(defaults)

    @cherrypy.expose
    def packet_config(self, packet_layers):
        """Takes the configured layers and sends it to the C side.

        Takes the packet_layers (in a JSON format, see configure_packet_layers
        above), turns it into a legitimate Scapy packet, and then sends it to
        the C side.

        Args:
            packet_layers (JSON): The packet layers in a string of JSON. See
                configure_packet_layers above for an example of what this would
                look like.
        """
        # If the user didn't even configure a packet, but just clicked the
        # "Done configuring" button like the silly user they are.
        if packet_layers == '[]':
            return
        # Turn it into a Scapy packet.
        packet = configure_packet_layers(packet_layers)
        # Turn it into the corresponding int array.
        packet = conversions.convert_packet_int_array(packet)
        # Send it to the C side, using the SEASIDE format.
        SEASIDE.send_SEASIDE(c_socket, c_socket_lock, 0, packet)

    @cherrypy.expose
    def command(self, command, data):
        """Sends the C side a command.

        The flags can be found in SEASIDE.

        Args:
            command (int): The flag to send to the C side.
            data (str): Any additional data to send with the flag.

        TODO: Clean up the types / documentation.
        TODO: Remove the eval.
        """
        SEASIDE.send_SEASIDE(c_socket, c_socket_lock, int(command), eval(data))

    @cherrypy.expose
    def command_and_respond(self, command, size):
        """Sends a command to the C side, and gets the response.

        Some flags are used for getting info from the C side, such as getting
        bandwidth, or the structure of the current packet.

        Args:
            command (int): The flag to send to the C side.
            size (str): The size of the reponse that you're expecting. See
                https://docs.python.org/2/library/struct.html for different
                sizes.

        Returns:
            str: The response that was received, encoded in hex format. The
                format looks like this: 12abc4394fa. I.e. there's no dashes or
                spaces in between each byte, and no \\x or equivalent. As a
                sidenote, that \\x used to have only one slash, but it threw
                errors, because apparently it couldn't be parsed...

        TODO: What if the value returned isn't an int? Make it more generic.
        """
        temp = SEASIDE.request_SEASIDE(c_socket, c_socket_lock, int(command))
        temp = struct.unpack('=' + size, temp)[0]
        temp = struct.pack('!' + size, temp)
        return temp.encode('hex')

    @cherrypy.expose
    def save_packet_to_file(self, pcap_filename, packet_layers):
        """Takes a packet and saves it to the pcap_files/ directory.

        Used for when you're done configuring a packet and want to save
        it so you can just pull it up whenever.

        Args:
            pcap_filename (str): Name of the file to save it to.
            packet_layers (JSON): The packet layers, which will be assembled
                to a whole packet, and then saved as a pcap file. See
                configure_packet_layers above for the format of this.
        """
        if pcap_filename == '' or packet_layers == '[]':
            return
        packet = configure_packet_layers(packet_layers)
        wrpcap('pcap_files/' + pcap_filename, packet)

    @cherrypy.expose
    def return_pcap_file(self, packet_layers):
        """Contructs a packet, makes a pcap file, and returns the contents.

        Takes a bunch of packet layers, and constructs a packet as you would
        normally. When finished, saves it to a temporary pcap file (doing the
        best with what we got), read that file, and returns the contents of
        the file.

        Args:
            packet_layers (JSON): The packet layers, which will be assembled
                to a whole packet, and then saved as a pcap file. See
                configure_packet_layers above for the format of this.
        """
        if packet_layers == '[]':
            return
        packet = configure_packet_layers(packet_layers)
        pcap_filename = '/tmp/temp_pcap_file.pcap'
        wrpcap(pcap_filename, packet)
        with open(pcap_filename, 'r') as pcap_file:
            data = pcap_file.read()
        return data

    @cherrypy.expose
    def get_pcap_filenames(self):
        """Returns the list of pcap filenames stored in pcap_files.

        Used for displaying to the user, so they can choose which one to load.
        The idea is that the name will be clear enough to that you know
        what's in the file.

        Returns:
            JSON: List of filenames in an array, encoded in JSON format.
        """
        return json.dumps(os.listdir('pcap_files'))

    @cherrypy.expose
    def load_pcap_file(self, filename):
        if filename == '':
            return
        packet = rdpcap('pcap_files/' + filename)[0]
        packet = conversions.convert_packet_int_array(packet)
        SEASIDE.send_SEASIDE(c_socket, c_socket_lock, 0, packet)

    @cherrypy.expose
    def upload_pcap_file(self, file_data):
        """Takes a pcap file, and sends it to the C side for sending.

        Args:
            file_data (File): A CherryPy representation of a file.
        """
        pcap_file = tempfile.NamedTemporaryFile()
        pcap_file.write(bytearray(file_data.file.read()))
        pcap_file.seek(0)
        packet = rdpcap(pcap_file.name)[0]
        packet = conversions.convert_packet_int_array(packet)
        SEASIDE.send_SEASIDE(c_socket, c_socket_lock, 0, packet)

        # SIDE-EFFECT REQUESTS END HERE

if __name__ == '__main__':
    os.chdir('sender_files/website/')
    c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    while True:
        try:
            c_socket.connect('/tmp/send_socket')
            break
        except:
            time.sleep(1)
            print 'Trying to connect...'

    global defaults
    global scapy_class_names
    defaults = computations.read_defaults()
    scapy_class_names = copy.deepcopy(defaults)

    del defaults['Other']
    for layer in defaults:
        defaults[layer].pop('class', None)

    print 'STUFF: ', scapy_class_names

    current_dir = os.path.dirname(os.path.abspath(__file__)) + os.path.sep
    config = {
        'global': {
            'server.socket_host': '0.0.0.0',
        },

        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': current_dir
        },

        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'public'
        }
    }
    webapp = PacketServer()
    cherrypy.quickstart(webapp, '/', config)
