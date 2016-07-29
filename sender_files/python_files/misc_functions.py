#!/usr/bin/env python
import socket

def int_array(pac):
   """Converts a packet into an array of integers."""
   tmp = str(pac).encode('hex')
   tmp = [x+y for x,y in zip(tmp[0::2], tmp[1::2])]
   return map(lambda x : int(x,16), tmp)

def split_MAC(address):
   """Converts a MAC address from form ffffff-ffffff to ff:ff:ff:ff:ff:ff"""
   mac = []
   address = address.replace("-", "")
   for i in xrange(0, len(address), 2):
      mac.append(address[i:i+2])
      mac.append(":")
   mac = mac[:-1]
   return "".join(mac)

def send_SEASIDE(c_socket, SEASIDE_flag, pkt='', sleep_time=0):
   """Sends a SEASIDE packet through the socket.
   
   SEASIDE_flag - indicator for the type of data to be sent.
      0 - Packet. Requires a packet be passed also
      1 - Start signal
      2 - Stop signal
      3 - Set delay. If no delay is passed, it will remove the delay.

   Converts the packet to an int array and the int array of data (including
   flag and size information) to a byte array, and then sends it through the
   provided socket.
   """
   
   if SEASIDE_flag == 0: # Packet signal
      if pkt == '':
         print 'Error: no packet given'
      else:
         c_socket.send(bytearray([SEASIDE_flag, 0, len(pkt)]
                                     + int_array(pkt)))
   elif SEASIDE_flag == 1: # Start signal
      c_socket.send(bytearray([SEASIDE_flag, 0, 0]))
   elif SEASIDE_flag == 2: # Stop signal
      c_socket.send(bytearray([SEASIDE_flag, 0, 0]))
   elif SEASIDE_flag == 3: # Set delay
      c_socket.send(bytearray([SEASIDE_flag, 0, 1, sleep_time]))
   else:
      print 'Error: invalid SEASIDE flag'

def get_tx():
   """Returns the number of bytes sent since startup."""
   with open('/sys/class/net/eth0/statistics/tx_bytes', 'r') as file:
      tx_data = file.read()
   return int(tx_data)

def get_speed(pps):
   """Calculates a delay between packets given the desired number of packets
   per second.

   pps - desired number of packets per second

   Returns the number of whole seconds and microseconds between packets
   as a tuple.
   """
   seconds = 0
   useconds = (1.0 / pps) * 1000000
   while useconds >= 1000000:
      useconds  -= 1000000
      seconds += 1 
   return (int(seconds), int(useconds))

def enums(*sequential):
   """ Takes a list of identifiers and zips it from 0...n-1, using the type
   function to generate a new class containing the identifiers as variables.


   Before enums were introduced in Python, this was one such method of 'faking'
   an enum. It takes a list of identifiers, zips it from 0..n-1, where n is the
   number of identifiers passed in, and uses the type function to generate a new
   class with the aforementioned identifiers as class variables.

   sequential - list of identifiers
   
   returns the class containing the enumerated identifiers.
   """
   enums = dict(zip(sequential, range(len(sequential))))
   return type('Enum', (), enums)
