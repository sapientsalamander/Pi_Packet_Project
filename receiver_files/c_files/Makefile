CC = gcc
STD = -std=gnu99
Libraries = -lpthread -lpcap
WFlags = -Wall -Wextra -Wformat=2 -Wswitch-default -Wcast-align \
    -Wpointer-arith -Wbad-function-cast -Wstrict-prototypes -Winline \
    -Wundef -Wnested-externs -Wcast-qual -Wshadow -Wwrite-strings \
    -Wconversion -Wunreachable-code -Wstrict-aliasing=2 -ffloat-store \
    -fno-common -fstrict-aliasing -lm -pedantic -O0 -ggdb3 -pg --coverage

all:
	$(CC) receive.c -o receive $(STD) $(Libraries) $(WFlags)

clean:
	rm *.o receive
