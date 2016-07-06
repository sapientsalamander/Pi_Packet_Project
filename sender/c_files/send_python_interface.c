#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <string.h>

#define BUFLEN 512
#define SERVER_IP "10.0.24.243"
#define PORT 7777

int main(void) {
   struct sockaddr_in si_other;
   int s, slen = sizeof(si_other);
   char buf[BUFLEN];

   if((s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) {
      printf("Cannot construct socket\n");
      return 1;
   }

   memset((char *) &si_other, 0, sizeof(si_other));
   si_other.sin_family = AF_INET;
   si_other.sin_port = htons(PORT);
   if(inet_aton(SERVER_IP, &si_other.sin_addr) == 0) {
      printf("Cannot conver server ip address\n");
      return 1;
   }

   int i = 0;
   while(1) {
      if(sendto(s, buf, BUFLEN, 0, (struct sockaddr *)&si_other, slen) == -1) {
         printf("Cannot send packet\n");
         return 1;
      }
      ++i;
   }
   close(s);
   return 0;
}
