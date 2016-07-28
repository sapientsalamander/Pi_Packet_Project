#!/usr/bin/env python

import fcntl
import sys

import os
import socket
import time
import thread

import scapy.all as scapy
from shared_files import computations
from shared_files import conversions
from shared_files import lcd_input as LCD
from shared_files import multithreaded_lcd as threaded_lcd
from shared_files import SEASIDE
from shared_files.SEASIDE import SEASIDE_FLAGS

lcd = LCD.LCD_Input_Wrapper()
lcd.set_color(0,0,0)
lcd.clear()

# An LCD lock to ensure that the configuration and statistics threads do not
# attempt to write to the LCD at the same time.
lcd_lock = thread.allocate_lock()

screen_output = ['','']
packet = scapy.Ether()

def configure_packet(lcd, lcd_lock): # TODO Rewrite with selectable layers
    """Configure an Ether/IP/UDP/Raw packet with user provided values.

    Configures destination MAC address, destination IP address, source and 
    destination UDP ports, payload, packet size. Multithreading safe.

    lcd -- the lcd screen to be used
    lcd_lock -- the lock associated with the lcd screen

    Returns:
        The configured packet.
    """
    msg_options = ["Here's a message\nFinis",
                    'Hello, world!',
                    '-Insert message\n here-',
                    'This message is\nthe longest one.'] 
    with lcd_lock:
        ip = lcd.get_input_format('IP address\n%i%i%i.%i%i%i.%i%i%i.%i%i%i',
                                    '010.000.024.243')[11:]
        src_port = lcd.get_input_format('Source Port\n%i%i%i%i',
                                    '4321')[12:]
        dst_port = lcd.get_input_format('Destination Port\n%i%i%i%i',
                                    '4321')[17:]
        dstMAC = lcd.get_input_format('MAC Address\n%h%h%h%h%h%h-%h%h%h%h%h%h',
                                    'b827eb-611bd4')[12:]
        msg = lcd.get_input_list(msg_options)

        dstMAC = conversions.convert_MAC_addr(dstMAC)
        dst_port = int(dst_port)
        src_port = int(src_port)
        ip = '.'.join([str(int(octal)) for octal in ip.split('.')])
    
        packet = generate_UDP_packet(ip, dst_port, src_port, dstMAC)

        psize = len(packet) + len(msg)
        size = lcd.get_input_format('Size of packet:\n%i%i%i%i bytes', '%04d' % psize)
        size = int(size[16:-6])

    packet = generate_UDP_packet(ip, dst_port, src_port, dstMAC, msg)
    resize_packet(packet, msg, size)
    return conversions.convert_packet_int_array(packet)

def resize_packet(packet, msg, size): # TODO Make warnings print to LCD
    if len(packet) > size:
        print 'Warning: Specified packet size is too small. Cutting off payload.'
        if len(packet) - len(msg) > size:
                print 'Warning: Cutting off header.'
    if size < 64:
        print 'Warning: packet is below minimum size.'

    msg_size = size - len(packet) - len(msg)
    msg += ' ' * msg_size
    return scapy.Ether(str(packet)[:size - len(packet)])

def configure_delay(lcd, lcd_lock):
    with lcd_lock:
        delay_seconds = lcd.get_input_format('Delay (seconds):\n%i%i%i%i',
                                                '0001')
    return [int(delay_seconds[16:])]
    
def generate_UDP_packet(ip, srcpt, dstpt, dstMAC, msg=None): # TODO Generalize
    packet = scapy.Ether(dst = dstMAC) /\
             scapy.IP(dst = ip) /\
             scapy.UDP(sport = srcpt, dport = dstpt)
    if msg is not None:
        packet = packet / scapy.Raw(msg)
    return packet

def display_loop():
    """Display the current information on the LCD screen."""       

    while True:
        for i in xrange(2):
            threaded_lcd.lock_and_print_lcd_line(lcd, lcd_lock, screen_output[i], i)
        time.sleep(0.7)

def update_statistics_loop():
    """Update the values of bandwidth and CPU use.

    Calculates bandwidth using change in bytes received over time. 
    Calculates CPU using psutil. 
    """

    time_cur = time.time()
    tx_cur = computations.compute_interface_bytes('eth0', 'tx')
    while True:
        tx_prev = tx_cur
        time_prev = time_cur            

        tx_cur = computations.compute_interface_bytes('eth0', 'tx')
        time_cur = time.time()

        d_bytes = tx_cur - tx_prev
        d_time = time_cur - time_prev
        num_packets = d_bytes / (len(packet) + 8) # TODO Find real tx number
       
        bw = (num_packets * len(packet)) / (time_cur - time_prev) * 8
        bw, bw_unit = conversions.convert_bandwidth_units(bw)
       
        cpu, percore = computations.compute_cpu_usage() # percore unused

        screen_output[0] = 'Bw:%2.1f %s' % (bw, bw_unit)
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

    try:
        thread.start_new_thread(display_loop, ())
        thread.start_new_thread(update_statistics_loop, ())
    except:
        print 'Error: ', sys.exc_info()[0]

    led_state = (0, 1, 0)
    is_sending = False
    delay_seconds = [1]

    while True:
        if lcd.is_pressed(LCD.SELECT): # Configure packet
            packet = configure_packet(lcd, lcd_lock)
            delay_seconds = configure_delay(lcd, lcd_lock)    

            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.DELAY.value, delay_seconds)
            time.sleep(1) # TODO: Fix needing this sleep function
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.PACKET.value, packet)
        elif lcd.is_pressed(LCD.UP): # Begin sending
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.START.value)
            is_sending = True
        elif lcd.is_pressed(LCD.RIGHT): # Reset delay to user's number of seconds
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.DELAY.value, delay_seconds)
            led_state = (0, 1, 0)
            threaded_lcd.flash_led(lcd, lcd_lock, *led_state)
        elif lcd.is_pressed(LCD.LEFT): # Remove delay
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.DELAY.value, [0]) 
            led_state = (1, 0, 0)
            threaded_lcd.flash_led(lcd, lcd_lock, *led_state)
        elif lcd.is_pressed(LCD.DOWN): # Stop sending
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.STOP.value)
            is_sending = False
        if is_sending:
            threaded_lcd.lock_and_set_led_color(lcd, lcd_lock, *led_state)
        else:
            threaded_lcd.lock_and_set_led_color(lcd, lcd_lock, 0, 0, 0)
        time.sleep(0.3)
