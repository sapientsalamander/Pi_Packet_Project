CC=gcc
CFLAGS=-std=gnu99 -lpython2.7 -lpcap -pthread -g -O0

receiver: receiver.o
	$(CC) -o receiver receiver.o $(CFLAGS)
