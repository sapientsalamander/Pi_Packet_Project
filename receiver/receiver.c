#include <pcap.h>
#include <stdio.h>
#include <string.h>

/* Name of the device that we will be listening to (ex. eth0, wla0...). 
   Includes the null terminator. */
#define DEVICE_NAME_LENGTH 64

/* Static error buffer that holds any errors that pcap returns back to us. 
   Used so that you don't have to declare an error buffer per function. */
static char errbuf[PCAP_ERRBUF_SIZE];

void callback(u_char *user,
              const struct pcap_pkthdr *pkthdr,
              const u_char *packet);

int get_listening_device(char *dev, int dev_length);

int main(int argc, char *argv[]) {
    char dev[DEVICE_NAME_LENGTH];
    pcap_t *descr;
    
    /* If name of device is passed as command-line argument,
       use that as the device name. If not, get it from stdin. */
    if (argc == 2) {
        dev[0] = '\0';
        strncat(dev, argv[1], DEVICE_NAME_LENGTH-1);
    } else {
        if (get_listening_device(dev, DEVICE_NAME_LENGTH)) {
            printf("get_listening_device() failed\n");
            return -1;
        }
    }
    
    struct bpf_program fp;
    bpf_u_int32 pMask;
    bpf_u_int32 pNet;
    
    pcap_lookupnet(dev, &pNet, &pMask, errbuf);
    descr = pcap_open_live(dev, BUFSIZ, 0, -1, errbuf);
    
    if (descr == NULL) {
        printf("pcap_open_live() failed to open: %s\n", errbuf);
        return -1;
    }
    
    if (pcap_compile(descr, &fp, "tcp", 0, pNet) == -1) {
        printf("pcap_compile() failed\n");
        return -1;
    }
    
    if (pcap_setfilter(descr, &fp) == -1) {
        printf("pcap_setfilter() failed\n");
        return -1;
    }
    
    pcap_loop(descr, -1, callback, NULL);
    
    return 0;
}

/* Displays a list of available device and prompts the user to select
   a device to listen to. */
int
get_listening_device(char *dev, int dev_length)
{
    /* Pointer to device, held in a linked list structure. */
    pcap_if_t *alldevs;
        
    /* Find all devices that we can listen from. */
    if (pcap_findalldevs(&alldevs, errbuf) == -1) {
        printf("Error in pcap_findalldevs: %s\n", errbuf);
        return -1;
    }
        
    /* Display the name of each device, with a description (if available). */
    for (pcap_if_t *d = alldevs; d; d = d->next) {
        printf("%s", d->name);
        if(d->description) {
            printf(": %s", d->description);
        }
        printf("\n");
    }
    
    printf("Enter the name of a device: ");
    
    fgets(dev, dev_length-1, stdin);
        
    /* Get rid of the newline character. */
    dev[strlen(dev)-1] = '\0';
    
    return 0;
}

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
}
