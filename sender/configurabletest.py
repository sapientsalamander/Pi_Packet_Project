import time
import Adafruit_CharLCD as LCD
import sys

lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)
lcd.blink(True)

lcd.create_char(1, [0, 4, 14, 31,  4,  4, 4, 0])
lcd.create_char(2, [0, 4,  4,  4, 31, 14, 4, 0])
lcd.create_char(3, [0, 4, 12, 31, 12,  4, 0, 0]) 
lcd.create_char(4, [0, 4,  6, 31,  6,  4, 0, 0])
lcd.create_char(5, [0, 1,  3, 22, 28,  8, 0, 0])

IP = list('000.000.000.000') 
cursor = 0

def print_LCD():
   lcd.clear()
   lcd.message('IP:\n' + "".join(IP))
   lcd.set_cursor(cursor, 1)

def inc_digit():
   num = int(IP[cursor])
   num += 1
   if num > 9:
      num = 0
   elif num < 0:
      num = 9
   IP[cursor] = str(num)

def dec_digit():
   num = int(IP[cursor])
   num -= 1
   if num > 9:
      num = 0
   elif num < 0:
      num = 9
   IP[cursor] = str(num)

def rmv_leading_zeros(IP):
   strIP = "".join(IP)
   strIP = strIP.split(".")
   numIP = []
   rmvdIP = ""
   for octet in strIP:
      numIP.append(int(octet))
   for octet in numIP:
      rmvdIP += str(octet)
      rmvdIP += "."
   rmvdIP = rmvdIP[:-1]
   print rmvdIP
   return rmvdIP

print_LCD()

while True:
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
      if IP[cursor] == ".":
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

rmvd = rmv_leading_zeros(IP)
lcd.clear()
lcd.message('w/o leading 0s: \n' + rmvd)
time.sleep(3.0)
