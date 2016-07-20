#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <linux/if_packet.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <net/if.h>
#include <netinet/ether.h>

#define PACKET_INTERFACE "eth0"
#define PORT 666

static char packet[] = 
{184, 39, 235, 97, 27, 212, 184, 39, 235, 38, 96, 208, 8, 0, 69, 0, 0, 50, 0,
 1, 0, 0, 64, 17, 52, 214, 10, 0, 24, 242, 10, 0, 24, 243, 2, 154, 2, 154, 0,
 30, 203, 251, 84, 104, 105, 115, 32, 105, 115, 32, 97, 32, 109, 101, 115,
 115, 97, 103, 101, 46, 32, 69, 110, 100};

int NUM_PACKS_PER_CALL = 32;

int main(void) {
    int sockfd;
    struct ifreq if_idx, if_mac;
    struct sockaddr_ll socket_address;
    struct mmsghdr msg[NUM_PACKS_PER_CALL];
    struct iovec msg_packet;


    sockfd = socket(AF_PACKET, SOCK_DGRAM, IPPROTO_RAW);
    if (sockfd == -1) {
        perror("socket()");
        exit(EXIT_FAILURE);
    }

    memset(&if_idx, 0, sizeof(struct ifreq));
    strncpy(if_idx.ifr_name, PACKET_INTERFACE, sizeof(PACKET_INTERFACE));
    if (ioctl(sockfd, SIOCGIFINDEX, &if_idx) < 0) {
        perror("SIOCGIFINDEX");
    }
    memset(&if_mac, 0, sizeof(struct ifreq));
    strncpy(if_mac.ifr_name, PACKET_INTERFACE, sizeof(PACKET_INTERFACE));
    if (ioctl(sockfd, SIOCGIFHWADDR, &if_mac) < 0) {
        perror("SIOCGIFHWADDR");
    }

    socket_address.sll_ifindex = if_idx.ifr_ifindex;
    socket_address.sll_halen = ETH_ALEN;
    for(int i = 0; i < 6; ++i) {
        socket_address.sll_addr[i] = packet[i];
    }
    socket_address.sll_protocol = 0x0008; //TODO: Fix

    memset(&msg_packet, 0, sizeof(msg_packet));
    //for(int i = 0; i < NUM_PACKS_PER_CALL; ++i) {
        msg_packet.iov_base = packet + 14;
        msg_packet.iov_len = sizeof(packet) - 14;
    //}

    memset(&msg, 0, sizeof(msg));
    for(int i = 0; i < NUM_PACKS_PER_CALL; ++i) {
    msg[i].msg_hdr.msg_iov = &msg_packet;
    msg[i].msg_hdr.msg_iovlen = 1;//NUM_PACKS_PER_CALL;
    msg[i].msg_hdr.msg_name = (struct socketaddr_ll *) &socket_address;
    msg[i].msg_hdr.msg_namelen = sizeof(socket_address);
    }

    int ret = -1;
    printf("NUM = %d\n", NUM_PACKS_PER_CALL);
    while (ret < 0) ret = sendmmsg(sockfd, msg, NUM_PACKS_PER_CALL, 0);
    //while(ret > 0) ret = sendto(sockfd, packet + 14, sizeof(packet) - 14, 0, (struct sockaddr *) &socket_address, sizeof(socket_address));
    printf("error: %d.\n", errno);

    return 0;
}
