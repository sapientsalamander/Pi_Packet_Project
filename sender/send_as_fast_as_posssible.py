import time
import socket

from scapy.all import *
import Adafruit_CharLCD as LCD

lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)

number_packets_sent = 0
select_just_pressed = False

#packet = IP(dst='10.0.24.243')/UDP(sport=7777,dport=7777)/("Hello World!")

s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
s.bind(('eth0',0))
packet = Ether()/IP(dst='10.0.24.243')/ICMP()
data = packet.build()

def print_lcd():
   lcd.clear()
   lcd.message('# of packets\nsent: ' + str(number_packets_sent))

if __name__ == '__main__':
   while(True):
      s.send(data)
