#include <arpa/inet.h>
#include <errno.h>
#include <sys/file.h>
#include <math.h>
#include <netinet/tcp.h>
#include <pcap.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

/* WARNING: Before you change anything too big, be sure to read through
 * all the WARNING comments, as they generally lay out some of the unintended
 * consequences that could happen if you change something. */

#define MAX(A,B) (A) < (B) ? (B) : (A)
#define MIN(A,B) (A) < (B) ? (A) : (B)

/* The device that we will be listening to. */
#define DEVICE "eth0"

/* The file that we will create in order to initialize a socket between this
 * program and the UI program(s). */
#define UI_SOCKET "/tmp/receive_socket"

/* The singleton file that we will attempt to create and lock. This is so
 * that only one instance of this program can be run. If another instance
 * attempts to run, the lock will fail, and it'll quietly exit. */
#define SINGLETON_FILE "/tmp/receive_singleton"

/* Filter that pcap applies to any incoming packets. */
#define PCAP_FILTER "port 4321"

/* The size of the buffer that holds incoming packets. */
#define PCAP_BUFFER_SIZE 2097152

/* The buffer that will be used to hold the packet that the UI sends over,
 * must be big enough to gurantee that it does not overflow (obviously). */
#define UI_BUFFER_SIZE 2048

#define NANOSECONDS_PER_SECOND 1000000000

#define SEASIDE_PACKET          0
#define SEASIDE_START           1
#define SEASIDE_STOP            2
#define SEASIDE_SLEEP_TIME      3
#define SEASIDE_NUM_PACKETS     4
#define SEASIDE_SINGLE_PACKET   5
#define SEASIDE_GET_PACKET      6
#define SEASIDE_GET_BANDWIDTH   7
#define SEASIDE_GET_PACKET_SIZE 8
#define SEASIDE_START_SEQUENCE  9
#define SEASIDE_STOP_SEQUENCE   10
#define SEASIDE_RESPONSE        11

/* Struct to hold the info that we receive from the UI side. The type
 * refers to the type of data that it holds (see above defines), and the size
 * member is the size of the data that it receives. */
typedef struct {
    uint8_t type;
    uint16_t size;
    uint8_t *data;
} __attribute__((packed)) SEASIDE;

/* Singleton file, used to ensure only once instance of this program
 * is running at a time. */
static int singleton_file;

/* These next few declarations are for the UI socket that we will be
 * opening, so we can redirect any incoming packets to the UI. */
static struct sockaddr_un address;
static int socket_fd;

/* The main server socket, located at UI_SOCKET. Other UI programs will
 * attempt to connect to this socket. */
static struct sockaddr *pointer_sock;
static socklen_t size_sock;

/* A thread dedicated solely to sending packets onto the wire. */
static pthread_t ui_listen_thread;

/* pcap handle for the listener that we'll create. */
static pcap_t *handle;

/* packet and packet length, to send to the receiving Pi. */
static uint8_t packet[UI_BUFFER_SIZE] = {'\0'};
static size_t packet_len = 0;

/* Mutex to ensure no two threads attempt to modify packet or packet_len
 * at the same time. */
static pthread_mutex_t packet_mutex;

/* Variable to hold the bandwidth calculation (bits/s). */
static unsigned long long bandwidth = 0;

/* Variable to hold how many packets we have received. Used for diagnostic
 * purposes on the UI side. */
static volatile uint32_t num_packets_received = 0;

/* Timespecs for received packets. Used to calculate bandwidth. */
static struct timespec cur_time;
static struct timespec packet_received_time;
static struct timespec prev_packet_received_time;
static struct timespec elapsed_time;

/* Helper function to add two timespecs together. */
static struct timespec
timespec_add(const struct timespec *t1, const struct timespec *t2)
{
    struct timespec result;

    result.tv_sec = t1->tv_sec + t2->tv_sec;
    result.tv_nsec = t1->tv_nsec + t2->tv_nsec;

    while (result.tv_nsec >= NANOSECONDS_PER_SECOND) {
        result.tv_nsec -= NANOSECONDS_PER_SECOND;
        result.tv_sec++;
    }

    return result;
}

/* Helper function to subtract two timespecs together. */
static struct timespec
timespec_sub(const struct timespec *t1, const struct timespec *t2)
{
    struct timespec result = *t1;

    /* TODO: While portable for a long, result.tv_nsec might overflow if
     * a weird datatype. */
    if (t1->tv_nsec < t2->tv_nsec) {
        result.tv_sec--;
        result.tv_nsec += NANOSECONDS_PER_SECOND;
    }

    result.tv_sec -= t2->tv_sec;
    result.tv_nsec -= t2->tv_nsec;

    return result;
}

/* Every time a packet is received, pcap calls this function. We use it to
 * store relevant information for later retrieval from the ui threads. */
/* TODO: Handle situations where we only receive part of a packet. */
/* TODO: See if we're still dropping packets at high-volume bandwidth. */
void
callback(u_char *user,
         const struct pcap_pkthdr *pkthdr,
         const u_char *packet_recv)
{
    (void) user;

    pthread_mutex_lock(&packet_mutex);

    num_packets_received++;
    prev_packet_received_time = packet_received_time;
    clock_gettime(CLOCK_MONOTONIC, &packet_received_time);
    printf("Timespec: %lld.%.9ld\n", (long long) packet_received_time.tv_sec,
                                     packet_received_time.tv_nsec);

    /* Stores the received packet for later diagnostic use. */
    memcpy(packet, packet_recv, pkthdr->caplen);
    packet_len = pkthdr->caplen;

    pthread_mutex_unlock(&packet_mutex);
}


/* Initializes the socket that will be used to receive packet info from
 * the UI program. It binds to the file specified as UI_SOCKET,
 * and then listens in for any attempted connections. When it hears one,
 * we assume that it's the UI program, and we continue on our
 * merry way. */
static int
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
    strcpy(address.sun_path, UI_SOCKET);
    unlink(address.sun_path);

    /* Attempt to bind to the file, and then waits for the UI program
     * to connect. */
    size_sock = sizeof(struct sockaddr_un);
    pointer_sock = (struct sockaddr *) &address;
    if (bind(socket_fd, pointer_sock, size_sock) < 0) {
        fprintf(stderr, "bind() failed.\n");
        sleep(1);
        fprintf(stderr, "Retrying...\n");
    }

    if (listen(socket_fd, 8) < 0) {
        fprintf(stderr, "listen() failed.\n");
        return -1;
    }

    return 0;
}

/* Sends a response SEASIDE struct through an arbitrary file descriptor.
 * First sends the header SEASIDE struct (type and size), and then sends the
 * actual data. */
void
send_response(int ui_fd, void *data, uint16_t len)
{
    char buf[3];

    buf[0] = SEASIDE_RESPONSE;
    memcpy(buf + 1, &len, 2);

    if (send(ui_fd, buf, 3, MSG_MORE) < 0) {
        fprintf(stderr, "Error with send to ui_fd\n");
    }
    if (send(ui_fd, data, len, 0) < 0) {
        fprintf(stderr, "Error with send to ui_fd\n");
    }
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

/* Opens up an ethernet socket from pcap, to be used when sending packets
 * over the wire. */
static int
initialize_pcap(void)
{
    /* Error buffer for any error that pcap throws at us. */   
    static char errbuf[PCAP_ERRBUF_SIZE];

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

    if (pcap_set_filter(PCAP_FILTER)) {
        fprintf(stderr, "Error in pcap_set_filter helper function.\n");
        return -1;
    }

    printf("Successfully initialized pcap.\n");
    printf("Waiting for packets...\n");

    return 0;
}

/* Listens to the Unix socket for the packet that we should be sending to the
 * receiving Pi. When it gathers all the information for it, such as
 * destination, data, speed, etc. it starts sending the packet. */
static void *
listen_packet_info(void *ui_fd_temp)
{
    /* Temporary variables to store any received data, before moving it
     * to the global scope. */
    uint8_t request[UI_BUFFER_SIZE];
    ssize_t request_len;

    int ui_fd = *(int *) ui_fd_temp;
    while (1) {
        printf("Waiting for request\n");
        request_len = recv(ui_fd, request, UI_BUFFER_SIZE, 0);

        /* EOF signal received, will close socket in orderly manner. */
        if (request_len == 0) {
            close(ui_fd);
            return (void *) NULL;
        }

        SEASIDE seaside_header;

        /* WARNING: If you ever change the layout or order of the SEASIDE
         * struct, be sure to change this copying bit, too. */
        memcpy(&seaside_header.type, request, sizeof(uint8_t));
        memcpy(&seaside_header.size, (request + 1), sizeof(uint16_t));
        seaside_header.data = request + 3;

        printf("Type: [%d], size: [%d]\n",
            seaside_header.type, seaside_header.size);
        for (int i = 0; i < request_len; ++i) {
            printf("%i ", request[i]);
        }
        printf("\n");

        pthread_mutex_lock(&packet_mutex);

        switch (seaside_header.type) {

        /* Not supported on the receiving side. */
        case SEASIDE_PACKET:
            break;

        /* Not supported on the receiving side. */
        case SEASIDE_START:
            break;

        /* Not supported on the receiving side. */
        case SEASIDE_STOP:
            break;

        /* Not supported on the receiving side. */
        case SEASIDE_SLEEP_TIME:
            break;

        /* Return the number of received packets. */
        case SEASIDE_NUM_PACKETS:
            send_response(ui_fd, &num_packets_received,
                          sizeof(num_packets_received));
            break;

        /* Not supported on the receiving side. */
        case SEASIDE_SINGLE_PACKET:
            break;

        /* Return the current packet. */
        case SEASIDE_GET_PACKET:
            send_response(ui_fd, packet, packet_len);
            break;

        /* Return the bandwidth calculated. */
        /* TODO: See if we can cut down the size of this case. This is all
         * within the mutex, so we could be potentially blocking other
         * important processes. */
        /* TODO: Not accurate at speeds around 1 Mbps. */
        case SEASIDE_GET_BANDWIDTH:
            /* Calculates the elapsed time, and approximates the bandwidth from the
             * time between received packets. */
            clock_gettime(CLOCK_MONOTONIC, &cur_time);

            if (timespec_sub(&cur_time, &packet_received_time).tv_sec >= 1) {
                /* It's been a while since we've received a packet, so we
                 * set bandwidth to 0. */
                bandwidth = 0;
            } else {
                elapsed_time = timespec_sub(&packet_received_time,
                                            &prev_packet_received_time);
                double d_time = elapsed_time.tv_sec
                                + ( (double) elapsed_time.tv_nsec
                                    / NANOSECONDS_PER_SECOND );
    
                bandwidth = (packet_len * 8.0) / d_time;
                printf("Bandwidth: %llu | d_time: %Lf\n", bandwidth, d_time);
            }

            send_response(ui_fd, &bandwidth, sizeof(bandwidth));
            break;

        /* Return the size of the current packet. */
        case SEASIDE_GET_PACKET_SIZE:
            send_response(ui_fd, &packet_len, sizeof(packet_len));
            printf("Send packet size\n");
            break;

        default:
            fprintf(stderr, "Invalid SEASIDE flag received.\n");
            break;
        }

        pthread_mutex_unlock(&packet_mutex);
    }
    fprintf(stderr, "Error in listen_packet_info().\n");

    return NULL;
}

/* Listens at the specified socket descriptor for any incoming connections.
 * When it encounters one, it spawns a new thread to handle the connection,
 * and continues listening for any more connections. */
static void *
accept_connections(void *unused)
{
    int ui_fd;
    while (1) {
        if ((ui_fd = accept(socket_fd, pointer_sock, &size_sock)) < 0) {
            fprintf(stderr, "accept() failed.\n");
            perror(NULL);
            return unused;
        }

        pthread_t ui_thread;
        pthread_create(&ui_thread, NULL, listen_packet_info, (void *) &ui_fd);
    }

    return unused;
}

/* A singleton file, used to ensure that only one instance of this program
 * is running. It attempts to lock a certain file, specified by SINGLETON_FILE,
 * and if not successful, because another instance already locked it, returns
 * -1. */
static int
lock_single_instance_file(void)
{
    singleton_file = open(SINGLETON_FILE, O_CREAT | O_RDWR, 0666);
    if (flock(singleton_file, LOCK_EX | LOCK_NB)) {
        if (errno == EWOULDBLOCK) {
            fprintf(stderr, "The singleton file is already created. It's "
                    "assumed an instance of this program is already running."
                    " Exiting.\n");
            return -1;
            
        }
    }
    return 0;
}

/* Initializes pcap and the socket, and then sends the packet that was
 * received from the UI program. */
int
main(void)
{
    if (lock_single_instance_file()) {
        printf("Error in lock_single_instance_file().\n");
        return -1;
    }

    if (initialize_socket()) {
        printf("Error in initialize_socket().\n");
        return -1;
    }

    if (initialize_pcap()) {
        printf("Error in initialize_pcap().\n");
        return -1;
    }

    printf("Successfully initialized everything.\n");

    pthread_create(&ui_listen_thread, NULL, accept_connections, NULL);

    pcap_loop(handle, -1, callback, NULL);

    close(socket_fd);
    pcap_close(handle);
}

