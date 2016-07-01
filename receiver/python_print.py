#!/usr/bin/python
# Example using a character LCD plate.
import time

import Adafruit_CharLCD as LCD


# Initialize the LCD using the pins
lcd = LCD.Adafruit_CharLCDPlate()
lcd.set_color(0,0,0)

def python_print(a):
   lcd.clear()
   lcd.message('Received: ' + a + ' packets')
