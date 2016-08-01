import os, os.path
import string
import socket

import cherrypy
from scapy.all import *

#from shared_files import SEASIDE
#from shared_files import conversions

c_socket = None

def slice_html(dst, src, tag):
    i = dst.find(tag)
    j = dst.find('>', i)
    if j == -1:
        return src
    return dst[:j+1] + src + dst[j+1:]

class PacketServer(object):
    @cherrypy.expose
    def index(self):
        return open('index.html')
 

    @cherrypy.expose
    def packet_config(self, parameters):
        if parameters == '[]':
            return
        par = eval(parameters)
        packet = Packet()
        for layer in par:
            temp = eval(layer[0])()
            for key in layer[1]:
                setattr(temp, key, type(eval(layer[0] + '().' + key))(layer[1][key]))
            packet /= temp
        packet = conversions.convert_packet_int_array(packet)
        SEASIDE.send_SEASIDE(c_socket, 0, packet)
            

    @cherrypy.expose
    def command(self, command):
        SEASIDE.send_SEASIDE(c_socket, int(command))

if __name__ == '__main__':
    #c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    #c_socket.connect('/tmp/send_socket')
    config = {
        'global': {
            'server.socket_host': '0.0.0.0',
        },

        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },

        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
   }
    webapp = PacketServer()
    cherrypy.quickstart(webapp, '/', config)

