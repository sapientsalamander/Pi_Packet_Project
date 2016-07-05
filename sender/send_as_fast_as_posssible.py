import time
import socket

from scapy.all import *
import Adafruit_CharLCD as LCD

lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)

packet = IP(dst='10.0.24.243')/UDP(sport=7777,dport=7777)/("Hello World!")

#s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
#s.bind(('eth0',0))
#packet = Ether()/IP(dst='10.0.24.243')/ICMP()
#data = packet.build()

while(True):
   send(packet)
   time.sleep(0.5)
