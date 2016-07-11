#!/usr/bin/env python

import fcntl
import sys

# Lock to only allow one instance of this program to run
# Opens (and creates if non-existent) a file in /tmp/, and attempts to lock
# it. If it is already locked, then another instance is running, and this
# instance of the programs exits. If not, it successfully locks it and
# continues running.
pid_file = '/tmp/send.pid'
fp = open(pid_file, 'w')
try:
   fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
   print 'An instance of this program is already running'
   sys.exit(0)
# End of lock code.

import socket
import time
import thread
import os

from scapy.all import *
import Adafruit_CharLCD as LCD

# Before enums were introduced in Python, this was one such method of 'faking'
# an enum. It takes a list of identifiers, zips it from 0..n-1, where n is the
# number of identifiers passed in, and uses the type function to generate a new
# class with the aforementioned identifiers as class variables.
def enums(*sequential):
   enums = dict(zip(sequential, range(len(sequential))))
   return type('Enum', (), enums)

# Creating the class, called Screens, with variables listed below, each holding a
# value, starting from 0 to n-1.
Screens = enums('Summary', 'Payload', 'Source', 'Num')

# Used to determine which screen should currently be shown.
cur_screen = Screens.Summary

# Hold information for all screens, so screens in the background can
# still be updating and storing new information. Contains a list of tuples,
# each having two strings, representing line 0 and line 1 of the LCD for each
# type of screen there is.
screen_output = [['',''] for x in xrange(Screens.Num)]

# Abbreviations for bandwidth measuring.
BDWTH_ABBRS = ('bps', 'Kbps', 'Mbps')

# An LCD lock, to ensure that the two threads, one for port listening and
# one for bandwidth measuring, do not interfere when updating the LCD.
lcd_lock = thread.allocate_lock()

def display_loop():
   """Pull in screen_output and update screen based on which one should
   be currently up.
   """
   while True:
      for i in xrange(2):
         print_line(screen_output[cur_screen][i], i)
      time.sleep(0.7)

def print_line(message, line):
   """Print message to screen on line, multithreading safe.

   Locks the LCD so that only one thread can write to it at a time.
   Also ensures that writing to a line won't clear the entire screen.
   """
   # Pad with spaces, manually clearing the line on LCD.
   message = message.ljust(20)

   lcd_lock.acquire()

   lcd.set_cursor(0,line)
   lcd.message(message)

   lcd_lock.release()

def get_rx_bytes():
   """Return the total number of rx_bytes since startup.

   On Linux machines, there is a directory (/sys/class/net/...) that
   contains networking information about different interfaces, and we just
   pull the number of bytes received over eth0 since startup.

   Returns:
      The number of bytes received over eth0 since startup.
   """
   with open('/sys/class/net/eth0/statistics/rx_bytes', 'r') as file:
      data = file.read()
   return int(data)

def update_packet_info(packet, number_packets_received):
   """Update and print packet information to LCD, including payload, 
   and total number of packets received.

   Args:
      packet: A capture scapy packet.
      number_packets_received: Packets received since program started.
   """
   screen_output[Screens.Summary][0] = ('Rx:%3d ' % number_packets_received)

   # Grabs the payload from the scapy packet. If none is available,
   # or if packet is not a scapy packet, then it cannot parse the payload.
   try:
      screen_output[Screens.Payload][0] = packet.getlayer(Raw).load
   except AttributeError:
      screen_output[Screens.Payload][0] = 'No payload'

   # IP address
   screen_output[Screens.Source][0] = packet.getlayer(IP).src
   # MAC address
   screen_output[Screens.Source][1] = packet.getlayer(Ether).src.replace(':', '')

def update_statistics_loop():
   """Calculate the bandwidth (can be expanded to include more info) and displays 
   it on the LCD.
   """
   rx_prev = get_rx_bytes()
   time_prev = time.time()
   while True:
      rx_cur = get_rx_bytes()
      time_cur = time.time()

      # Bandwidth (bits/s) = (delta bytes / delta time) * 8 bits / byte.
      bandwidth = (rx_cur - rx_prev)/(time_cur - time_prev) * 8

      # If bandwidth > 1000, increases size of units (b -> Kb -> Mb).
      i = 0
      while bandwidth >= 1000:
         bandwidth /= 1000.0
         i += 1

      # Ex. Bw: 30.5 Kbps.
      message = 'Bw:%5.1f %s' % (bandwidth, BDWTH_ABBRS[i])

      screen_output[Screens.Summary][1] = message

      rx_prev = rx_cur
      time_prev = time_cur

      # Only update statistics once a second.
      time.sleep(1)

def listen_packets_loop():
   """Listen for packets according to filter and update display."""
   socket_addr = '/tmp/receive_socket'

   try:
      os.unlink(socket_addr)
   except OSError:
      if os.path.exists(socket_addr):
         raise

   c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
   c_socket.bind(socket_addr)
   c_socket.listen(1)
   connection, client_address = c_socket.accept()

   number_packets_received = 0

   while True:
      print 'Listening for packet'

      c_input = connection.recv(2048)
      print 'Len %d' % (len(c_input))
      print repr(c_input)

      packet = Ether(c_input) #sniff(filter = 'port 7777', count = 1)[0]
      print 'Packet:'
      print packet

      number_packets_received += 1
      update_packet_info(packet, number_packets_received)

def input_loop():
   """Listens for button presses and updates the current screen

   Each button is associated with a different screen, and so when you
   push a button, the screen that should be currently shown is changed.
   """
   global cur_screen
   while True:
      if lcd.is_pressed(LCD.UP):
         cur_screen = Screens.Summary
      elif lcd.is_pressed(LCD.DOWN):
         cur_screen = Screens.Payload
      elif lcd.is_pressed(LCD.LEFT):
         cur_screen = Screens.Source

if __name__ == '__main__':
   # Initializes LCD and turn off LED.
   lcd = LCD.Adafruit_CharLCDPlate()
   lcd.set_color(0,0,0)

   screen_output[Screens.Summary][0] = 'Awaiting packets'

   try:
      thread.start_new_thread(display_loop, ())
      thread.start_new_thread(update_statistics_loop, ())
      thread.start_new_thread(input_loop, ())
   except:
      print 'Error: ', sys.exc_info()[0]

   # Run one of the functions on the main thread, just to avoid having to create
   # another thread, and because the main thread would need to wait for the other
   # threads or the program would stop running as soon as it reaches the end.
   listen_packets_loop()
