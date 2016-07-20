#!/usr/bin/env python
import fcntl
import socket
import sys
import time

import psutil
import scapy.all

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

SOCKET_ADDR = '/tmp/send_socket'

msg_options = ["Here's a message\nFinis", "Hello, world!   \n    ",
               "-Insert message\n here-"] 

def configure_packet():
   ip = lcd.get_input_format("IP address\n%i%i%i.%i%i%i.%i%i%i.%i%i%i")
   ip = ip[11:]
   
   src_port = lcd.get_input_format("Source Port\n%i%i%i%i")
   src_port = int(src_port[12:])
   
   dst_port = lcd.get_input_format("Destination Port\n%i%i%i%i")
   dst_port = int(dst_port[17:])
   
   dstMAC = lcd.get_input_format("MAC Address\n%h%h%h%h%h%h-%h%h%h%h%h%h")
   dstMAC = dstMAC[12:]
   lcdMAC = dstMAC
   dstMAC = misc_functions.split_MAC(dstMAC)
   
   msg = lcd.get_input_list(msg_options)

   """packet = scapy.all.Ether(dst ="a0:8c:fd:4b:7e:f5") /\
            scapy.all.IP(dst = "10.0.24.239") /\
            scapy.all.UDP(sport = 666, dport = 666) /\
            scapy.all.Raw("-Insert message\n here-")
   return packet
   """
def calc_statistics(tx_prev, time_prev):
   # Bandwidth
   
   
   tx_cur = misc_functions.get_tx()
   time_cur = time.time()
   
   bw = (tx_cur - tx_prev) / (time_cur - time_prev) * 8   
   
   i = 0
   while bw >= 1000:
      bw = bw / 1000
      i += 1
   
   cpu = psutil.cpu_percent()
   
   lcd.clear()
   lcd.message("Bw:%2.1f CPU:%2.1f" % (bw, cpu))
   
   return (tx_cur, time_cur)
"""
def display_packet_info(packet):
   rows = [lcdMAC, ip, (src_port + " " + dst_port), msg]
   r1 = 0
   r2 = 1
   lcd.clear()
   lcd.message(rows[r1] + "\n" + rows[r2])

   while True:
   
   """   

   


c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
while True:
   try:
      c_socket.connect(SOCKET_ADDR)
      break
   except:
      time.sleep(1)

options = ["Reconfigure", "Statistics", "Packet Info"]

tx_prev = misc_functions.get_tx()
time_prev = time.time()

# packet = configure_packet()
packet = scapy.all.Ether(dst ="a0:8c:fd:4b:7e:f5") /\
         scapy.all.IP(dst = "10.0.24.239") /\
         scapy.all.UDP(sport = 80, dport = 80) /\
         scapy.all.Raw("-Insert message\n here-")
   
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










      
