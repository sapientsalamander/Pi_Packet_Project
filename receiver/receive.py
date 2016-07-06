#!/usr/bin/env python

import socket, fcntl, sys

#Lock to only allow one instance of this program to run
pid_file = '/tmp/send.pid'
fp = open(pid_file, 'w')
try:
   fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
   print 'An instance of this program is already running'
   sys.exit(0)
#End of lock code

from scapy.all import *
import Adafruit_CharLCD as LCD

lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)

listener = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)

number_packets_received = 0

def print_lcd(packet):
   lcd.clear()
   lcd.message('# received: ' + str(number_packets_received) + '\n')
   if packet:
      lcd.message(packet.getlayer(Raw).load)

if __name__ == '__main__':
   packet = None
   while True:
      print_lcd(packet)
      #packet = listener.recvfrom(7777)
      packet = sniff(filter = 'port 7777', count = 1)[0]
      number_packets_received += 1
