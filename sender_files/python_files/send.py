#!/usr/bin/env python

import fcntl
import sys

import os
import socket
import time
import thread
import struct

import scapy.all as scapy
import lcd_packet_generation as pgen
from shared_files import computations
from shared_files import conversions
from shared_files import lcd_input as LCD
from shared_files import multithreaded_lcd as threaded_lcd
from shared_files import SEASIDE
from shared_files.SEASIDE import SEASIDE_FLAGS


def display_loop():
    """Display the current information on the LCD screen."""

    while True:
        for i in xrange(2):
            threaded_lcd.lock_and_print_lcd_line(lcd, lcd_lock,
                                                 screen_output[i], i)
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
        bw = conversions.convert_bandwidth_bits_per_second(d_bytes, d_time,
                                                           len(packet), 8)

        bw, bw_unit = conversions.convert_bandwidth_units(bw)

        cpu, percore = computations.compute_cpu_usage()  # percore unused

        screen_output[0] = 'Bw:%2.1f %s' % (bw, bw_unit)
        screen_output[1] = 'CPU:%2.1f%%' % (cpu)
        time.sleep(1)


def user_interaction(lcd, lcd_lock, c_socket, d_packet_vals, d_delay):
    led_state = (0, 1, 0)
    is_sending = False

    global packet
    packet = conversions.convert_packet_int_array(
        # pgen.configure_UDP_packet(lcd, lcd_lock, d_packet_vals))
        pgen.configure_packet(lcd, lcd_lock))
    delay_seconds, delay_useconds = pgen.configure_delay(lcd, lcd_lock,
                                                         d_delay)
    delay_bytes = struct.pack('=BI', delay_seconds, delay_useconds)
    SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.DELAY.value, delay_bytes)
    time.sleep(1)
    SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.PACKET.value, packet)

    while True:
        if lcd.is_pressed(LCD.SELECT):  # Configure packet
            packet = conversions.convert_packet_int_array(
                # pgen.configure_UDP_packet(lcd, lcd_lock, d_packet_vals))
                pgen.configure_packet(lcd, lcd_lock))
            delay_seconds, delay_useconds = pgen.configure_delay(lcd, lcd_lock,
                                                                 d_delay)
            delay_bytes = conversions.delay_to_bytes(delay_seconds,
                                                     delay_useconds)

            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.DELAY.value,
                                 delay_bytes)
            time.sleep(1)  # TODO: Fix needing this sleep function
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.PACKET.value, packet)
            led_state = (0, 1, 0)
        elif lcd.is_pressed(LCD.UP):  # Begin sending
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.START.value)
            is_sending = True
        elif lcd.is_pressed(LCD.RIGHT):  # Reconfigure delay
            delay_seconds, delay_useconds = pgen.configure_delay(lcd, lcd_lock,
                                                                 d_delay)
            delay_bytes = conversions.delay_to_bytes(delay_seconds,
                                                     delay_useconds)
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.DELAY.value,
                                 delay_bytes)
            threaded_lcd.flash_led(lcd, lcd_lock, *led_state)
        elif lcd.is_pressed(LCD.LEFT):  # Changed to read packet from file
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.PACKET.value,
                                 computations.read_packet_from_file())
            led_state = (0, 0, 1)
            threaded_lcd.flash_led(lcd, lcd_lock, *led_state)
        elif lcd.is_pressed(LCD.DOWN):  # Stop sending
            SEASIDE.send_SEASIDE(c_socket, SEASIDE_FLAGS.STOP.value)
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
    lcd_lock = thread.allocate_lock()

    global screen_output
    screen_output = ['', '']

    d_packet_vals, d_delay = computations.read_defaults()

    global packet
    packet = (scapy.Ether(dst=d_packet_vals[0]) /
              scapy.IP(dst=d_packet_vals[1]) /
              scapy.UDP(sport=int(d_packet_vals[2]),
                        dport=int(d_packet_vals[3])))

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

    user_interaction(lcd, lcd_lock, c_socket, d_packet_vals, d_delay)


if __name__ == '__main__':
    main()
