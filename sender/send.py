#!/usr/bin/env python

import fcntl
import sys

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

import os
import socket
import time
import thread

import psutil
import misc_functions
import scapy.all as scapy
import lcd_input as LCD

lcd = LCD.LCD_Input_Wrapper()
lcd.set_color(0,0,0)

# An LCD lock to ensure that the configuration and statistics threads do not
# attempt to write to the LCD at the same time.
lcd_lock = thread.allocate_lock()

screen_output = ['','']

def configure_packet():
   lcd_lock.acquire()
   ip = lcd.get_input_format('IP address\n%i%i%i.%i%i%i.%i%i%i.%i%i%i', '010.000.024.243')[11:]
   ip = '.'.join([str(int(octal)) for octal in ip.split('.')])

   src_port = lcd.get_input_format('Source Port\n%i%i%i%i', '0666' )
   src_port = int(src_port[12:])
   
   dst_port = lcd.get_input_format('Destination Port\n%i%i%i%i', '0666')
   dst_port = int(dst_port[17:])
   
   dstMAC = lcd.get_input_format('MAC Address\n%h%h%h%h%h%h-%h%h%h%h%h%h', 'b827eb-611bd4')
   dstMAC = dstMAC[12:]
   dstMAC = misc_functions.split_MAC(dstMAC)
   
   msg_options = ["Here's a message\nFinis", 'Hello, world!   \n     ',
               '-Insert message\n here-'] 
   
   msg = lcd.get_input_list(msg_options)

   lcd_lock.release()

   packet = scapy.Ether(dst = dstMAC) /\
            scapy.IP(dst = ip) /\
            scapy.UDP(sport = src_port, dport = dst_port) /\
            scapy.Raw(msg)
   return packet
  
def display_loop():
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

def update_statistics_loop(tx_prev, time_prev):
   number_packet_sent = 0
   while True:
      tx_cur = misc_functions.get_tx()
      time_cur = time.time()
   
      bw = (tx_cur - tx_prev) / (time_cur - time_prev) * 8   
      units = []

      i = 0
      while bw >= 1000:
         bw = bw / 1000
         i += 1
   
      cpu = psutil.cpu_percent()

      screen_output[0] = 'Bw:%2.1f' % (bw)
      screen_output[1] = 'CPU:%2.1f' % (cpu)
      time.sleep(1)

if __name__ == '__main__':
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

   tx_prev = misc_functions.get_tx()
   time_prev = time.time()

   try:
      thread.start_new_thread(display_loop, ())
      thread.start_new_thread(update_statistics_loop, (tx_prev, time_prev))
   except:
      print 'Error: ', sys.exc_info()[0]
   while True:
      if lcd.is_pressed(LCD.SELECT):
         packet = configure_packet()
         misc_functions.send_packet(packet, c_socket)
      time.sleep(0.5)
   #packet = configure_packet()
   #misc_functions.send_packet(packet, c_socket)
   #while True:
   #   i = lcd.get_input_list(options)
   #
   #   if i == 0:
   #      packet = configure_packet()
   #      misc_functions.send_packet(packet, c_socket)
   #   elif i == 1:
   #      tx_prev, time_prev = calculate_statistics(tx_prev, time_prev)
   #   elif i == 2:
   #      break
