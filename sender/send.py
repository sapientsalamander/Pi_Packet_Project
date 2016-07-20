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

def to_int_array(pac):
   tmp = str(pac).encode('hex')
   tmp = [x+y for x,y in zip(tmp[0::2], tmp[1::2])]
   return map(lambda x : int(x,16), tmp)
# Ether(dst='b8:27:eb:61:1b:d4',src='b8:27:eb:26:60:d0')
packet = IP(version=4,id=1,ttl=64,proto='udp',src='10.0.24.242',dst='10.0.24.243') / \
         UDP(sport=666,dport=666) / \
         Raw('This is a message. End')

number_packets_sent = 0
select_just_pressed = False

SOCKET_ADDR = '/tmp/send_socket'
c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
while True:
   try:
      c_socket.connect(SOCKET_ADDR)
      break
   except:
      time.sleep(1)

def send_packet(pac):
   c_socket.send(bytearray(to_int_array(pac)))

send_packet(packet)

def print_lcd():
   lcd.set_cursor(0,0)
   lcd.clear()
   lcd.message('# of packets\nsent: ' + str(number_packets_sent))

print_lcd()

"""while(True):
   if lcd.is_pressed(LCD.SELECT):
      if not select_just_pressed:
         select_just_pressed=True
         number_packets_sent += 1
         print_lcd()
         send(packet, iface='eth0')
   else:
      select_just_pressed = False
"""
