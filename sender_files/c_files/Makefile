CC = gcc
STD = -std=gnu99
Libraries = -lpthread -lpcap
WFlags = -Wall -Wextra -Wpedantic -Werror

all:
	$(CC) send.c -o send $(STD) $(Libraries) $(WFlags)

clean:
	rm *.o send
