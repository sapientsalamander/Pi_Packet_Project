import shared_functions

SEASIDE_FLAGS = shared_functions.enums('PACKET', 'START', 'STOP', 'SLEEP_TIME')

def send_SEASIDE(c_socket, SEASIDE_flag, data=0):
   """Sends a SEASIDE packet through the socket.

   SEASIDE_flag - indicator for the type of data to be sent.
      0 - Packet. Requires a packet be passed also
      1 - Start signal
      2 - Stop signal
      3 - Set delay. If no delay is passed, it will remove the delay.

   Converts the packet to an int array and the int array of data (including
   flag and size information) to a byte array, and then sends it through the
   provided socket.
   """

   if SEASIDE_flag == 0: # Packet signal
      if data == 0:
         print 'Error: no packet given'
      else:
         c_socket.send(bytearray([SEASIDE_flag, 0, len(data)]
                                     + shared_functions.int_array(data)))
   elif SEASIDE_flag == 1: # Start signal
      c_socket.send(bytearray([SEASIDE_flag, 0, 0]))
   elif SEASIDE_flag == 2: # Stop signal
      c_socket.send(bytearray([SEASIDE_flag, 0, 0]))
   elif SEASIDE_flag == 3: # Set delay
      c_socket.send(bytearray([SEASIDE_flag, 0, 1, data]))
   else:
      print 'Error: invalid SEASIDE flag'
