#include <arpa/inet.h>
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
#define PYTHON_SOCKET "/tmp/send_socket"

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

/* Struct to hold the info that we receive from the UI side. The type
 * refers to the type of data that it holds (see above defines), and the size
 * member is the size of the data that it receives. */
typedef struct {
    uint8_t type;
    uint16_t size;
    uint8_t *data;
} __attribute__((packed)) SEASIDE;

/* These next few declarations are for the UI socket that we will be
 * opening, so we can redirect any incoming packets to the UI. */
static struct sockaddr_un address;
static int socket_fd;

/* */
static struct sockaddr *pointer_sock;
static socklen_t size_sock;

/* A thread dedicated solely to sending packets onto the wire. */
static pthread_t send_thread;

/* Static error buffer that holds any errors that pcap returns back to us.
 * Used so that you don't have to declare an error buffer per function. */
static char errbuf[PCAP_ERRBUF_SIZE];
static pcap_t *handle;

/* packet and packet length, to send to the receiving Pi. Both need _temp
 * variables because while we are sending, we are also listening in for new
 * packets to send, and we need to store these new packets without corrupting
 * a send, so we store them in temporary variables while the sending function
 * finishes up, and then we sync them. */
static uint8_t packet[UI_BUFFER_SIZE];
static uint8_t packet_temp[UI_BUFFER_SIZE];
size_t packet_len;
ssize_t packet_len_temp;

/* Boolean to share between threads. As long as send is true, the sending
 * thread will spam the receiving Pi with as many packets as it can send.
 * If it turns false, it will stop sending packets. */
static volatile unsigned int spam_packets = 0;

/* Variable to hold how many packets we have sent. Used for diagnostic
 * purposes on the UI side. */
static volatile unsigned long long num_packets_sent = 0;

/* How long we should wait in between each sent packet. */
static uint8_t sleep_time_seconds = 1;
static int32_t sleep_time_useconds = 0;

/* Initializes the socket that will be used to receive packet info from
 * the UI program. It binds to the file specified as PYTHON_SOCKET,
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
    strcpy(address.sun_path, PYTHON_SOCKET);
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

/* Opens up an ethernet socket from pcap, to be used when sending packets
 * over the wire. */
static int
initialize_pcap(void)
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

    if (pcap_activate(handle)) {
        fprintf(stderr, "pcap couldn't intialize handler.\n");
        fprintf(stderr, "pcap error is %s.\n", pcap_geterr(handle));
        return -1;
    }

    return 0;
}

/* static int
send_statistics(void)
{
    SEASIDE python_seaside;

    python_seaside.type = SEASIDE_NUM_PACKETS;
    python_seaside.size = sizeof(num_packets_sent);

    char buffer[sizeof(SEASIDE) + python_seaside.size];

    memcpy(buffer, &python_seaside, sizeof(SEASIDE));
    unsigned long long num_temp = num_packets_sent;
    memcpy(buffer + sizeof(SEASIDE), &num_temp, sizeof(num_temp));

    ssize_t ret;
    if ((ret = send(python_fd, buffer, sizeof(buffer), 0)) < 0) {
        fprintf(stderr, "Error with sending to UI socket.\n");
        return -1;
    }

    return 0;
} */

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

/* Send a packet through the pcap interface. */
static int
send_packet(void)
{
    return pcap_inject(handle, packet, packet_len);
}

/* Sends the packet stored in packet to the socket specified in
 * initialize_pcap, and displays logging information. */
/* WARNING: Before you change anything the packet, sleep time, etc.
 * be sure to kill this thread, make any changes you want, and then
 * start the thread back up, to ensure that there are no race conditions. */
static void *
send_packets(void *unused)
{
    if (packet == NULL) {
        printf("Cannot send an empty packet\n");
        return unused;
    }

    /* How long to wait in between each check of spam_packets, to see
     * if we should exit or not. */
    const long SPAM_CHECK_TIME = 500000;

    struct timespec cur_time, end_time, sleep_time;
    long diff;
    ssize_t ret = 0;

    /* Converting the sleep data we got from spam_packets to the
     * timespec struct, for ease of use. */
    sleep_time.tv_sec = sleep_time_seconds;
    sleep_time.tv_nsec = sleep_time_useconds * 1000;

    clock_gettime(CLOCK_MONOTONIC, &cur_time);
    end_time = cur_time;

    do {
        end_time = timespec_add(&end_time, &sleep_time);

        /* Basically a non-blocking sleep. We could just sleep the entire
         * time, but then if we want to send a new packet, for example,
         * we would have to wait until it's done sleeping. Instead,
         * we just sleep in small increments, and check to see if we
         * should exit for whatever reason. */
        do {
            clock_gettime(CLOCK_MONOTONIC, &cur_time);
            diff = (end_time.tv_sec - cur_time.tv_sec) * 1000000
                 + (end_time.tv_nsec - cur_time.tv_nsec) / 1000;

            /* Sleep for either SPAM_CHECK_TIME, or the rest of the
             * sleep time, which ever one is smaller. Then cap it to
             * 0, just in case diff is < 0. */
            const long SLEEP_TIME = MAX(MIN(SPAM_CHECK_TIME, diff), 0);
            if (SLEEP_TIME >= 1000000) {
                fprintf(stderr, "Something went wrong in the calculation"
                       " of SLEEP_TIME; it's too big for usleep, and will"
                       " have the potential of breaking it.");
            } else {
                usleep(SLEEP_TIME);
            }

            if (!spam_packets) {
                break;
            }
        } while (diff > 0);

        printf(".");

    } while (spam_packets &&
            (ret = send_packet()) >= 0);

    if (ret < 0) {
        fprintf(stderr, "Error in send_packet(), returned %d\n", ret);
        printf("%s\n", pcap_geterr(handle));
    }

    return unused;
}

/* Helper function to set spam_packets to 1 and spawns a new thread
 * to start sending packets. */
static void
start_sending(void)
{
    if (spam_packets < 1) {
        (void) __sync_add_and_fetch(&spam_packets, 1);
        pthread_create(&send_thread, NULL, send_packets, NULL);
    }
}

/* Helper function to set spam_packets to 0 and then waits for the sending
 * thread to join before returning. */
static void
stop_sending(void)
{
    if (spam_packets > 0) {
        (void) __sync_sub_and_fetch(&spam_packets, 1);
        (void) pthread_join(send_thread, NULL);
    }
}

/* Listens to the Unix socket for the packet that we should be sending to the
 * receiving Pi. When it gathers all the information for it, such as
 * destination, data, speed, etc. it starts sending the packet. */
static void *
listen_packet_info(void *ui_fd_temp)
{
    int ui_fd = *(int *) ui_fd_temp;
    while (1) {
        while ((packet_len_temp = 
               recv(ui_fd, packet_temp, UI_BUFFER_SIZE, 0)) <= 0);

        SEASIDE seaside_header;

        /* WARNING: If you ever change the layout or order of the SEASIDE
         * struct, be sure to change this copying bit, too. */
        memcpy(&seaside_header.type, packet_temp, sizeof(uint8_t));
        memcpy(&seaside_header.size, (packet_temp + 1), sizeof(uint16_t));
        seaside_header.data = packet_temp + 3;

        printf("Type: [%d], size: [%d]\n",
            seaside_header.type, seaside_header.size);
        for (int i = 0; i < packet_len_temp; ++i) {
            printf("%i ", packet_temp[i]);
        }
        printf("\n");

        /* A state variable, to remember if we were sending before we
         * stopped. After we parse the SEASIDE packet, we continue
         * sending if we were already sending before (or a start
         * flag was sent). */
        unsigned int should_continue_sending = spam_packets;

        stop_sending();

        switch (seaside_header.type) {

        /* An Ethernet frame was received. Update our packet to reflect it. */
        case SEASIDE_PACKET:
            memcpy(packet, seaside_header.data, seaside_header.size);
            packet_len = seaside_header.size;
            break;

        /* We should start sending, if not already sending. */
        case SEASIDE_START:
            should_continue_sending = 1;
            break;

        /* We should stop sending, if we have not already stopped. */
        case SEASIDE_STOP:
            should_continue_sending = 0;
            break;

        /* Change the sleep time in between each packet. */
        case SEASIDE_SLEEP_TIME:
            /* WARNING: If you ever change the types of sleep_time_seconds or
             * useconds, be sure to change the sizes here, too. */
            memcpy(&sleep_time_seconds, seaside_header.data, sizeof(uint8_t));
            memcpy(&sleep_time_useconds, seaside_header.data + 1, sizeof(int32_t));
            printf("Seconds: [%d], USeconds: [%d]\n",
                sleep_time_seconds, sleep_time_useconds);
            break;

        /* Send a single packet. */
        case SEASIDE_SINGLE_PACKET:
            send_packet();
            break;

        default:
            fprintf(stderr, "Invalid SEASIDE flag received.\n");
            break;
        }

        if (should_continue_sending) {
            start_sending();
        }
    }
    fprintf(stderr, "Error in listen_packet_info().\n");

    return NULL;
}

static int
accept_connections(void)
{
    int ui_fd;
    while (1) {
        if ((ui_fd = accept(socket_fd, pointer_sock, &size_sock)) < 0) {
            fprintf(stderr, "accept() failed.\n");
            return -1;
        }

        pthread_t ui_thread;
        pthread_create(&ui_thread, NULL, listen_packet_info, (void *) &ui_fd);
    }

    return -1;
}

/* Initializes pcap and the socket, and then sends the packet that was
 * received from the UI program. */
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
    accept_connections();
    close(socket_fd);
    pcap_close(handle);
}
