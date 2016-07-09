CC=gcc
CFLAGS=-std=gnu99 -lpython2.7 -lpcap -pthread

receiver: receiver.o c_to_python_interface.o
	gcc -o receiver receiver.o c_to_python_interface.o $(CFLAGS)
