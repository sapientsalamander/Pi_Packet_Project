import time

from scapy.all import *
import Adafruit_CharLCD as LCD

lcd = LCD.Adafruit_CharLCDPlate()

number_packets_sent = 0
select_just_pressed = False

lcd.set_color(0, 0, 0)
lcd.clear();
lcd.message('Number of packets sent:\n' + str(number_packets_sent))

while(True):
   if lcd.is_pressed(LCD.SELECT):
      if not select_just_pressed:
         select_just_pressed=True
         number_packets_sent += 1
         send(IP(dst='10.0.24.243')/UDP(dport=7777)/("Hello World!"), iface="eth0")
         lcd.clear()
         lcd.message('Number of packets sent:\n' + str(number_packets_sent))
   else:
      select_just_pressed = False
