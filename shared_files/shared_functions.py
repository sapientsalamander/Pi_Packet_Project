def enums(*sequential):
   """ Constructs a 'fake' enum with the provided identifiers.
   
   Before enums were introduced in Python, this was one such method of 'faking'
   an enum. It takes a list of identifiers, zips it from 0..n-1, where n is the
   number of identifiers passed in, and uses the type function to generate a new
   class with the aforementioned identifiers as class variables.
   
   sequential -- a list of enum identifiers
   
   Returns:
      A class containing the identifiers as class variables.
   
   """
   enums = dict(zip(sequential, range(len(sequential))))
   return type('Enum', (), enums)

def int_array(pac):
   """Converts a packet into an array of integers."""

   tmp = str(pac).encode('hex')
   tmp = [x+y for x,y in zip(tmp[0::2], tmp[1::2])]
   return map(lambda x : int(x,16), tmp)

def convert_MAC(address):
   """Converts a MAC address from form ffffff-ffffff to ff:ff:ff:ff:ff:ff"""

   mac = []
   address = address.replace('-', '')
   for i in xrange(0, len(address), 2):
      mac.append(address[i:i+2])
   return ':'.join(mac)

def calculate_packet_delay(pps):
   """Calculates a delay between packets given the desired number of packets
   per second.

   pps - desired number of packets per second

   Returns:
      The number of whole seconds and microseconds between packets
      as a tuple.
   """
   seconds = 0
   useconds = (1.0 / pps) * 1000000
   while useconds >= 1000000:
      useconds  -= 1000000
      seconds += 1
   return (int(seconds), int(useconds))

def get_interface_bytes(interface, io):
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

def calculate_bandwidth_unit(bandwidth):
   """Calculate the most appropriate unit for a given number of bps.

   Chooses the largest applicable unit between bits, kilobits and megabits.
   
   bandwidth -- current bandwidth in bits per second.

   Returns:
       The adjusted number and appropriate unit as a tuple.
   """
   BDWTH_ABBRS = ('bps', 'Kbps', 'Mbps')

   bw_unit = 0
   while bandwidth >= 1000:
      bandwidth /= 1000.0
      bw_unit += 1
      if bw_unit > 2:
         bw_unit = 2
   return (bandwidth, BDWTH_ABBRS[bw_unit])

# ==================== LCD Multithreading-safe functions ====================

def display_bandwidth_LED(lcd, lcd_lock, bandwidth, bw_unit):
   with lcd_lock:
      
      if bw_unit == 0 and bandwidth == 0:
         lcd.set_color(0, 0, 0)
      elif bw_unit == 0:
         lcd.set_color(0, 0, 1)
      elif bw_unit == 1:
         lcd.set_color(0, 1, 0)
      elif bw_unit == 2:
         lcd.set_color(1, 0, 0)
   
def lock_and_set_led_color(lcd, lcd_lock, r, g, b):
   with lcd_lock:
      lcd.set_color(r, g, b)

def print_line(lcd, lcd_lock, message, line):
   """Print message to screen on line, multithreading safe.

   Locks the LCD so that only one thread can write to it at a time.
   Also ensures that writing to a line won't clear the entire screen.
   """
   # Pad with spaces, manually clearing the line on LCD.
   message = message.ljust(20)

   with lcd_lock:
      
      lcd.set_cursor(0,line)
      lcd.message(message)
      

