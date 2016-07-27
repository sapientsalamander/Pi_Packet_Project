# Before enums were introduced in Python, this was one such method of 'faking'
# an enum. It takes a list of identifiers, zips it from 0..n-1, where n is the
# number of identifiers passed in, and uses the type function to generate a new
# class with the aforementioned identifiers as class variables.
def enums(*sequential):
   enums = dict(zip(sequential, range(len(sequential))))
   return type('Enum', (), enums)

def print_line(message, line, lcd, lcd_lock):
   """Print message to screen on line, multithreading safe.

   Locks the LCD so that only one thread can write to it at a time.
   Also ensures that writing to a line won't clear the entire screen.
   """
   # Pad with spaces, manually clearing the line on LCD.
   message = message.ljust(20)

   lcd_lock.acquire()

   lcd.set_cursor(0,line)
   lcd.message(message)

   lcd_lock.release()

def get_rx_tx_bytes(rx_or_tx):
   """Return the total number of rx_bytes or tx_bytes since startup.

   On Linux machines, there is a directory (/sys/class/net/...) that
   contains networking information about different interfaces, and we just
   pull the number of bytes received / sent over eth0 since startup.

   Returns:
      The number of bytes received / sent over eth0 since startup.
   """
   with open('/sys/class/net/eth0/statistics/' + 
             rx_or_tx + '_bytes', 'r') as file:
      data = file.read()
   return int(data)

def calculate_bandwidth(bandwidth):
   # Abbreviations for bandwidth measuring.
   BDWTH_ABBRS = ('bps', 'Kbps', 'Mbps')

   # If bandwidth > 1000, increases size of units (b -> Kb -> Mb).
   bw_unit = 0
   while bandwidth >= 1000:
      bandwidth /= 1000.0
      bw_unit += 1
      if bw_unit > 2:
         bw_unit = 2
   return (bandwidth, BDWTH_ABBRS[bw_unit])

def display_LED(bandwidth, bw_unit):
   if bw_unit == 0 and bandwidth == 0:
      lcd.set_color(0, 0, 0)
   elif bw_unit == 0:
      lcd.set_color(0, 0, 1)
   elif bw_unit == 1:
      lcd.set_color(0, 1, 0)
   elif bw_unit == 2:
      lcd.set_color(1, 0, 0)
