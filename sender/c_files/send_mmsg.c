#define _GNU_SOURCE
#include <errno.h>
#include <netinet/ip.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <net/if.h>
#include <linux/if_packet.h>
#include <sys/ioctl.h>

#define NUM_PACKS_PER_CALL 35
#define PORT 666

static char packet[64] = 
{184, 39, 235, 97, 27, 212, 184, 39, 235, 38, 96, 208, 8, 0, 69, 0, 0, 50, 0,
 1, 0, 0, 64, 17, 52, 214, 10, 0, 24, 242, 10, 0, 24, 243, 2, 154, 2, 154, 0,
 30, 203, 251, 84, 104, 105, 115, 32, 105, 115, 32, 97, 32, 109, 101, 115,
 115, 97, 103, 101, 46, 32, 69, 110, 100};

int main(void) {
    int sockfd;
    struct ifreq ifr;
    struct sockaddr_in addr;
    struct mmsghdr msg;
    struct iovec msg_packet[NUM_PACKS_PER_CALL];

    sockfd = socket(AF_INET, SOCK_DGRAM, 0);//, IPPROTO_RAW);
    if (sockfd == -1) {
        perror("socket()");
        exit(EXIT_FAILURE);
    }
    memset(&ifr, 0, sizeof(ifr));
    snprintf(ifr.ifr_name, sizeof(ifr.ifr_name), "eth0");
    if (setsockopt(sockfd, SOL_SOCKET, SO_BINDTODEVICE, (void *) &ifr, sizeof(ifr)) < 0) {
        printf("Cannot bind socket\n");
    }

    /*addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = inet_addr("10.0.24.243");
    addr.sin_port = htons(666);
    if (connect(sockfd, (struct sockaddr *) &addr, sizeof(addr)) == -1) {
        perror("connect()");
        exit(EXIT_FAILURE);
    }*/

    memset(&msg_packet, 0, sizeof(msg_packet));
    for(int i = 0; i < NUM_PACKS_PER_CALL; ++i) {
        msg_packet[i].iov_base = packet;
        msg_packet[i].iov_len = sizeof(packet);
    }

    struct sockaddr_in sin;
    memset(&sin, 0, sizeof(sin));
    sin.sin_family = AF_INET;
    sin.sin_addr.s_addr = inet_addr("10.0.24.243");

    memset(&msg, 0, sizeof(msg));
    msg.msg_hdr.msg_iov = msg_packet;
    msg.msg_hdr.msg_iovlen = NUM_PACKS_PER_CALL;

    int ret = 0;
    //while(!ret) ret = sendto(sockfd, packet, sizeof(packet), 0, (struct sockaddr *) &sin, sizeof(sin));

    /*while(1) if (send(sockfd, packet, sizeof(packet), 0) < 0) printf("Error\n");*/
    while(ret != -1) ret = sendmmsg(sockfd, &msg, 1, 0); printf("Error %d\n", ret);
    printf("error: %d.\n", errno);

    return 0;
}
