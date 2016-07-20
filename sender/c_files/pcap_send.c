#include <pcap.h>
#include <pthread.h>
#include <stdbool.h>
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

/* These next few declarations are for the Python socket that we will be
 * opening, so we can redirect any incoming packets to the Python UI. */
/* The buffer that will be used to hold the packet that Python sends over,
 * must be big enough to gurantee that it does not overflow (obviously). */
static struct sockaddr_un address;
static int socket_fd, python_fd;

/* Static error buffer that holds any errors that pcap returns back to us.
 * Used so that you don't have to declare an error buffer per function. */
static char errbuf[PCAP_ERRBUF_SIZE] = {'\0'};
static pcap_t *pcap;

static u_char packet[PACKET_BUFF_LEN];

/* Boolean to share between threads. As long as send is true, the sending
 * thread will spam the receiving Pi with as many packets as it can send.
 * If it turns false, it will stop sending packets. */
static volatile bool spam_packets = false;

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
    pcap = pcap_open_live("eth0", 2048, 0, 0, errbuf);
    if (*errbuf) {
        fprintf(stderr, "%s", errbuf);
    }
    if (!pcap) {
        return -1;
    }
    return 0;
}

/* Sends the packet stored in packet using the pcap library to the socket
 * specified in initialize_pcap, and displays logging information. */
void
send_packets(void)
{
    const int MSG_LEN = recv(python_fd, packet, PACKET_BUFF_LEN, 0);
    printf("Received packet, size[%d].\n", MSG_LEN);
    for (int i = 0; i < MSG_LEN; ++i) {
        printf("%i ", packet[i]);
    }
    int n;
    while (spam_packets && (n = pcap_inject(pcap, packet, MSG_LEN)) > 0) {
        printf("pcap_inject successfully injected %d bytes.\n", n);
        sleep(1);
    }
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
    //pthread_t one, two;
    //pthread_create(&one, NULL, send_packets, NULL);
    //pthread_create(&two, NULL, send_packets, NULL);
    printf("Successfully initialized everything.\n");
    spam_packets = true;
    send_packets();
    close(python_fd);
    pcap_close(pcap);
}
