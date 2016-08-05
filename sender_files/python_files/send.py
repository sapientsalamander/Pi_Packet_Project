#!/usr/bin/env python

import fcntl
import os
import sys
import signal

import socket
import time
import thread
import threading
import struct

import scapy.all as scapy
import lcd_packet_generation as pgen
from shared_files import computations
from shared_files import conversions
from shared_files import lcd_input as LCD
from shared_files import multithreaded_lcd as threaded_lcd
from shared_files import SEASIDE
from shared_files.SEASIDE import SEASIDE_FLAGS


def sigint_handler(signum, frame):
    global c_socket
    c_socket.shutdown(socket.SHUT_RDWR)
    c_socket.close()

    raise KeyboardInterrupt


def display_loop():
    """Display the current information on the LCD screen."""

    while True:
        for i in xrange(2):
            threaded_lcd.lock_and_print_lcd_line(lcd, lcd_lock,
                                                 screen_output[i], i)
        time.sleep(0.7)


def update_statistics_loop(c_socket, c_socket_lock):
    """Update the values of bandwidth and CPU use.

    Calculates bandwidth using change in bytes received over time.
    Calculates CPU using psutil.
    """
    while True:
        d_bytes = SEASIDE.request_SEASIDE(c_socket, c_socket_lock,
                                          SEASIDE_FLAGS.GET_BANDWIDTH.value)

        d_bytes = struct.unpack('=Q', d_bytes)
        d_bytes = d_bytes[0]

        bw, bw_unit = conversions.convert_bandwidth_units(d_bytes)

        cpu, percore = computations.read_cpu_usage()  # percore unused

        screen_output[0] = 'Bw:%2.1f %s' % (bw, bw_unit)
        screen_output[1] = 'CPU:%2.1f%%' % (cpu)
        time.sleep(1)


def user_interaction(lcd, lcd_lock, c_socket, c_socket_lock):
    led_state = (0, 1, 0)
    is_sending = False

    global packet

    delay_seconds, delay_useconds = 1, 0
    
    delay_bytes = conversions.convert_delay_bytes(delay_seconds,
                                                  delay_useconds)
    while True:
        if lcd.is_pressed(LCD.SELECT):  # Configure packet
            packet_temp = pgen.configure_packet(lcd, lcd_lock)
            if packet_temp is None:
                time.sleep(0.3)
                continue
            packet = conversions.convert_packet_int_array(packet_temp)

            SEASIDE.send_SEASIDE(c_socket, c_socket_lock,
                                 SEASIDE_FLAGS.DELAY.value, delay_bytes)
            time.sleep(1)  # TODO: Fix needing this sleep function
            SEASIDE.send_SEASIDE(c_socket, c_socket_lock,
                                 SEASIDE_FLAGS.PACKET.value, packet)
            led_state = (0, 1, 0)
        elif lcd.is_pressed(LCD.UP):  # Begin sending
            SEASIDE.send_SEASIDE(c_socket, c_socket_lock,
                                 SEASIDE_FLAGS.START.value)
            is_sending = True
        elif lcd.is_pressed(LCD.RIGHT):  # Configure delay
            delay_seconds, delay_useconds = pgen.configure_delay(lcd, lcd_lock)
            delay_bytes = conversions.convert_delay_bytes(delay_seconds,
                                                          delay_useconds)
            SEASIDE.send_SEASIDE(c_socket, c_socket_lock,
                                 SEASIDE_FLAGS.DELAY.value, delay_bytes)
            threaded_lcd.flash_led(lcd, lcd_lock, 0, 0, 1)
        elif lcd.is_pressed(LCD.LEFT):  # Send single packet
            SEASIDE.send_SEASIDE(c_socket, c_socket_lock,
                                 SEASIDE_FLAGS.SINGLE_PACKET.value)
            threaded_lcd.flash_led(lcd, lcd_lock, *led_state)
        elif lcd.is_pressed(LCD.DOWN):  # Stop sending
            SEASIDE.send_SEASIDE(c_socket, c_socket_lock,
                                 SEASIDE_FLAGS.STOP.value)
            is_sending = False

        if is_sending:
            threaded_lcd.lock_and_set_led_color(lcd, lcd_lock, *led_state)
        else:
            threaded_lcd.lock_and_set_led_color(lcd, lcd_lock, 0, 0, 0)
        time.sleep(0.3)


def main():
    global lcd
    lcd = LCD.LCD_Input_Wrapper()
    lcd.set_color(0, 0, 0)
    lcd.clear()

    # An LCD lock to ensure that the configuration and statistics threads don't
    # attempt to write to the LCD at the same time.
    global lcd_lock
    lcd_lock = threading.RLock()

    # A lock to ensure that only one thread may use the c_socket to communicate
    # using SEASIDE at once.
    global c_socket_lock
    c_socket_lock = threading.RLock()

    global screen_output
    screen_output = ['', '']

    global packet

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

    global c_socket # Global so that the signal handler can close it.
    c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    SOCKET_ADDR = '/tmp/send_socket'
    while True:
        try:
            c_socket.connect(SOCKET_ADDR)
            break
        except:
            time.sleep(1)
            print 'Trying to connect...'
    def_handler = signal.signal(signal.SIGINT, sigint_handler)

    print 'Connected to socket'

    try:
        thread.start_new_thread(display_loop, ())
        thread.start_new_thread(update_statistics_loop, (c_socket, c_socket_lock))
    except:
        print 'Error: ', sys.exc_info()

    user_interaction(lcd, lcd_lock, c_socket, c_socket_lock)


if __name__ == '__main__':
    main()
