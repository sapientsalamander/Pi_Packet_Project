import json
import os, os.path
import socket
import string
import struct
import sys

import cherrypy
from scapy.all import *

from shared_files import SEASIDE
from shared_files import conversions

c_socket = None

def str_to_class(string):
    return reduce(getattr, string.split("."), sys.modules[__name__])

class PacketServer(object):
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
    def packet_config(self, packet_layers):
        if packet_layers == '[]':
            return

        packet_layers = json.loads(packet_layers)
        packet = Packet()

        for layer in packet_layers:
            layer_type = str_to_class(layer['layer_type'])
            temp = layer_type()
            for key in layer:
                if layer[key] != '' and key != 'layer_type':
                    setattr(temp, key, type(getattr(layer_type(), key))(layer[key]))
            packet /= temp

        packet.show()
        packet = conversions.convert_packet_int_array(packet)
        SEASIDE.send_SEASIDE(c_socket, 0, packet)
            

    @cherrypy.expose
    def command(self, command, data=None):
        if data is None:
            data = []
        SEASIDE.send_SEASIDE(c_socket, int(command), eval(data))

    @cherrypy.expose
    def command_and_respond(self, command, data=None):
        if data is None:
            data = []
        SEASIDE.send_SEASIDE(c_socket, int(command), eval(data))
        return c_socket.recv(2048)

if __name__ == '__main__':
    os.chdir('sender_files/website/')
    c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    c_socket.connect('/tmp/send_socket')
    # On Startup
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

