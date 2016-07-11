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
#define PYTHON_SOCKET "/tmp/receive_socket"


static struct sockaddr_un address;
static int socket_fd;
static socklen_t address_length;


/* Static error buffer that holds any errors that pcap returns back to us. 
   Used so that you don't have to declare an error buffer per function. */
static char errbuf[PCAP_ERRBUF_SIZE] = {'\0'};

/* Function that is invoked whenever a packet is received. Takes in a 
   struct pcap_pkthdr, which contains information about the length of
   the packet. */
void 
callback(u_char *user,
         const struct pcap_pkthdr *pkthdr,
         const u_char *packet)
{
    static int count = 0;
    printf("User [%s], packet number [%d], length of portion [%d], "
           "length of packet [%d]\n", 
           user, ++count, pkthdr->caplen, pkthdr->len);
           
    printf("Packet:\n");
    
    for (int len = pkthdr->caplen; len; --len, ++packet) {
        printf("%u ", (unsigned)*packet);
    }
    printf("\n\n");

    strncpy(msg, packet, pkthdr->len);

    int n = send(socket_fd, msg, pkthdr->caplen, 0);
    if(n < 0) {
        printf("Error writing to socket\n");
    } else {
        printf("Successfully wrote %d bytes to socket\n", n);
    }
}

void
initialize_socket()
{
    socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if(socket_fd < 0) {
        printf("socket() failed\n");
    }

    memset(&address, 0, sizeof(struct sockaddr_un));

    address.sun_family = AF_UNIX;
    strcpy(address.sun_path, PYTHON_SOCKET);

    if(connect(socket_fd, (struct sockaddr *)&address, sizeof(struct sockaddr_un)) < 0) {
        printf("connect() failed\n");
    }
}

int
main(int argc, char *argv[])
{
    initialize_socket();

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
