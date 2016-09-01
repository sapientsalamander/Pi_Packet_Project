"""Configures a scapy packet with user input from the lcd screen.

Uses the LCD_Input_Wrapper class to interact with the user. All functions
that use the screen directly require a lock object so that only one function
can write to the screen at a time; otherwise garbage may result.

configure_delay: gets the delay between packets from the user.
configure_layer: gets the field values for a layer from the user.
configure_packet: handles the creation of a scapy packet using the LCD screen.
generate_packet: constructs the packet layer by layer.
select_layer: gets the next layer from the user or signals to finish or cancel.
size_and_gen_packet: builds packet, modifying size if necessary.
"""


import sys
import time
import scapy.all as scapy
from shared_files import conversions
from shared_files import computations
import dictionaries as dicts
import data_sanitization as ds


def configure_delay(lcd, lcd_lock):
    """Configures the delay in seconds between packets to be sent.

    Args:
        lcd (LCD_Input_Wrapper object): the lcd screen to interact with
        lcd_lock(RLock object): the lock associated with the screen

    Returns:
        tuple (int, int): the chosen delay in seconds and microseconds.
    """
    with lcd_lock:
        delay = lcd.get_input('Delay:\n%i%i%i.%i%i%i%i',
                              '%08.4f' % float(dicts.DEFAULTS['Other']
                                                             ['delay']))
    delay = float(delay[7:])

    delay_seconds = int(delay)
    delay_useconds = (delay * 1000000 - delay_seconds * 1000000)
    return (delay_seconds, delay_useconds)


def configure_layer(lcd, lcd_lock, layer):
    """Configures a layer's fields as defined in the layer dictionary.

    Args:
        lcd (LCD_Input_Wrapper object): the lcd screen to interact with
        lcd_lock(RLock object): the lock associated with the screen
        layer(scapy class): scapy class of the layer to configure

    Returns:
        scapy layer object: scapy packet layer with the fields filled in.
    """
    p_layer = layer()
    for key in dicts.LCD_INPUT_FORMAT[layer].keys():
        try:
            default = ds.sanitize(dicts.DEFAULTS[layer.name][key],
                                  dicts.SAN_LCD[layer][key])
        except KeyError:
            continue
        val = lcd.get_input(key + ':\n' + dicts.LCD_INPUT_FORMAT[layer][key],
                            default)
        field, value = val.replace('\n', '').split(':')
        value = ds.sanitize(value, dicts.SAN_SCAPY[layer][key])
        setattr(p_layer, field, value)
    return p_layer


def configure_packet(lcd, lcd_lock):
    """Configures a packet layer by layer.

    Args:
        lcd (LCD_Input_Wrapper object): the lcd screen to interact with
        lcd_lock(RLock object): the lock associated with the screen

    Returns:
        A generated packet, or None if generation was cancelled.
    """
    packet = []
    with lcd_lock:
        while True:
            layer = select_layer(lcd, lcd_lock)
            if layer == 'Finish':
                return size_and_gen_packet(lcd, lcd_lock, packet)
            elif layer == 'Cancel':
                return None
            elif layer == 'Load Packet':
                return computations.read_pcap_file(dicts.DEFAULTS['Other']
                                                                 ['pkt_file'])
            elif layer == scapy.Raw:
                packet.append(configure_Raw_layer(lcd, lcd_lock))
            else:
                packet.append(configure_layer(lcd, lcd_lock, layer))


# TODO Modify the way input is handled so this doesn't need to be separate
# TODO Related to the TCP Flags todo
def configure_Raw_layer(lcd, lcd_lock):
    """Configures a scapy Raw layer.

    Args:
        lcd (LCD_Input_Wrapper object): the lcd screen to interact with
        lcd_lock(RLock object): the lock associated with the screen

    Returns:
        str: the chosen message.
    """
    msg_options = ["Here's a message\nFinis",
                   'Hello, world!',
                   '-Insert message\n here-',
                   'This message is\nthe longest one.']
    with lcd_lock:
        msg = msg_options[lcd.get_input(msg_options)]
    return scapy.Raw(msg)


def generate_packet(packet_layers):
    """Constructs a packet consisting of the provided layers.

    The / operator is used to stack packet layers in Scapy. Together, the
    stacked layers form the whole packet. The first layer is used to create the
    packet object and subsequent layers are added onto the bottom.

    Args:
        packet_layers (list): a list of the configured layer objects.

    Returns:
        a fully built scapy packet.
    """
    packet = packet_layers[0]
    packet_layers = packet_layers[1:]

    for layer in packet_layers:
        packet = packet / layer
    return packet


def select_layer(lcd, lcd_lock):
    """Selects the next layer to be configured.

    Args:
        lcd (LCD_Input_Wrapper object): the lcd screen to interact with
        lcd_lock(RLock object): the lock associated with the screen

    Returns:
        scapy layer class of the selected layer.
    """
    layer_class = dicts.LCD_INPUT_FORMAT.keys() + [scapy.Raw, 'Finish',
                                                   'Cancel', 'Load Packet']
    with lcd_lock:
        layer = lcd.get_input([key.name for key in
                               dicts.LCD_INPUT_FORMAT.keys()]
                              + ['Raw', 'Finish', 'Cancel', 'Load Packet'])
    return layer_class[layer]


def size_and_gen_packet(lcd, lcd_lock, packet):
    """Sizes an arbitrary packet, padding with null bytes or truncating.

    Args:
        lcd (LCD_Input_Wrapper object): the lcd screen to interact with
        lcd_lock(RLock object): the lock associated with the screen
        packet (list of scapy layer objects): the configured layers.

    Returns:
        a fully configured and built scapy packet sized to the user's request.
    """
    with lcd_lock:
        ptemp = generate_packet(packet)
        size = int(lcd.get_input('Size(bytes):\n%i%i%i%i',
                                 '%04d' % len(ptemp))[13:])
        if size < len(ptemp):
            lcd.clear()
            lcd.message('Warning:\nTruncating Pkt')
            time.sleep(2)
    padsize = size - len(ptemp)
    if padsize > 0:
        packet.append(scapy.Raw('\x00'*padsize))
    return scapy.Ether(str(generate_packet(packet))[:size])
