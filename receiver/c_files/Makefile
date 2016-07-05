CC=gcc
CFLAGS=-std=gnu99 -lpython2.7 -lpcap

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

receiver: receiver.o print_lcd.o
	gcc -o receiver receiver.o print_lcd.o $(CFLAGS)
