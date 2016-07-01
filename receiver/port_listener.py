import socket

listener = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)

while True:
   print listener.recvfrom(7777), '\n', type(listener)
