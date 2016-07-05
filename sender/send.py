#!/usr/bin/env python
import time

from scapy.all import *
import Adafruit_CharLCD as LCD

lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)

number_packets_sent = 0
select_just_pressed = False

def print_lcd():
   lcd.set_cursor(0,0)
   lcd.clear()
   lcd.message('# of packets\nsent: ' + str(number_packets_sent))

if __name__ == '__main__':
   print_lcd()
   while(True):
      if lcd.is_pressed(LCD.SELECT):
         if not select_just_pressed:
            select_just_pressed=True
            number_packets_sent += 1
            send(IP(dst='10.0.24.243')/UDP(dport=7777)/ICMP()/"Hello World!", iface="eth0")
            print_lcd()
      else:
         select_just_pressed = False
