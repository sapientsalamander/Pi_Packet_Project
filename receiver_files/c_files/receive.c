#include <pcap.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

/* The device that we will be listening to. */
#define DEVICE "eth0"

/* The file that the Python side will create, and the one we will connect
 * to initialize the socket. */
#define PYTHON_SOCKET "/tmp/receive_socket"

/* The size of the buffer that holds incoming packets. */
#define PCAP_BUFFER_SIZE 2097152

/* These next few declarations are for the Python socket that we will be
 * opening, so we can redirect any incoming packets to the Python UI. */
static struct sockaddr_un address;
static int socket_fd;

/* pcap structure used for interfacing with sending side. Handles most of the
 * backend of packet sniffing for us. */
pcap_t *handle = NULL;

/* Static error buffer that holds any errors that pcap returns back to us. 
 * Used so that you don't have to declare an error buffer per function. */
static char errbuf[PCAP_ERRBUF_SIZE];

/* Function that is invoked whenever a packet is received. Takes in a
 * struct pcap_pkthdr, which contains information about the size of
 * the packet. It then sends the received packet to the Python socket
 * that we opened earlier. */
void
callback(u_char *user,
         const struct pcap_pkthdr *pkthdr,
         const u_char *packet)
{
    static int count = 0; /* Total number of packets received. */
    /* Print general information about this packet. */
    printf("User [%s], packet number [%d], size of portion [%d], "
           "size of packet [%d].\n", 
           user, ++count, pkthdr->caplen, pkthdr->len);

    /* Redirect the packet to the Python socket. */
    int n = send(socket_fd, packet, pkthdr->caplen, 0);
    if (n < 0) {
        fprintf(stderr, "Error writing to socket.\n");
    }
}

/* Initialize the Python socket by attemping to open a file descriptor
 * that has already been created by the Python side. */
static int
initialize_socket(void)
{
    /*Initialize the type of socket. */
    socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (socket_fd < 0) {
        fprintf(stderr, "Error opening socket().\n");
        return -1;
    }

    memset(&address, 0, sizeof(struct sockaddr_un)); /* Zero out address. */

    address.sun_family = AF_UNIX;
    strcpy(address.sun_path, PYTHON_SOCKET);

    /* Attempt to connect to the file, and if it failed, keep attempting to
     * connect (in the case that the Python program has not yet started). */
    const socklen_t size_sock = sizeof(struct sockaddr_un);
    const struct sockaddr *pointer_sock = (struct sockaddr *) &address;
    while (connect(socket_fd, pointer_sock, size_sock) < 0) {
        printf("connect() failed. Check that the Python program is up.\n");
        sleep(1);
    }
    printf("Successfully connected to Python socket.\n");

    return 0;
}

/* Sets a new filter on the pcap_t. For syntax, see the man pages on
 * pcap-filter, it describes the arguments that the filter can be supplied.
 * This function can be called while pcap is listening for packets, but
 * any packets that were received and not yet processed may or may not be
 * dropped. */
static int
pcap_set_filter(const char *filter)
{
    /* Structure used for compiling a filter into something pcap can use. */
    struct bpf_program fp;

    if (pcap_compile(handle, &fp, filter, 0, PCAP_NETMASK_UNKNOWN) == -1) {
        fprintf(stderr, "pcap_compile() failed.\n");
        fprintf(stderr, "pcap error is %s.\n", pcap_geterr(handle));
        return -1;
    }

    if (pcap_setfilter(handle, &fp) == -1) {
        fprintf(stderr, "pcap_setfilter() failed.\n");
        return -1;
    }

    return 0;
}

/* Initialize the pcap interface we will use to capture packets. When that's
 * finished, we run pcap_loop, which takes over this thread and calls the
 * handler that we specified whenever it sniffs any incoming packet. */
static int
run_pcap(void)
{
    handle = pcap_create(DEVICE, errbuf);

    if (handle == NULL) {
        fprintf(stderr, "pcap failed to create handler: %s.\n", errbuf);
        return -1;
    }

    if (pcap_set_buffer_size(handle, PCAP_BUFFER_SIZE)) {
        fprintf(stderr, "pcap_set_buffer_size() failed to expand buffer.\n");
        return -1;
    }

    if (pcap_set_promisc(handle, 1)) {
        fprintf(stderr, "pcap_set_promisc() couldn't set promiscuous mode.\n");
        return -1;
    }

    if (pcap_activate(handle)) {
        fprintf(stderr, "pcap couldn't intialize handler.\n");
        fprintf(stderr, "pcap error is %s.\n", pcap_geterr(handle));
        return -1;
    }

    if (pcap_set_filter("port 4321")) {
        fprintf(stderr, "Error in pcap_set_filter helper function.\n");
        return -1;
    }

    printf("Successfully initialized pcap.\n");
    printf("Waiting for packets...\n");

    /* pcap function, where we give it a function to call whenever it receives
     * a packet, and then it starts to listen for packets, which is blocking,
     * i.e. takes over this thread, so in theory should never reach end of
     * the function. */
    pcap_loop(handle, -1, callback, NULL);

    return 0; /* Should never reach here. */
}

/* Initialize the Python socket, and runs pcap. Since pcap takes over this
 * thread, it will never reach the end (barring any errors). */
int
main(void)
{
    if (initialize_socket()) {
        fprintf(stderr, "Error in initialize_socket().\n");
        return -1;
    }

    if (run_pcap()) {
        fprintf(stderr, "Error in run_pcap().\n");
        return -1;
    }

    return 0;
}
