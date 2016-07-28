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
