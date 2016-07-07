import time
import Adafruit_CharLCD as LCD
from scapy.all import *

lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)
lcd.blink(True)

lcd.create_char(1, [0, 4, 14, 31,  4,  4, 4, 0]) #Up arrow
lcd.create_char(2, [0, 4,  4,  4, 31, 14, 4, 0]) #Down arrow
lcd.create_char(3, [0, 4, 12, 31, 12,  4, 0, 0]) #Left arrow
lcd.create_char(4, [0, 4,  6, 31,  6,  4, 0, 0]) #Right arrow
lcd.create_char(5, [0, 1,  3, 22, 28,  8, 0, 0]) #Checkmark

ip = list('000.000.000.000') 
cursor = 0

def print_LCD():
   lcd.clear()
   lcd.message('IP:\n' + "".join(ip))
   lcd.set_cursor(cursor, 1)

def inc_digit():  #Increase current digit within 0-9
   num = int(ip[cursor])
   num += 1
   if num > 9:
      num = 0
   elif num < 0:
      num = 9
   ip[cursor] = str(num)

def dec_digit():  #Decrease current digit within 0-9
   num = int(ip[cursor])
   num -= 1
   if num > 9:
      num = 0
   elif num < 0:
      num = 9
   ip[cursor] = str(num)

def rmv_leading_zeros(ip): #Remove leading zeros from entered IP
   strIP = "".join(ip)
   strIP = strIP.split(".")
   numIP = []
   rmvdIP = ""
   for octet in strIP:
      numIP.append(int(octet))
   for octet in numIP:
      rmvdIP += str(octet)
      rmvdIP += "."
   rmvdIP = rmvdIP[:-1]
   return rmvdIP

print_LCD()

while True: #sleep functions ensure single presses are counted once
   if lcd.is_pressed(LCD.UP):
      inc_digit()
      print_LCD()
      time.sleep(0.1)
   if lcd.is_pressed(LCD.DOWN):
      dec_digit()
      print_LCD()
      time.sleep(0.1)
   if lcd.is_pressed(LCD.LEFT):
      cursor -= 1
      if IP[cursor] == ".": #Periods do not need to be changed
         cursor -= 1
      print_LCD()
      time.sleep(0.1)
   if lcd.is_pressed(LCD.RIGHT):
      cursor += 1
      if IP[cursor] == ".":
         cursor += 1
      print_LCD()
      time.sleep(0.1)
   if lcd.is_pressed(LCD.SELECT):
      break

rmvd = rmv_leading_zeros(ip)
pkt = IP(dst = '10.0.24.243') / UDP(sport = 7777, dport = 7777)# / Raw("Hello world")
pktct = 0
lcd.clear()
lcd.message('IP: ' + rmvd + '\n' + 'pkts sent: ' +str(pktct)) 
while True:
   if lcd.is_pressed(LCD.SELECT):
      send(pkt)
      pktct += 1
      lcd.clear()
      lcd.message('IP: ' + rmvd + '\n' + 'pkts sent: ' +str(pktct)) 
   if lcd.is_pressed(LCD.UP):
      break
