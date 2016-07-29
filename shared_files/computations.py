import psutil


def compute_interface_bytes(interface, io):
    """Return the total number of rx_bytes or tx_bytes since startup.

    On Linux machines, there is a directory (/sys/class/net/...) that
    contains networking information about different interfaces, and we just
    pull the number of bytes received / sent over eth0 since startup.

    Returns:
        The number of bytes received / sent over eth0 since startup.
    """
    try:
        with open('/sys/class/net/%s/statistics/%s_bytes' % (interface, io),
                  'r') as file:
            return int(file.read())
    except (IOError):
        return None


def compute_cpu_usage():
    """Calculates cpu usage using the psutil library.

    Returns:
        tuple (float, list): The first return value is the average
        cpu usage, while the second argument is the cpu usage
        per core.
        """
    return (psutil.cpu_percent(), psutil.cpu_percent(percpu=True))


def read_packet_from_file():
    with open('/home/pi/Sender/sender_files/python_files/packet', 'r') as file:
        data = file.read()
    return data

def get_MAC():  # TODO Move to computations
    try:
        with open('/sys/class/net/eth0/address') as file:
            return file.read()
    except:
        return 'ff:ff:ff:ff:ff:ff'


def read_defaults():  # TODO make path more relative
    with open('/home/pi/Sender/sender_files/python_files/packet_config.txt',
              'r') as conf:
        fields = [val for val in conf.read().split('\n')
                  if len(val) > 0 and val[0] != '#']
    return (fields[:-1], fields[len(fields)-1])
