#!/usr/bin/env python
import fcntl
import socket
import sys
import thread
import time

import psutil
import scapy.all as scapy

import lcd_input as LCD
import misc_functions

# Lock to only allow one instance of this program to run 
pid_file = '/tmp/send.pid'
fp = open(pid_file, 'w')
try:
   fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
   print 'An instance of this program is already running'
   sys.exit(0)
# End of lock code

lcd = LCD.LCD_Input_Wrapper()
lcd.set_color(0,0,0)



def configure_packet():
   ip = lcd.get_input_format('IP address\n%i%i%i.%i%i%i.%i%i%i.%i%i%i', '010.000.024.243')
   ip = ip[11:]
   
   src_port = lcd.get_input_format('Source Port\n%i%i%i%i', '0666' )
   src_port = int(src_port[12:])
   
   dst_port = lcd.get_input_format('Destination Port\n%i%i%i%i', '0666')
   dst_port = int(dst_port[17:])
   
   dstMAC = lcd.get_input_format('MAC Address\n%h%h%h%h%h%h-%h%h%h%h%h%h', 'b827eb611bd4')
   dstMAC = dstMAC[12:]
   dstMAC = misc_functions.split_MAC(dstMAC)
   
   msg_options = ["Here's a message\nFinis", 'Hello, world!   \n    ',
               '-Insert message\n here-'] 
   
   msg = lcd.get_input_list(msg_options)

   packet = scapy.Ether(dst = dstMAC) /\
            scapy.IP(dst = ip) /\
            scapy.UDP(sport = src_port, dport = dst_port) /\
            scapy.Raw(msg)
   return packet
  

def calc_statistics_thread(tx_prev, time_prev):
   # Bandwidth
   
   while True:
      tx_cur = misc_functions.get_tx()
      time_cur = time.time()
   
      bw = (tx_cur - tx_prev) / (time_cur - time_prev) * 8   
   
      i = 0
      while bw >= 1000:
         bw = bw / 1000
         i += 1
   
      cpu = psutil.cpu_percent()
   
      lcd.clear()
      lcd.message('Bw:%2.1f CPU:%2.1f' % (bw, cpu))
      lcd.wait_to_continue() # TODO find a better way to do this after multithreading 


   
# def update_display_thread():
   


if __name__ == '__main__':
   """c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
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
   """
   packet = configure_packet()
   """packet = scapy.Ether(dst = 'b8:27:eb:61:1b:d4') /\
            scapy.IP(dst = '10.0.24.243') /\
            scapy.UDP(sport = 666, dport = 666) /\
            scapy.Raw('This is line 1\nThis is line 2')
   """   
   misc_functions.send_packet(packet, c_socket)
   """
   while True:
      i = lcd.get_input_list(options)
   
      if i == 0:
         packet = configure_packet()
         misc_functions.send_packet(packet, c_socket)
      elif i == 1:
         tx_prev, time_prev = calculate_statistics(tx_prev, time_prev)
      elif i == 2:
         break
   """









      
