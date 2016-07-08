#!/usr/bin/env python

import time
import fcntl
import sys
import socket

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

#s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
#s.bind(('eth0', 0))
pkt = IP(dst='10.0.24.243')/UDP(sport=7777,dport=7777)/("Hello World!")
#pkt = Ether()/IP(dst='10.0.24.243')/UDP()
#data = pkt.build()

number_packets_sent = 0
select_just_pressed = False

def print_lcd():
   lcd.set_cursor(0,0)
   lcd.clear()
   lcd.message('# of packets\nsent: ' + str(number_packets_sent))

print_lcd()

while(True):
   if lcd.is_pressed(LCD.SELECT):
      if not select_just_pressed:
         select_just_pressed=True
         number_packets_sent += 1
         send(pkt, iface='eth0')
         print_lcd()
   else:
      select_just_pressed = False
