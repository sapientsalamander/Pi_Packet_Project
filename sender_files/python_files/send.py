#!/usr/bin/env python

import fcntl
import sys

import os
import socket
import time
import thread

import psutil
import scapy.all as scapy
from shared_files import lcd_input as LCD
from shared_files import shared_functions

lcd = LCD.LCD_Input_Wrapper()
lcd.set_color(0,0,0)
lcd.clear()

# An LCD lock to ensure that the configuration and statistics threads do not
# attempt to write to the LCD at the same time.
lcd_lock = thread.allocate_lock()

screen_output = ['','']
packet = scapy.Ether()

SEASIDE = shared_functions.enums('PACKET', 'START', 'STOP', 'SLEEP_TIME')

def set_lcd_color(r,g,b):
   lcd_lock.acquire()
   lcd.set_color(r,g,b)
   lcd_lock.release()

def configure_packet():
   """Configure an Ether/IP/UDP/Raw packet with user provided values.

   Configures destination MAC address, destination IP address, source and 
   destination UDP ports, payload, packet size, and delay between packets.

   Returns the packet and delay in seconds as a tuple.
   """

   lcd_lock.acquire()
   ip = lcd.get_input_format('IP address\n%i%i%i.%i%i%i.%i%i%i.%i%i%i',
                            '010.000.024.243')[11:]

   ip = '.'.join([str(int(octal)) for octal in ip.split('.')])

   src_port = lcd.get_input_format('Source Port\n%i%i%i%i', '4321' )
   src_port = int(src_port[12:])
   
   dst_port = lcd.get_input_format('Destination Port\n%i%i%i%i', '4321')
   dst_port = int(dst_port[17:])
   
   dstMAC = lcd.get_input_format('MAC Address\n%h%h%h%h%h%h-%h%h%h%h%h%h',
                                 'b827eb-611bd4')
   dstMAC = dstMAC[12:]
   dstMAC = shared_functions.split_MAC(dstMAC)
   
   msg_options = ["Here's a message\nFinis", 'Hello, world!',
               '-Insert message\n here-', 'This message is\nthe longest one.'] 
   
   msg = lcd.get_input_list(msg_options)
   
   
   packet = scapy.Ether(src = 'b8:27:eb:26:60:d0', dst = dstMAC) /\
            scapy.IP(src = '10.0.24.242', dst = ip) /\
            scapy.UDP(sport = src_port, dport = dst_port)
   
   psize = len(packet) + len(msg)
   psize = '%04d' % psize

   size = lcd.get_input_format('Size of packet:\n%i%i%i%i bytes', psize)
   size = int(size[16:-6])
   
   # pps = lcd.get_input_format('Pps: %i%i%i%i%i', '00001')
   # pps = int(pps[5:])
   seconds = lcd.get_input_format('Delay (seconds):\n%i%i%i%i', '0001')
   seconds = int(seconds[16:])

   lcd_lock.release()

   msg_size = size - len(packet) - len(msg)
   msg += ' ' * msg_size

   packet = packet / scapy.Raw(msg)

   if len(packet) > size:
      print 'Warning: Specified packet size is too small. Cutting off payload.'
      if len(packet) - len(msg) > size:
         print 'Warning: Cutting off header.'
      packet = scapy.Ether(str(packet)[:size - len(packet)])

   if size < 64:
      print 'Warning: packet is below minimum size.'   
 
   # seconds, useconds = shared_functions.get_speed(pps)
   return (packet, seconds)# , useconds)

def display_loop():
   """Display the current information on the LCD screen."""   

   while True:
      for i in xrange(2):
         print_line(screen_output[i], i)
      time.sleep(0.7)

def print_line(message, line):
   """Print message to screen on line, multithreading safe.

   Locks the LCD so that only one thread can write to it at a time.
   Also ensures that writing to a line won't clear the entire screen.
   """
   # Pad with spaces, manually clearing the line on LCD.
   message = message.ljust(20)

   lcd_lock.acquire()

   lcd.set_cursor(0,line)
   lcd.message(message)

   lcd_lock.release()

def update_statistics_loop():
   """Update the values of bandwidth and CPU use.

   Calculates bandwidth using change in bytes received over time. Calculates CPU using psutil. 
   Updates values in 
   """
   time_cur = time.time()
   tx_cur = shared_functions.get_rx_tx_bytes('tx')
   while True:
      tx_prev = tx_cur
      time_prev = time_cur      

      tx_cur = shared_functions.get_rx_tx_bytes('tx')
      time_cur = time.time()

      d_bytes = tx_cur - tx_prev
      num_packets = d_bytes / (len(packet) + 8)
      bw = (num_packets * len(packet)) / (time_cur - time_prev) * 8
      units = ['bps', 'Kbps', 'Mbps']

      i = 0
      while bw >= 1000:
         bw /= 1000
         i += 1
      """Commented out to tie LED to sending status. Saved for future use.
      lcd_lock.acquire()

      if i == 0 and bw == 0:
         lcd.set_color(0, 0, 0)
      if i == 0:
         lcd.set_color(0, 0, 1)
      elif i == 1:
         lcd.set_color(0, 1, 0)
      elif i == 2:
         lcd.set_color(1, 0, 0)
      
      lcd_lock.release()
      """
      cpu = psutil.cpu_percent()

      screen_output[0] = 'Bw:%2.1f %s' % (bw, units[i])
      screen_output[1] = 'CPU:%2.1f%%' % (cpu)
      time.sleep(1)

if __name__ == '__main__':
   # Lock to only allow one instance of this program to run
   # Opens (and creates if non-existent) a file in /tmp/, and attempts to lock
   # it. If it is already locked, then another instance is running, and this
   # instance of the programs exits. If not, it successfully locks it and
   # continues running.
   pid_file = '/tmp/send.pid'
   fp = open(pid_file, 'w')
   try:
      fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
   except IOError:
      print 'An instance of this program is already running'
      sys.exit(0)
   # End of lock code.

   c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
   SOCKET_ADDR = '/tmp/send_socket'
   while True:
      try:
         c_socket.connect(SOCKET_ADDR)
         break
      except:
         time.sleep(1)
         print 'Trying to connect...'

   print 'Connected to socket'
   
   options = ['Reconfigure', 'Statistics', 'Packet Info']

   try:
      thread.start_new_thread(display_loop, ())
      thread.start_new_thread(update_statistics_loop, ())
   except:
      print 'Error: ', sys.exc_info()[0]

   led_state = (0, 1, 0)
   is_sending = False

   while True:
      if lcd.is_pressed(LCD.SELECT): # Configure packet
         packet, seconds = configure_packet() # Removed useconds for now. 
         
         shared_functions.send_SEASIDE(c_socket, SEASIDE.SLEEP_TIME, sleep_time=seconds)
         time.sleep(1) # TODO: Fix needing this sleep function
         shared_functions.send_SEASIDE(c_socket, SEASIDE.PACKET, pkt=packet)

      elif lcd.is_pressed(LCD.UP): # Begin sending
         shared_functions.send_SEASIDE(c_socket, SEASIDE.START)
         is_sending = True
      elif lcd.is_pressed(LCD.RIGHT): # Reset delay to user's number of seconds
         shared_functions.send_SEASIDE(c_socket, SEASIDE.SLEEP_TIME, sleep_time=seconds)
         set_lcd_color(0, 1, 0) # Flash green 
         time.sleep(0.1)
         set_lcd_color(0, 0, 0)
         led_state = (0, 1, 0)
      elif lcd.is_pressed(LCD.LEFT): # Remove delay
         shared_functions.send_SEASIDE(c_socket, SEASIDE.SLEEP_TIME) 
         set_lcd_color(1, 0, 0) # Flash red
         time.sleep(0.1)
         set_lcd_color(0, 0, 0)
         led_state = (1, 0, 0)
      elif lcd.is_pressed(LCD.DOWN): # Stop sending
         shared_functions.send_SEASIDE(c_socket, SEASIDE.STOP)
         is_sending = False
      if is_sending:
         set_lcd_color(*led_state)
      else:
         set_lcd_color(0, 0, 0)
      time.sleep(0.3)
