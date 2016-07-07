#!/usr/bin/env python

import fcntl, sys

#Lock to only allow one instance of this program to run
pid_file = '/tmp/send.pid'
fp = open(pid_file, 'w')
try:
   fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
   print 'An instance of this program is already running'
   sys.exit(0)
#End of lock code

import socket, time, thread

from scapy.all import *
import Adafruit_CharLCD as LCD

def get_rx_bytes():
   with open('/sys/class/net/eth0/statistics/rx_bytes', 'r') as file:
      data = file.read()
   return int(data)

abbrs = ('bps', 'Kbps', 'Mbps')

def print_lcd(packet, number_packets_received, bandwidth):
   lcd.clear()
   lcd.message('Rx:%3d ' % number_packets_received)
   if packet:
      try:
         lcd.message(packet.getlayer(Raw).load)
      except AttributeError:
         lcd.message('No payload')

   lcd.set_cursor(0,1)

   i = 0
   while bandwidth >= 1000:
      bandwidth /= 1000.0
      i += 1
   lcd.message('Bw:%3.0f %s' % (bandwidth, abbrs[i]))

if __name__ == '__main__':
   #Initializing LCD
   lcd = LCD.Adafruit_CharLCDPlate()
   lcd.set_color(0,0,0)

   #Opening a raw socket to receive data from
   listener = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)

   number_packets_received = 0

   #How many bytes received, for bandwidth measuring
   rx_prev = get_rx_bytes()
   time_prev = time.time()

   packet = None
   lcd.message('Waiting for\npackets...')

   while True:
      packet = listener.recvfrom(7777)
      #packet = sniff(filter = 'port 7777', count = 1)[0]

      number_packets_received += 1

      rx_cur = get_rx_bytes()
      time_cur = time.time()

      print_lcd(packet, number_packets_received, (rx_cur - rx_prev)/(time_cur - time_prev) * 8)

      rx_prev = rx_cur
      time_prev = time_cur
