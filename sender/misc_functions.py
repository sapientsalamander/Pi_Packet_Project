#!/usr/bin/env python
import socket

def to_int_array(pac):
   tmp = str(pac).encode('hex')
   tmp = [x+y for x,y in zip(tmp[0::2], tmp[1::2])]
   return map(lambda x : int(x,16), tmp)

def split_MAC(address):
   mac = []
   address = address.replace("-", "")
   for i in xrange(0, len(address), 2):
      mac.append(address[i:i+2])
      mac.append(":")
   mac = mac[:-1]
   return "".join(mac)

def send_packet(packet, c_socket):
   c_socket.send(bytearray(to_int_array(packet)))

def get_tx():
   with open('/sys/class/net/eth0/statistics/tx_bytes', 'r') as file:
      tx_data = file.read()
   return tx_data
