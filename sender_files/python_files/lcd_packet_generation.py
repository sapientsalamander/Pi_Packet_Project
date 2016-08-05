import sys
import time
import scapy.all as scapy
from shared_files import conversions
from shared_files import computations
import dictionaries as dicts
import data_sanitization as ds


def configure_packet(lcd, lcd_lock):
    """Configures a packet layer by layer.

    lcd -- the screen used for user input
    lcd_lock -- the lock associated with the screen

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
                return computations.read_pcap_file(dicts.DEFAULTS['Other']['pkt_file'])
            elif layer == scapy.Raw:
                packet.append(configure_Raw_layer(lcd, lcd_lock))
            else:
                packet.append(configure_layer(lcd, lcd_lock, layer))


def generate_packet(packet_layers):
    """Constructs a packet consisting of the provided layers."""
    packet = packet_layers[0]
    packet_layers = packet_layers[1:]

    for layer in packet_layers:
        packet = packet / layer
    return packet


def select_layer(lcd, lcd_lock):
    """Selects the next layer to be configured."""
    layer_obj = dicts.LAYER.keys() + [scapy.Raw, 'Finish', 'Cancel',
                                      'Load Packet']
    with lcd_lock:
        layer = lcd.get_input([key.name for key in dicts.LAYER.keys()]
                              + ['Raw', 'Finish', 'Cancel', 'Load Packet'])
    return layer_obj[layer]


def configure_layer(lcd, lcd_lock, layer):
    """Configures a layer's fields as defined in the layer dictionary.

    lcd -- the lcd screen to interact with
    lcd_lock -- the lock associated with the screen
    layer -- scapy class of the layer to configure
    """
    p_layer = layer()
    for key in dicts.LAYER[layer].keys():
        try:
            default = ds.sanitize(dicts.DEFAULTS[layer.name][key],
                                  dicts.SAN_LCD[layer][key])
        except KeyError:
            continue
        val = lcd.get_input(key + ':\n' + dicts.LAYER[layer][key], default)
        val = val.replace('\n', '')

        field, value = val.split(':')

        value = ds.sanitize(value, dicts.SAN_SCAPY[layer][key])

        setattr(p_layer, field, value)
    return p_layer


def size_and_gen_packet(lcd, lcd_lock, packet):
    """Sizes an arbitrary packet, padding with null bytes or truncating."""
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


def configure_Raw_layer(lcd, lcd_lock):
    """Configures a scapy Raw layer."""
    msg_options = ["Here's a message\nFinis",
                   'Hello, world!',
                   '-Insert message\n here-',
                   'This message is\nthe longest one.']
    with lcd_lock:
        msg = msg_options[lcd.get_input(msg_options)]
    return scapy.Raw(msg)


def configure_delay(lcd, lcd_lock):
    """Configures the delay in seconds between packets to be sent."""
    with lcd_lock:
        delay = lcd.get_input('Delay:\n%i%i%i.%i%i%i%i',
                              '%08.4f' % float(dicts.DEFAULTS['Other']['delay']))
    delay = float(delay[7:])

    delay_seconds = int(delay)
    delay_useconds = (delay * 1000000 - delay_seconds * 1000000)
    return (delay_seconds, delay_useconds)
