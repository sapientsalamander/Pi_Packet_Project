#include <arpa/inet.h>
#include <pcap.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

/* The device that we will be listening to. */
#define DEVICE "eth0"

/* The file that we will create in order to initialize a socket between this
 * program and the Python program. */
#define PYTHON_SOCKET "/tmp/send_socket"

/* The buffer that will be used to hold the packet that Python sends over,
 * must be big enough to gurantee that it does not overflow (obviously). */
#define PACKET_BUFF_LEN 2048

#define SEASIDE_PACKET      0
#define SEASIDE_START       1
#define SEASIDE_STOP        2
#define SEASIDE_SLEEP_TIME  3

/* Struct to hold the info that we receive from the Python side. The type
 * refers to the type of data that it holds (see above defines), and the size
 * member is the size of the data that it receives. */
/* TODO: Rework the program so this struct doesn't have to be packed. */
typedef struct {
    u_char type;
    u_short size;
    u_char *data;
} __attribute__((packed)) SEASIDE;

/* These next few declarations are for the Python socket that we will be
 * opening, so we can redirect any incoming packets to the Python UI. */
/* The buffer that will be used to hold the packet that Python sends over,
 * must be big enough to gurantee that it does not overflow (obviously). */
static struct sockaddr_un address;
static int socket_fd, python_fd;

/* A thread dedicated solely to sending packets onto the wire. */
static pthread_t send_thread;

/* Static error buffer that holds any errors that pcap returns back to us.
 * Used so that you don't have to declare an error buffer per function. */
static char errbuf[PCAP_ERRBUF_SIZE] = {'\0'};
static pcap_t *pcap;

/* packet and packet length, to send to the receiving Pi. Both need _temp
 * variables because while we are sending, we are also listening in for new
 * packets to send, and we need to store these new packets without corrupting
 * a send, so we store them in temporary variables while the sending function
 * finishes up, and then we sync them. */
static uint8_t packet[PACKET_BUFF_LEN];
static uint8_t packet_temp[PACKET_BUFF_LEN];
intptr_t packet_len;
intptr_t packet_len_temp;

/* Boolean to share between threads. As long as send is true, the sending
 * thread will spam the receiving Pi with as many packets as it can send.
 * If it turns false, it will stop sending packets. */
static volatile unsigned int spam_packets = 0;

/* How long we should wait in between each sent packet. */
static uint8_t sleep_time = 1;

/* Initializes the socket that will be used to receive packet info from
 * the Python program. It binds to the file specified as PYTHON_SOCKET,
 * and then listens in for any attempted connections. When it hears one,
 * we assume that it's the Python program, and we continue on our
 * merry way. */
int
initialize_socket(void)
{
    /*Initialize the type of socket. */
    socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (socket_fd < 0) {
        fprintf(stderr, "socket() failed.\n");
        return -1;
    }

    memset(&address, 0, sizeof(struct sockaddr_un)); /* Zero out address. */

    address.sun_family = AF_UNIX;
    strcpy(address.sun_path, PYTHON_SOCKET);
    unlink(address.sun_path);

    /* Attempt to bind to the file, and then waits for the Python program
     * to connect. */
    socklen_t size_sock = sizeof(struct sockaddr_un);
    struct sockaddr *pointer_sock = (struct sockaddr *) &address;
    if (bind(socket_fd, pointer_sock, size_sock) < 0) {
        fprintf(stderr, "bind() failed.\n");
        sleep(1);
    }

    if (listen(socket_fd, 1) < 0) {
        fprintf(stderr, "listen() failed.\n");
        return -1;
    }

    if ((python_fd = accept(socket_fd, pointer_sock, &size_sock)) < 0) {
        fprintf(stderr, "accept() failed.\n");
        return -1;
    }

    return 0;
}

/* Opens up an ethernet socket from pcap, to be used when sending packets
 * over the wire. */
int
initialize_pcap(void)
{
    pcap = pcap_open_live(DEVICE, 2048, 0, 0, errbuf);
    if (*errbuf) {
        fprintf(stderr, "%s", errbuf);
    }
    if (!pcap) {
        return -1;
    }
    return 0;
}

/* Sends the packet stored in packet to the socket specified in
 * initialize_pcap, and displays logging information. */
void *
send_packets(void * unused)
{
    if (packet == NULL) {
        printf("Cannot send an empty packet\n");
        return unused;
    }

    int ret;

    while (spam_packets && (ret = pcap_inject(pcap, packet, packet_len) > 0)) {
        printf(".");
        sleep(sleep_time);
    }
    if (ret <= 0) {
        fprintf(stderr, "Error in pcap_inject(), returned %d\n", ret);
    }
    return unused;
}

/* Listens to the Unix socket for the packet that we should be sending to the
 * receiving Pi. When it gathers all the information for it, such as
 * destination, data, speed, etc. it starts sending the packet. */
void
listen_packet_info(void)
{
    while (1) {
        while((packet_len_temp = 
               recv(python_fd, packet_temp, PACKET_BUFF_LEN, 0)) <= 0);

        /* TODO: Get rid of this ugly sizeof hack. */
        SEASIDE seaside_header;
        const SEASIDE *ss_temp = (SEASIDE *) 0;
        const int header_size = sizeof(SEASIDE) - sizeof(ss_temp->data);
        memcpy(&seaside_header, packet_temp, header_size);
        seaside_header.data = packet_temp + header_size;

        /* Byte ordering */
        seaside_header.size = seaside_header.size;

        /* seaside_header.type = packet_temp[0];
        seaside_header.size = ntohs(*(uint16_t *) (packet_temp + 1));
        seaside_header.data = packet_temp + 3; */

        printf("Type: [%d], size: [%d]\n", seaside_header.type, seaside_header.size);
        for (int i = 0; i < packet_len_temp; ++i) {
            printf("%i ", packet_temp[i]);
        }
        printf("\n");

        switch (seaside_header.type) {
        /* An Ethernet frame was received. Update our packet to reflect it. */
        case SEASIDE_PACKET:
            memcpy(packet, seaside_header.data, seaside_header.size);
            packet_len = seaside_header.size;
            break;

        /* We should start sending, if not already sending. */
        case SEASIDE_START:
            if (spam_packets < 1) {
                (void) __sync_add_and_fetch(&spam_packets, 1);
                pthread_create(&send_thread, NULL, send_packets, NULL);
            }
            break;

        /* We should stop sending, if we have not already stopped. */
        case SEASIDE_STOP:
            if (spam_packets > 0) {
                (void) __sync_sub_and_fetch(&spam_packets, 1);
                (void) pthread_join(send_thread, NULL);
            }
            break;

        /* Change the sleep time to attempt to reach a target bandwidth. */
        case SEASIDE_SLEEP_TIME:
            /* TODO: Change length to accurately reflect sleep_time. */
            sleep_time = seaside_header.data[0];
            break;
        }
    }
    printf("Broke out of loop\n");
}

/* Initializes pcap and the socket, and then sends the packet that was
 * received from the Python program. */
int
main(void)
{
    if (initialize_pcap()) {
        printf("Error in initialize_pcap().\n");
        return -1;
    }
    if (initialize_socket()) {
        printf("Error in initialize_socket().\n");
        return -1;
    }
    printf("Successfully initialized everything.\n");
    listen_packet_info();
    close(python_fd);
    pcap_close(pcap);
}
