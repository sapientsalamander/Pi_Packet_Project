#include <pcap.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

/* The device that we will be listening to. */
#define DEVICE "eth0"

/* The file that the Python side will create, and the one we will connect
 * to initialize the socket. */
#define PYTHON_SOCKET "/tmp/receive_socket"

/* These next few declarations are for the Python socket that we will be
 * opening, so we can redirect any incoming packets to the Python UI. */
static struct sockaddr_un address;
static int socket_fd;
static socklen_t address_length;

/* Static error buffer that holds any errors that pcap returns back to us. 
 * Used so that you don't have to declare an error buffer per function. */
static char errbuf[PCAP_ERRBUF_SIZE] = {'\0'};

/* Function that is invoked whenever a packet is received. Takes in a
 * struct pcap_pkthdr, which contains information about the length of
 * the packet. It then sends the received packet to the Python socket
 * that we opened earlier. */
void 
callback(u_char *user,
         const struct pcap_pkthdr *pkthdr,
         const u_char *packet)
{
    static int count = 0; /* Total number of packets received. */

    /* Print general information about this packet. */
    printf("User [%s], packet number [%d], length of portion [%d], "
           "length of packet [%d]\n", 
           user, ++count, pkthdr->caplen, pkthdr->len);

    /* Redirect the packet to the Python socket. */
    int n = send(socket_fd, packet, pkthdr->caplen, 0);
    if (n < 0) {
        printf("Error writing to socket\n");
    }
}

/* Initialize the Python socket by attemping to open a file descriptor
 * that has already been created by the Python side. */
int
initialize_socket()
{
    /*Initialize the type of socket. */
    socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (socket_fd < 0) {
        printf("socket() failed\n");
        return -1;
    }

    memset(&address, 0, sizeof(struct sockaddr_un)); /* Zero out address. */

    address.sun_family = AF_UNIX;
    strcpy(address.sun_path, PYTHON_SOCKET);

    /* Attempt to connect to the file, and check to see if successful. */
    int connect_return = connect(socket_fd, (struct sockaddr *)&address,
                                 sizeof(struct sockaddr_un));

    if(connect_return < 0) {
        printf("connect() failed\n");
        return -1;
    }

    return 0;
}

/* Initialize the pcap interface we will use to capture packets. When that's
 * finished, we run pcap_loop, which takes over this thread and calls the
 * handler that we specified whenever it sniffs any incoming packet. */
int
run_pcap()
{
    pcap_t *descr;
    
    struct bpf_program fp;
    bpf_u_int32 pMask;
    bpf_u_int32 pNet;
    
    pcap_lookupnet(DEVICE, &pNet, &pMask, errbuf);
    descr = pcap_open_live(DEVICE, BUFSIZ, 0, -1, errbuf);
    
    if (descr == NULL) {
        printf("pcap_open_live() failed to open: %s\n", errbuf);
        return -1;
    }
    
    if (pcap_compile(descr, &fp, "port 7777", 0, pNet) == -1) {
        printf("pcap_compile() failed\n");
        return -1;
    }
    
    if (pcap_setfilter(descr, &fp) == -1) {
        printf("pcap_setfilter() failed\n");
        return -1;
    }
    
    pcap_loop(descr, -1, callback, NULL);
}

/* Initialize the Python socket, and runs pcap. Since pcap takes over this
 * thread, it will never reach the end (barring any errors). */
int
main(int argc, char *argv[])
{
    int err;

    if (err = initialize_socket()) {
        return err;
    }

    if (err = run_pcap()) {
        return err;
    }

    /* Old stuff, was playing around with threads. Will leave here for now
     * as a reference in case we need any of it later. */
    /*pthread_t python_threads, python_update;
    int rc = pthread_create(&python_threads, NULL, initialize, NULL);
    if(rc) {
        printf("Error %d\n", rc);
        exit(-1);
    }
    sleep(1000);
    initialize(NULL);*/
    return 0;
}
