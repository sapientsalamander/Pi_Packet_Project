CC=gcc
CFLAGS=-std=gnu99 -lpython2.7 -lpcap -pthread -g -O0

receive: receive.o
	$(CC) -o receive receive.o $(CFLAGS)
