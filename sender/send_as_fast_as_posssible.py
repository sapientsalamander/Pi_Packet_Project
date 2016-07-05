import time

from scapy.all import *
import Adafruit_CharLCD as LCD

lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)

number_packets_sent = 0
select_just_pressed = False

def print_lcd():
   lcd.clear()
   lcd.message('# of packets\nsent: ' + str(number_packets_sent))

if __name__ == '__main__':
   while(True):
      send(IP(dst='10.0.24.243')/UDP(dport=7777)/("Hello World!"), iface="eth0")
      number_packets_sent += 1
      print number_packets_sent
