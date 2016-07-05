import socket

from scapy.all import *
import Adafruit_CharLCD as LCD

lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)

listener = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)

number_packets_received = 0

def print_lcd():
   lcd.clear()
   lcd.message('# of packets\nreceived: ' + str(number_packets_received))

if __name__ == '__main__':
   while True:
      print_lcd()
      print listener.recvfrom(7777), '\n', type(listener)
      number_packets_received += 1
