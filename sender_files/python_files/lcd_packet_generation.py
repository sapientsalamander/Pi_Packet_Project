import sys
import StringIO
import scapy.all as scapy
from shared_files import conversions
from shared_files import computations


d_packet_vals, d_delay = computations.read_defaults()
d_dstMAC, d_IP, d_srcport, d_dstport, d_psize = d_packet_vals


def configure_packet(lcd, lcd_lock):
    packet = []
    while True:
        layer = select_layer(lcd, lcd_lock)
        if layer == 'Finish':
            return generate_packet(packet)
        elif layer == 'Cancel':
            return None
        else:
            packet.append(configure_layer_hard(lcd, lcd_lock, layer))


def generate_packet(packet_layers):  # TODO Write this
    packet = packet_layers[0]
    packet_layers = packet_layers[1:]

    for layer in packet_layers:
        packet = packet / layer

    return packet


def select_layer(lcd, lcd_lock):  # To add new layer, include name here.
    layer_options = ['Ether', 'IP', 'Raw', 'TCP', 'UDP', 'Finish',
                     'Cancel']
    with lcd_lock:
        layer = lcd.get_input_list(layer_options)

    # if layer != 'Finish' & layer != 'Cancel':
    #     layer = eval('scapy.' + layer)

    return layer


def configure_layer(lcd, lcd_lock, layer):
    old_stdout = sys.stdout  # TODO turn into function or context manager
    captured_output = StringIO.StringIO()  # TODO determine if lock is needed
    sys.stdout = captured_output        # to prevent stealing other output

    scapy.ls(layer)

    sys.stdout = old_stdout

    layer_fields = captured_output.getvalue().split('\n')
    layer_fields = layer_fields[:-1]  # Separating fields

    i = 0
    while i < len(layer_fields):  # Remove extraneous spaces and punctuation
        layer_fields[i] = [x for x in layer_fields[i].split(' ') if len(x) > 1]
        i += 1                  # TODO remove parentheses from default

    with lcd_lock:
        pass
        # TODO create input calls from scapy types


def configure_layer_hard(lcd, lcd_lock, layer):
    return eval('configure_%s_layer(lcd, lcd_lock)' % layer)


def configure_Ether_layer(lcd, lcd_lock):
    with lcd_lock:  # TODO fix indent
        dest = lcd.get_input_format(
               'Destination MAC:\n%h%h%h%h%h%h-%h%h%h%h%h%h',
               d_dstMAC)[17:]
        dest = conversions.convert_MAC_addr(dest)

        source = lcd.get_input_format('Source MAC:\n%h%h%h%h%h%h-%h%h%h%h%h%h',
                                      computations.get_MAC())[12:]
        source = conversions.convert_MAC_addr(source)
    # TODO Type is not configurable because it is a keyword. Workaround?
    return scapy.Ether(dst=dest, src=source)


def configure_IP_layer(lcd, lcd_lock):
    with lcd_lock:
        source = lcd.get_input_format('Source IP:\n%i%i%i.%i%i%i.%i%i%i.%i%i%i',
                                        '010.000.024.242')[11:]
        source  = '.'.join([str(int(octal)) for octal in source.split('.')])
        # TODO find out how to get source IP

        dest = lcd.get_input_format(  # TODO fix indent
               'Destination IP:\n%i%i%i.%i%i%i.%i%i%i.%i%i%i',
                d_IP)[16:]
        dest  = '.'.join([str(int(octal)) for octal in dest.split('.')])

        ttl = int(lcd.get_input_format('TTL:\n%i%i%i', '064')[5:])
        if ttl > 255:
            ttl = 255
    return scapy.IP(src=source, dst=dest, ttl=ttl)


def configure_UDP_layer(lcd, lcd_lock):
    with lcd_lock:
        src = int(lcd.get_input_format('Source Port\n%i%i%i%i',
                                        d_srcport)[12:])
        dst = int(lcd.get_input_format('Destination Port\n%i%i%i%i',
                                        d_dstport)[17:])
    return scapy.UDP(sport=src, dport=dst)


def configure_TCP_layer(lcd, lcd_lock):
    with lcd_lock:
        src = int(lcd.get_input_format('Source Port\n%i%i%i%i',
                                        d_srcport)[12:])
        dst = int(lcd.get_input_format('Destination Port\n%i%i%i%i',
                                        d_dstport)[17:])
        flag_options = ['FIN', 'SYN', 'ACK', 'RST', 'PSH',
                        'ACK', 'URG', 'ECE', 'CWR', 'Finish']
        flags = ''
        while True:
            flag = lcd.get_input_list(list_options)
            if flag != 'Finish':
                flags.append(flag[0])
            else:
                break 
        return scapy.TCP(sport=src, dport=dst, flags=flags)


def configure_Raw_layer(lcd, lcd_lock):
    msg_options = ["Here's a message\nFinis",
                   'Hello, world!',
                   '-Insert message\n here-',
                   'This message is\nthe longest one.']
    with lcd_lock:
        msg = lcd.get_input_list(msg_options)
    return scapy.Raw(msg)


def input_field_values(fname, field, default):
    if default == '(None)':
        default = ''

    fields = {'DestMACField': ('%h%h%h%h%h%h-%h%h%h%h%h%h', default),
              'SourceMACField': ('%h%h%h%h%h%h-%h%h%h%h%h%h',
                                 computations.get_MAC()),
              'XShortEnumField': ('0x%h%h%h%h', hex(default)[2:])
              }  # TODO Gotta be a better way


def resize_packet(packet, msg, size):  # TODO Make warnings print to LCD
    if len(packet) > size:
        print 'Warning: Specified packet size is too small.\
              Cutting off payload.'
        if len(packet) - len(msg) > size:
                print 'Warning: Cutting off header.'
    if size < 64:
        print 'Warning: packet is below minimum size.'

    msg_size = size - len(packet) - len(msg)
    msg += ' ' * msg_size
    return scapy.Ether(str(packet)[:size])


def configure_UDP_packet(lcd, lcd_lock, defaults):  # TODO Selectable layers
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

    d_MAC, d_ip, d_srcport, d_dstport, d_size = defaults

    with lcd_lock:
        ip = lcd.get_input_format('IP address\n%i%i%i.%i%i%i.%i%i%i.%i%i%i',
                                  d_ip)[11:]
        src_port = lcd.get_input_format('Source Port\n%i%i%i%i',
                                        d_srcport)[12:]
        dst_port = lcd.get_input_format('Destination Port\n%i%i%i%i',
                                        d_dstport)[17:]
        dstMAC = lcd.get_input_format('MAC Address\n%h%h%h%h%h%h-%h%h%h%h%h%h',
                                      d_MAC)[12:]
        msg = lcd.get_input_list(msg_options)

        dstMAC = conversions.convert_MAC_addr(dstMAC)
        dst_port = int(dst_port)
        src_port = int(src_port)
        ip = '.'.join([str(int(octal)) for octal in ip.split('.')])

        packet = generate_UDP_packet(ip, dst_port, src_port, dstMAC)

        psize = len(packet) + len(msg)
        size = lcd.get_input_format('Size of packet:\n%i%i%i%i bytes',
                                    '%04d' % psize)
        size = int(size[16:-6])

    packet = generate_UDP_packet(ip, dst_port, src_port, dstMAC, msg)
    packet = resize_packet(packet, msg, size)
    return packet


def generate_UDP_packet(ip, srcpt, dstpt, dstMAC, msg=None):  # TODO Generalize
    packet = (scapy.Ether(dst=dstMAC) /
              scapy.IP(dst=ip) /
              scapy.UDP(sport=srcpt, dport=dstpt))
    if msg is not None:
        packet = packet / scapy.Raw(msg)
    return packet


def configure_delay(lcd, lcd_lock, default):
    with lcd_lock:
        delay = lcd.get_input_format('Delay:\n%i%i%i.%i%i%i%i',
                                     default)
    delay = float(delay[7:])

    delay_seconds = int(delay)
    delay_useconds = (delay * 1000000 - delay_seconds * 1000000)
    return (delay_seconds, delay_useconds)
