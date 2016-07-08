#!/usr/bin/env python

import time
import fcntl
import sys

import Adafruit_CharLCD as LCD
from scapy.all import *

# Lock to only allow one instance of this program to run
pid_file = '/tmp/send.pid'
fp = open(pid_file, 'w')
try:
   fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
   print 'An instance of this program is already running'
   sys.exit(0)
# End of lock code


lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)
lcd.blink(True)


def print_payload(payloads, select):
   """Print the selected payload to the LCD."""

   lcd.clear()
   lcd.message('Payload:\n' + payloads[select])

def print_IP(ip, cursor): 
   """Print the IP address to the LCD screen.

   ip -- list containing an IP address
   """   
   
   lcd.clear()
   lcd.message('IP:\n' + "".join(ip))
   lcd.set_cursor(cursor, 1)

def print_port(line, srcpt, dstpt, cursor):
   """Prints source and destination ports to the LCD screen.
   
   line -- the line onscreen of the port being configured
   """   

   lcd.clear()
   lcd.message('Src Port: ' + "".join(srcpt) + '\nDst Port: ' + "".join(dstpt))
   lcd.set_cursor(cursor + 10, line) #+10 to skip over text 

def inc_digit(lst, cursor):
   """Increase the digit under the cursor by 1, looping through 0-9. 
      
   lst -- list containing numeric characters only
   """

   num = int(lst[cursor])
   num += 1             
   if num > 9:
      num = 0
   elif num < 0:
      num = 9
   lst[cursor] = str(num)

def dec_digit(lst, cursor):
   """Decrease the digit under the cursor by 1, looping through 0-9.

   lst -- list containing numeric characters only
   """

   num = int(lst[cursor])
   num -= 1
   if num > 9:
      num = 0
   elif num < 0:
      num = 9
   lst[cursor] = str(num)

def rmv_leading_zerosIP(ip):
   """Removes leading zeros from an IP address.

   ip - list containing only numeric characters and periods
   
   returns a string containing the IP address without leading zeros
   """
   
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

def rmv_leading_zerosPORT(port): 
   """Removes leading zeros from UDP port numbers.

   port -- list containing only numeric characters
   returns an integer of the provided port  
   """
   strPort = "".join(port)
   numPort = int(strPort)
   return numPort


ip = list('000.000.000.000')
payloads = ['Hello World!', 'foo', 'bar', '']
srcpt = list('0000') 
dstpt = list('0000') 
cursor = 0


# Inputting IP address
print_IP(ip, cursor)
while True: 
   if lcd.is_pressed(LCD.UP):
      inc_digit(ip, cursor)
      print_IP(ip, cursor)
      time.sleep(0.1) # To prevent duplicate presses
   if lcd.is_pressed(LCD.DOWN):
      dec_digit(ip, cursor)
      print_IP(ip, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.LEFT):
      cursor -= 1
      if cursor < 0: # Prevent cursor from leaving screen
         cursor = 0
      if ip[cursor] == ".": # Skip over periods
         cursor -= 1
      print_IP(ip, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.RIGHT):
      cursor += 1
      if cursor > 14:   # IP uses characters 0-14, leaving one blank
         cursor = 14
      if ip[cursor] == ".":
         cursor += 1
      print_IP(ip, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.SELECT):
      time.sleep(0.1)
      break
ip = rmv_leading_zerosIP(ip)
# End IP input


# Inputting source port
cursor = 0
print_port(0, srcpt, dstpt, cursor)
while True:
   if lcd.is_pressed(LCD.UP):
      inc_digit(srcpt, cursor)
      print_port(0, srcpt, dstpt, cursor) 
      time.sleep(0.1)
   if lcd.is_pressed(LCD.DOWN):
      dec_digit(srcpt, cursor)
      print_port(0, srcpt, dstpt, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.LEFT):
      cursor -= 1
      if cursor < 0:
         cursor = 0
      print_port(0, srcpt, dstpt, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.RIGHT):
      cursor += 1
      if cursor > 3:
         cursor = 3
      print_port(0, srcpt, dstpt, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.SELECT):
      time.sleep(0.1)
      break
# Do not remove leading zeros until both ports are entered
# print_port() requires both be lists

# Inputting destination port
cursor = 0
print_port(1, srcpt, dstpt, cursor)
while True:
   if lcd.is_pressed(LCD.UP):
      inc_digit(dstpt, cursor)
      print_port(1, srcpt, dstpt, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.DOWN):
      dec_digit(dstpt, cursor)
      print_port(1, srcpt, dstpt, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.LEFT):
      cursor -= 1
      if cursor < 0:
         cursor = 0
      print_port(1, srcpt, dstpt, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.RIGHT):
      cursor += 1
      if cursor > 3:
         cursor = 3
      print_port(1, srcpt, dstpt, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.SELECT):
      time.sleep(0.1)
      break
dstpt = rmv_leading_zerosPORT(dstpt)
srcpt = rmv_leading_zerosPORT(srcpt)
# End port input

# Choose payload
select = 0
print_payload(payloads, select)
while True:
   if lcd.is_pressed(LCD.UP):
      select += 1
      if select > 3:
         select = 0
      print_payload(payloads, select)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.DOWN):
      select -= 1
      if select < 0:
         select = 3
      print_payload(payloads, select)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.SELECT):
      time.sleep(0.1)
      break

 # Construct packet
if payloads[select] is '':
   pkt = IP(dst = ip) / UDP(sport = srcpt, dport = dstpt)
else:
   pkt = IP(dst = ip) / UDP(sport = srcpt, dport = dstpt) / Raw(payloads[select])

pktct = 0
lcd.clear()
lcd.message(str(ip) + '\nS:' + str(srcpt) + 'D:' + str(dstpt))

# Sending packets 
while True:
   if lcd.is_pressed(LCD.UP): # Toggle continuous send
      lcd.set_color(1,1,1)
      while True:
         send(pkt)
         pktct += 1
         time.sleep(0.1)
         if lcd.is_pressed(LCD.UP):
            lcd.set_color(0,0,0)
            lcd.clear()
            lcd.message(str(ip) + '\nS:' + str(srcpt) + 'D:' + str(dstpt) + 'Tx' + str(pktct)) 
            break
   if lcd.is_pressed(LCD.DOWN):
      lcd.clear()
      if len(payloads[select]) < 16:
         lcd.message(payloads[select])
      else:
         whole  = payloads[select]
         first = whole[:15]
         second = whole[15:]
         lcd.message(first + '\n' + second)
         
   if lcd.is_pressed(LCD.LEFT):
      lcd.clear()
      lcd.message(str(ip) + '\nS: ' + str(srcpt) + ' D: ' + str(dstpt))
 
   if lcd.is_pressed(LCD.SELECT): # Exit program
      lcd.clear()
      lcd.message(str(pktct) + " packets sent.")
      break
   
