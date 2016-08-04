import json
import os, os.path
import socket
import string
import struct
import sys
import threading

import cherrypy
from scapy.all import *

from shared_files import SEASIDE
from shared_files import conversions

c_socket = None
c_socket_lock = threading.Lock()

def str_to_class(string):
    return reduce(getattr, string.split("."), sys.modules[__name__])

def configure_packet_layers(packet_layers):
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
    def send(self):
        return open('send.html')
 

    @cherrypy.expose
    def packet_config(self, packet_layers):
        if packet_layers == '[]':
            return

        packet = configure_packet_layers(packet_layers)
        packet = conversions.convert_packet_int_array(packet)
        SEASIDE.send_SEASIDE(c_socket, c_socket_lock, 0, packet)
            

    @cherrypy.expose
    def command(self, command, data=None):
        if data is None:
            data = []
        SEASIDE.send_SEASIDE(c_socket, c_socket_lock, int(command), eval(data))

    @cherrypy.expose
    def command_and_respond(self, command, size):
        print 'COMMAND_AND_RESPOND'
        temp = SEASIDE.request_SEASIDE(c_socket, c_socket_lock, int(command))
        print temp, ' ', len(temp), ' ', repr(temp)
        temp = struct.unpack('=' + size, temp)[0]
        temp = struct.pack('!' + size, temp)
        return temp.encode('hex')


    @cherrypy.expose
    def save_packet_to_file(file_name, packet_layers):
        if file_name == '':
            return
        packet = configure_packet_layers(packet_layers)
        wrpcap('pcap_files/' + file_name, packet)


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

