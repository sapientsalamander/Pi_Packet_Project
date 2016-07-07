#!/usr/bin/env python

import fcntl, sys

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

import socket, time, thread

from scapy.all import *
import Adafruit_CharLCD as LCD

# Abbreviations for bandwidth measuring.
UNIT_ABBRS = ('bps', 'Kbps', 'Mbps')

# An LCD lock, to ensure that the two threads, one for port listening and
# one for bandwidth measuring, do not interfere when updating the LCD.
lcd_lock = thread.allocate_lock()

def print_line(message, line):
   """Print message to screen on line, multithreading safe

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
   pull the number of bytes received over eth0 since startup
   """
   with open('/sys/class/net/eth0/statistics/rx_bytes', 'r') as file:
      data = file.read()
   return int(data)

def update_packet_info(packet, number_packets_received):
   """Update and print packet information to LCD, including payload, 
   and total number of packets received.

   Args:
      packet: a capture scapy packet
      number_packets_received: packets received since program started.
   """
   message = ('Rx:%3d ' % number_packets_received)

   # Grabs the payload from the scapy packet. If none is available,
   # or if packet is not a scapy packet, then it cannot parse the payload.
   if packet:
      try:
         message += packet.getlayer(Raw).load
      except AttributeError:
         message += 'No payload'

   print_line(message, 0)

def update_statistics():
   """Calculate the bandwidth and displays it on the LCD."""
   rx_prev = get_rx_bytes()
   time_prev = time.time()
   while True:
      rx_cur = get_rx_bytes()
      time_cur = time.time()

      # Bandwidth (bits/s) = (delta bytes / delta time) * 8 bits / byte.
      bandwidth = (rx_cur - rx_prev)/(time_cur - time_prev) * 8

      # If > 1000, increases size of units (b -> Kb -> Mb).
      i = 0
      while bandwidth >= 1000:
         bandwidth /= 1000.0
         i += 1

      # Ex. Bw: 30.5 Kbps.
      message = 'Bw:%5.1f %s' % (bandwidth, UNIT_ABBRS[i])

      print_line(message, 1)

      rx_prev = rx_cur
      time_prev = time_cur

      # Only update statistics once a second.
      time.sleep(1)

def listen_packets():
   """Listen for packets according to filter and update display."""
   number_packets_received = 0
   while True:
      # Listen for one packet, and since sniff returns a list, take
      # the first element
      packet = sniff(filter = 'port 7777', count = 1)[0]

      number_packets_received += 1

      update_packet_info(packet, number_packets_received) 

if __name__ == '__main__':
   # Initializing LCD and turn off LED.
   lcd = LCD.Adafruit_CharLCDPlate()
   lcd.set_color(0,0,0)

   print_line('Awaiting packets', 0)

   try:
      thread.start_new_thread(update_statistics, ())
   except:
      print 'Error: ', sys.exc_info()[0]

   listen_packets()
