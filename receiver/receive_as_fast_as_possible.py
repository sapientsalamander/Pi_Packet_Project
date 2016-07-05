import socket
from datetime import datetime

from scapy.all import *
import Adafruit_CharLCD as LCD

lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)

listener = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)

number_packets_received = 0

def print_lcd():
   lcd.set_cursor(0,0)
   lcd.clear()
   #lcd.message('# of packets\nreceived: ' + str(number_packets_received))
   lcd.message('Hello World')

if __name__ == '__main__':
   previous_time = datetime.now()
   while True:
      current_time = datetime.now()
      p = listener.recvfrom(7777)
      number_packets_received += 1
      print number_packets_received, 1/(current_time - previous_time).total_seconds() * len(p)
      previous_time = current_time
