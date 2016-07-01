from scapy.all import *

send(IP(dst='10.0.24.243')/UDP(dport=7777)/("Hello World!"), iface="eth0")
