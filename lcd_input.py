#!/usr/bin/env python

import time
import Adafruit_CharLCD as LCD

# Before enums were introduced in Python, this was one such method of 'faking'
# an enum. It takes a list of identifiers, zips it from 0..n-1, where n is the
# number of identifiers passed in, and uses the type function to generate a new
# class with the aforementioned identifiers as class variables.
def enums(*sequential):
   enums = dict(zip(sequential, range(len(sequential))))
   return type('Enum', (), enums)

Input_Type = enums('Char', 'Int', 'Hex')

Value_Types = { 'i' : (Input_Type.Int, 2), \
                'h' : (Input_Type.Hex, 2) }

Value_Arrays = { Input_Type.Int : '0123456789', \
                 Input_Type.Hex : '0123456789abcdef' }

class Input_Char():
   value = ' '
   value_type = ''

def _inc_or_dec(value, value_type, delta):
   values_array = Value_Arrays[value_type]
   return values_array[(values_array.index(value) + delta) % len(values_array)]

def increment(value):
   return _inc_or_dec(value.value, value.value_type, 1)

def decrement(value):
   return _inc_or_dec(value.value, value.value_type, -1)

def parse_identifier(input_format):
   char_type = Input_Char()
   advances = 0
   try:
      value_type = Value_Types[input_format[1]]
      char_type.value_type = value_type[0]
      char_type.value = '0'
      advances = value_type[1]
   except (IndexError, KeyError):
      print 'Cannot parse format; unknown identifier after "%"'
      char_type.value_type = Input_Type.Char
      char_type.value = input_format[0]
      advances = 2
   return (advances, char_type)

def parse_char(input_format):
   char_type = Input_Char()
   advances = 0
   if input_format[0] == '%':
      advances, char_type = parse_identifier(input_format)
   else:
      char_type.value_type = Input_Type.Char
      char_type.value = input_format[0]
      advances = 1
   return (advances, char_type)

def _find_input(list_chars, index, delta):
   for i in list_chars[(index+delta) % len(list_chars)::delta]:
      if i.value_type != Input_Type.Char:
         return list_chars.index(i)
   return index

def find_previous_input(list_chars, index):
   return _find_input(list_chars, index, -1)

def find_next_input(list_chars, index):
   return _find_input(list_chars, index, 1)

def get_input(lcd, lcd_format):
   list_chars = []
   i = 0
   while i < len(lcd_format):
      advance, char = parse_char(lcd_format[i:i+2])
      i += advance
      list_chars.append(char)

   index = find_next_input(list_chars, -1)
   if index == -1:
      print 'Enter a format, dummy'
      return ''

   index_newline = -1
   for i in xrange(len(list_chars)):
      if list_chars[i].value == '\n':
         index_newline = i
         break

   lcd.clear()
   lcd.message(''.join([x.value for x in list_chars]))

   lcd.blink(True)
   lcd.set_cursor(0,0)

   while True:
      time.sleep(0.1)
      if lcd.is_pressed(LCD.UP):
         list_chars[index].value = increment(list_chars[index])
      elif lcd.is_pressed(LCD.DOWN):
         list_chars[index].value = decrement(list_chars[index])
      elif lcd.is_pressed(LCD.LEFT):
         index = find_previous_input(list_chars, index)
      elif lcd.is_pressed(LCD.RIGHT):
         index = find_next_input(list_chars, index)
      elif lcd.is_pressed(LCD.SELECT):
         break
      else:
         continue
      lcd.clear()
      lcd.message(''.join([x.value for x in list_chars]))
      cursor_index = index
      if index >= index_newline:
         cursor_index -= index_newline + 1
      lcd.set_cursor(cursor_index, index >= index_newline)
