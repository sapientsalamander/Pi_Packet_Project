"""LCD Interface for Sending Pi.

This module is used for displaying information on the LCD, as well as taking
in user input, such as configurations for any packet to send out. This IO is
not intrinsically coupled with the rest of the program, so if need be, you
can write your own IO interface, and couple it with the backend.
TODO: Explain how you would write this new interface

Due to the way Python handles modules, and our project layout, in order to
run this file, you need to be in the project root directory (in the same
directory as the README, LICENSE, etc., and run it as a module, ie.

python -m receiver_files.python_files.receive

You probably also have to run it as root.
"""

import fcntl
import sys
import os
import socket
import time
import thread
from enum import Enum

import scapy.all as scapy
import psutil
import Adafruit_CharLCD as LCD

from shared_files import multithreaded_lcd as thread_lcd
from shared_files import computations
from shared_files import conversions

# The file used to initialize the socket to communicate with C program.
SOCKET_ADDR = '/tmp/receive_socket'

# The interface that we are receiving packets from
INTERFACE = 'eth0'

# Creating the class, called Screens, which represents the different screens
# on the LCD that can be accessed via the four directional buttons.
Screens = Enum('Screens', 'Summary Payload Source CPU', start=0)

# Used to determine which screen should currently be shown.
cur_screen = Screens.Summary.value

# Hold information for all screens, so screens in the background can
# still be updating and storing new information. Contains a list of tuples,
# each having two strings, representing line 0 and line 1 of the LCD for each
# type of screen there is.
# TODO: Currently relies on the nature of atomic operations and the Global
# Interpreter Lock. Might want to change it so it is an structure with
# actual multithreaded support.
screen_output = [['', ''] for x in xrange(len(Screens))]

# An LCD lock, to ensure that the two threads, one for port listening and
# one for bandwidth measuring, do not interfere when updating the LCD.
lcd_lock = thread.allocate_lock()


# TODO Request bandwidth from SEASIDE

# TODO: Currently, this global variable is only used for calculating
# bandwidth. We should implement bandwidth calculation some other way
# (perhaps using the SEASIDE struct), and remove this global variable.
packet = scapy.Ether()


def display_loop():
    """Pull in screen_output, and updates the LCD screen display."""
    while True:
        for i in xrange(2):
            thread_lcd.lock_and_print_lcd_line(
                lcd, lcd_lock, screen_output[cur_screen][i], i)
        time.sleep(0.7)


def update_packet_info(packet, number_packets_received):
    """Update and print packet information to LCD, including payload,
    and total number of packets received.

    Args:
        packet: A capture scapy packet.
        number_packets_received: Packets received since program started.
    """
    screen_output[Screens.Summary.value][0] = ('Rx:%3d ' %
                                               number_packets_received)

    # Grabs the payload from the scapy packet. If none is available,
    # or if packet is not a scapy packet, then it cannot parse the payload.
    # TODO: Refactor it, so it doesn't rely on the LCD having only two lines.
    try:
        string_payload = packet.getlayer(scapy.Raw).load
        index = string_payload.find('\n')
        if index == -1:
            screen_output[Screens.Payload.value][0] = string_payload
        else:
            screen_output[Screens.Payload.value][0] = string_payload[:index]
            screen_output[Screens.Payload.value][1] = string_payload[index+1:]
    except AttributeError:
        screen_output[Screens.Payload.value][0] = 'No payload'

    # MAC address
    eth_out = packet.getlayer(scapy.Ether).src
    # TODO: Make MAC address look nicer.
    screen_output[Screens.Source.value][0] = eth_out.replace(':', '')

    # IP address, may not always be available, so we wrap it in a try
    # except block.
    # TODO: Make it so that the packet can show fields other than IP.
    try:
        screen_output[Screens.Source.value][1] = packet.getlayer(scapy.IP).src
    except (AttributeError):
        screen_output[Screens.Source.value][1] = ''


def update_statistics_loop():
    """Gets cpu usage and bandwidth and displays it on the LCD.

    Currently, the bandwidth calculation is done by reading from
    /sys/class/net/[interface]. However, we are not able to get super
    accurate results from it. We currently have plans to move it so that
    the C side will tell us how many packets it has received.
    TODO: Update the info above as soon as we move to SEASIDE.
    """
    rx_cur = computations.read_interface_bytes(INTERFACE, 'rx')
    time_cur = time.time()
    while True:
        rx_prev = rx_cur
        time_prev = time_cur

        #  Switch bandwidth calculation to SEASIDE
        rx_cur = computations.read_interface_bytes(INTERFACE, 'rx')
        time_cur = time.time()

        bw_bits_second = conversions.convert_bandwidth_bits_per_second(
            rx_cur - rx_prev, time_cur - time_prev, len(packet), -14)

        bandwidth, bw_unit = conversions.convert_bandwidth_units(
            bw_bits_second)

        thread_lcd.lock_and_display_bandwidth_LED(
            lcd, lcd_lock, bandwidth, bw_unit)

        bandwidth_output = 'Bw:%5.1f %s' % (bandwidth, bw_unit)

        screen_output[Screens.Summary.value][1] = bandwidth_output

        avg_cpu_usage, per_core_cpu_usage = computations.read_cpu_usage()
        screen_output[Screens.CPU.value][0] = \
            'CPU Usage: %4.1f%%' % (avg_cpu_usage)

        screen_output[Screens.CPU.value][1] = \
            '%2.0f%% %2.0f%% %2.0f%% %2.0f%%' % tuple(per_core_cpu_usage)

        time.sleep(1)


def listen_packets_loop():
    """Initializes the socket used to interface with the C program, and listen
    for any incoming packets. When we hear one, parse it with scapy and update
    the display to show information about packet.
    """
    global packet
    # If file descriptor already exists from previous session, we delete it.
    try:
        os.unlink(SOCKET_ADDR)
    except OSError:
        if os.path.exists(SOCKET_ADDR):
            raise

    # Create the actual socket at the defined address.
    c_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    c_socket.bind(SOCKET_ADDR)
    print 'Successfully created socket'

    print 'Waiting for C program to connect'
    # Listen for the C program to connect
    c_socket.listen(1)
    connection, client_address = c_socket.accept()
    print 'C program connected'

    number_packets_received = 0

    print 'Listening for packets...'

    while True:
        # Receive any packet that the C side has sent over.
        c_input = connection.recv(2048)
        if c_input == -1:
            print 'Error with SEASIDE socket.'
            break

        elif c_input == '':
            print 'Error: Cannot parse empty input.'
            break

        number_packets_received += 1

        print 'Received packet [%d]' % (number_packets_received)

        # Parse packet with scapy so we can pull it apart easier.
        packet = scapy.Ether(c_input)

        update_packet_info(packet, number_packets_received)


def input_loop():
    """Listens for button presses and updates the displayed screen.

    Each button is associated with a different screen, and so when you
    push a button, the screen that should be currently shown is changed.
    """
    global cur_screen
    while True:
        if lcd.is_pressed(LCD.UP):
            cur_screen = Screens.Summary.value
        elif lcd.is_pressed(LCD.DOWN):
            cur_screen = Screens.Payload.value
        elif lcd.is_pressed(LCD.LEFT):
            cur_screen = Screens.Source.value
        elif lcd.is_pressed(LCD.RIGHT):
            cur_screen = Screens.CPU.value


if __name__ == '__main__':
    # Lock to only allow one instance of this program to run.
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

    # Initializes LCD and turn off LED.
    lcd = LCD.Adafruit_CharLCDPlate()
    lcd.set_color(0, 0, 0)
    lcd.clear()

    screen_output[Screens.Summary.value][0] = 'Awaiting packets'

    try:
        thread.start_new_thread(display_loop, ())
        thread.start_new_thread(update_statistics_loop, ())
        thread.start_new_thread(input_loop, ())
    except:
        print 'Error: ', sys.exc_info()[0]

    # Run one of the functions on the main thread, just to avoid having to
    # create another thread, and because the main thread would need to wait
    # for the other threads or the program would stop running as soon as it
    # reaches the end.
    listen_packets_loop()
