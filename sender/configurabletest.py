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


def print_port(line, srcpt, dstpt, cursor):
   """Prints source and destination ports to the LCD screen.
   
   line -- the line onscreen of the port being configured
   """   

   lcd.clear()
   lcd.message('Src Port: ' + "".join(srcpt) + '\nDst Port: ' + "".join(dstpt))
   lcd.set_cursor(cursor + 10, line) #+10 to skip over text 

def update_display(disp, lst, cursor):
   """Prints either IP address or Payload to LCD screen during selection.

   disp -- 0 for payload, 1 for IP
   lst -- a list containing the information to be printed
   cursor -- the location of the cursor on the screen
   """
   screens = ['Payload: \n', 'IP: \n']
   lcd.clear()
   lcd.message(screens[disp] + "".join(lst))
   lcd.set_cursor(cursor, 1)

def input_port(srcpt, dstpt, port):
   """Changes a port value to user input.

   srcpt -- the starting value of the source port
   dstpt -- the starting value of the destination port
   port -- the port to be modified (0 for source, 1 for destination)

   returns the modified port as a list of digits
   """
   cursor = 0
   ports = [srcpt, dstpt]
   print_port(port, ports[0], ports[1], cursor)
   while True:
      if lcd.is_pressed(LCD.UP):
         inc_digit(ports[port], cursor)
         print_port(port, ports[0], ports[1], cursor) 
         time.sleep(0.1)
      if lcd.is_pressed(LCD.DOWN):
         dec_digit(ports[port], cursor)
         print_port(port, ports[0], ports[1], cursor)
         time.sleep(0.1)
      if lcd.is_pressed(LCD.LEFT):
         cursor -= 1
         if cursor < 0:
            cursor = 0
         print_port(port, ports[0], ports[1], cursor)
         time.sleep(0.1)
      if lcd.is_pressed(LCD.RIGHT):
         cursor += 1
         if cursor > 3:
            cursor = 3
         print_port(port, ports[0], ports[1], cursor)
         time.sleep(0.1)
      if lcd.is_pressed(LCD.SELECT):
         time.sleep(0.1)
         return ports[port]

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


lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)
lcd.blink(True)

ip = list('000.000.000.000')
payloads = [list('Hello World!'), list('foo'), list('bar'), list('')]
srcpt = list('0000') 
dstpt = list('0000') 
cursor = 0

# Inputting IP address
update_display(1, ip, cursor)
while True: 
   if lcd.is_pressed(LCD.UP):
      inc_digit(ip, cursor)
      update_display(1, ip, cursor)
      time.sleep(0.1) # To prevent duplicate presses
   if lcd.is_pressed(LCD.DOWN):
      dec_digit(ip, cursor)
      update_display(1, ip, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.LEFT):
      cursor -= 1
      if cursor < 0: # Prevent cursor from leaving screen
         cursor = 0
      if ip[cursor] == ".": # Skip over periods
         cursor -= 1
      update_display(1, ip, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.RIGHT):
      cursor += 1
      if cursor > 14:   # IP uses characters 0-14, leaving one blank
         cursor = 14
      if ip[cursor] == ".":
         cursor += 1
      update_display(1, ip, cursor)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.SELECT):
      time.sleep(0.1)
      break
ip = rmv_leading_zerosIP(ip)
# End IP input

# Port input
srcpt = input_port(srcpt, dstpt, 0)
dstpt = input_port(srcpt, dstpt, 1)

dstpt = rmv_leading_zerosPORT(dstpt)
srcpt = rmv_leading_zerosPORT(srcpt)
# End port input

# Choose payload
select = 1
update_display(0, payloads[select], 0)
while True:
   if lcd.is_pressed(LCD.UP):
      select += 1
      if select > 3:
         select = 0
      update_display(0, payloads[select], 0)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.DOWN):
      select -= 1
      if select < 0:
         select = 3
      update_display(0, payloads[select], 0)
      time.sleep(0.1)
   if lcd.is_pressed(LCD.SELECT):
      time.sleep(0.1)
      break
payloads[select] = "".join(payloads[select])

# Construct packet
if payloads[select] is '':
   pkt = IP(dst = ip) / UDP(sport = srcpt, dport = dstpt)
else:
   pkt = IP(dst = ip) / UDP(sport = srcpt, dport = dstpt) / Raw(payloads[select])

pktct = 0
lcd.clear()
lcd.message(str(ip) + '\nS:' + str(srcpt) + 'D:' + str(dstpt) + 'Tx%2d' % (pktct))

# Sending packets 
while True:
   if lcd.is_pressed(LCD.UP): # Toggle continuous send
      lcd.set_color(1,1,1)
      lcd.clear()
      while True:
         send(pkt)
         lcd.set_color(1,0,0) # Flash red when packet is sent
         pktct += 1
         lcd.clear()
         lcd.message(str(ip) + '\nS:' + str(srcpt) 
                        + 'D:' + str(dstpt) + 'Tx%2d' % (pktct)) 
         time.sleep(0.05)
         lcd.set_color(1,1,1)
         time.sleep(0.5)
         if lcd.is_pressed(LCD.UP):
            lcd.set_color(0,0,0)
            lcd.clear()
            lcd.message(str(ip) + '\nS:' + str(srcpt) 
                        + 'D:' + str(dstpt) + 'Tx%2d' % (pktct)) 
            time.sleep(0.5)
            break
   if lcd.is_pressed(LCD.DOWN):
      lcd.clear()
      if len(payloads[select]) < 16:
         lcd.message(payloads[select])
      else:
         whole = "".join(payloads[select])
         first = whole[:15]
         second = whole[15:]
         lcd.message(first + '\n' + second)
         
   if lcd.is_pressed(LCD.LEFT):
      lcd.clear()
      lcd.message(str(ip) + '\nS:' + str(srcpt) + 'D:' + str(dstpt) + 'Tx%2d' % (pktct))

   if lcd.is_pressed(LCD.RIGHT):
      lcd.set_color(1,0,0)
      send(pkt)
      pktct += 1
      lcd.clear()
      lcd.message(str(ip) + '\nS:' + str(srcpt) 
                  + 'D:' + str(dstpt) + 'Tx%2d' % (pktct)) 
      time.sleep(0.1)
      lcd.set_color(0,0,0)
      
   if lcd.is_pressed(LCD.SELECT): # Exit program
      lcd.clear()
      lcd.message(str(pktct) + " packets sent.")
      break
