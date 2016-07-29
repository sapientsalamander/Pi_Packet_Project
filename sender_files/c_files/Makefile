CC = gcc
STD = -std=gnu99
Libraries = -lpthread -lpcap
WFlags = -Wall -Wextra -Wpedantic -Werror

all:
	$(CC) pcap_send.c -o pcap_send $(STD) $(Libraries) $(WFlags)

clean:
	rm *.o pcap_send
