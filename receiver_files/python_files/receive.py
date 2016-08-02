#!/usr/bin/env python

import fcntl
import sys
import os
import socket
import time
import thread

import scapy.all as scapy
import psutil
import Adafruit_CharLCD as LCD
from shared_files import shared_functions

# Creating the class, called Screens, with variables listed below, each
# holding a value, starting from 0 to n-1.
Screens = shared_functions.enums(
            'Summary', 'Payload', 'Source', 'CPU', 'Num')

# Used to determine which screen should currently be shown.
cur_screen = Screens.Summary

# Hold information for all screens, so screens in the background can
# still be updating and storing new information. Contains a list of tuples,
# each having two strings, representing line 0 and line 1 of the LCD for each
# type of screen there is.
screen_output = [['',''] for x in xrange(Screens.Num)]

# The file used to initialize the socket to communicate with C program.
SOCKET_ADDR = '/tmp/receive_socket'

# An LCD lock, to ensure that the two threads, one for port listening and
# one for bandwidth measuring, do not interfere when updating the LCD.
lcd_lock = thread.allocate_lock()

packet = scapy.Ether()

def display_LED(bandwidth, bw_unit):
   color = (0,0,0)
   if bw_unit == 'bps' and bandwidth == 0:
      color = (0, 0, 0)
   elif bw_unit == 'bps':
      color = (0, 1, 0)
   elif bw_unit == 'Kbps':
      color = (0, 0, 1)
   elif bw_unit == 'Mbps':
      color = (1, 0, 0)

   with lcd_lock:
      lcd.set_color(*color)

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
      string_payload = packet.getlayer(scapy.Raw).load
      index = string_payload.find('\n')
      if index == -1:
         screen_output[Screens.Payload][0] = string_payload
      else:
         screen_output[Screens.Payload][0] = string_payload[:index]
         screen_output[Screens.Payload][1] = string_payload[index+1:]
   except AttributeError:
      screen_output[Screens.Payload][0] = 'No payload'

   # IP address
   screen_output[Screens.Source][0] = packet.getlayer(scapy.IP).src
   # MAC address
   eth_out = packet.getlayer(scapy.Ether).src
   screen_output[Screens.Source][1] = eth_out.replace(':', '')

def update_statistics_loop():
   """Calculate the bandwidth and cpu usage (can be expanded to include
   more info) and displays it on the LCD.
   """
   rx_cur = shared_functions.get_rx_tx_bytes('rx')
   time_cur = time.time()

   while True: 
      rx_prev = rx_cur
      time_prev = time_cur
      
      rx_cur = shared_functions.get_rx_tx_bytes('rx')
      # TODO: Find actual received frame size
      time_cur = time.time()

      screen_output[Screens.CPU][0] = 'CPU Usage: %4.1f%%' % \
                                      (psutil.cpu_percent())
      cores = psutil.cpu_percent(percpu=True)
      screen_output[Screens.CPU][1] = '%2.0f%% %2.0f%% %2.0f%% %2.0f%%' % \
                                      tuple(cores)

      d_bytes = rx_cur - rx_prev
      try:
         num_packets = d_bytes / (len(packet) - 14)
      except (ZeroDivisionError):
         print 'Zero'
         num_packets = 0

      # Bandwidth (bits/s) = (delta bytes / delta time) * 8 bits / byte.
      bandwidth = (num_packets * len(packet))/(time_cur - time_prev) * 8
      bandwidth, bw_unit = shared_functions.calculate_bandwidth(bandwidth)

      display_LED(bandwidth, bw_unit)

      # Ex. Bw: 30.5 Kbps.
      message = 'Bw:%5.1f %s' % (bandwidth, bw_unit)

      screen_output[Screens.Summary][1] = message


      time.sleep(1)

def listen_packets_loop():
   """Initializes the socket used to interface with the C program, and listen
   for any incoming packets. When we hear one, parse it with scapy and update
   the display to show information about packet.
   """
   global packet
   # If file descriptor already exists from previous session, we delete it.
   try:
      os.unlink(SOCKET_ADDR)
   except OSError:
      if os.path.exists(SOCKET_ADDR):
         raise

   # Create the actual socket at the defined address.
   c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
   c_socket.bind(SOCKET_ADDR)
   print 'Successfully created socket'

   print 'Waiting for C program to connect'
   # Listen for the C program to connect
   c_socket.listen(1)
   connection, client_address = c_socket.accept()
   print 'C program connected'

   number_packets_received = 0

   print 'Listening for packets...'

   while True:

      c_input = connection.recv(2048)

      number_packets_received += 1

      print 'Received packet [%d]' % (number_packets_received)

      # Parse packet with scapy so we can pull it apart easier.
      packet = scapy.Ether(c_input)

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
      elif lcd.is_pressed(LCD.RIGHT):
         cur_screen = Screens.CPU

if __name__ == '__main__':
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
   
   # Initializes LCD and turn off LED.
   lcd = LCD.Adafruit_CharLCDPlate()
   lcd.set_color(0,0,0)
   lcd.clear()

   screen_output[Screens.Summary][0] = 'Awaiting packets'

   try:
      thread.start_new_thread(display_loop, ())
      thread.start_new_thread(update_statistics_loop, ())
      thread.start_new_thread(input_loop, ())
   except:
      print 'Error: ', sys.exc_info()[0]

   # Run one of the functions on the main thread, just to avoid having to
   # create another thread, and because the main thread would need to wait
   # for the other threads or the program would stop running as soon as it 
   # reaches the end.
   listen_packets_loop()
