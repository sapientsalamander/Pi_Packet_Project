# Pi Packet Project

This project focuses on the basics of networking. Two Raspberry Pi's will form a communication network where one will act as a sender and the other as a receiver. The sender will then attempt to form packets that can be preconfigured by the user and send them to the receiver. They will then display any diagnostic information that they have available on LCD shields that they are connected to.

For more information, check the rndwiki under Raspberry Pi Network Tools available on the rndwiki!

Read COMPILE_README.md for more information on compiling this sucker.

IMPORTANT: If you want to run the webserver or the LCD screen Python programs, you have to run them as modules from the root directory of this project. In essence, make sure that you're in the same directory as this README.md file, and then run the following command to start the server:

```bash
sudo python -m sender_files.website.server
```

## Overview
### System Overview

There are two main projects being worked on here: a Sending Pi and a Receiving Pi. The Sending Pi acts as a general packet generator, where you will be able to craft packets of different layers, configure fields within those layers, configure the bandwidth and other sending options, and then start sending. The Receiving Pi acts as a diagnostic tool. It displays information about any incoming packets, bandwidth, etc. They can be used in conjunction with one another, but they can also be separated and used independently.

### Assumptions

### Facts

1. Scapy is not capable of sending and receiving packets fast enough to saturate a 100 Mbps connection; it maxes out at around 6 Kbps.
2. The Raspberry Pi 3 (along with the 2) has an onboard Ethernet interface that maxes out at a theoretical 100 Mbps (although in reality the max is usually about 95-97 Mbps).
3. A Python <-> C interface, where Python handles the user interface and C manages the sending and receiving of packets, on the receiving Raspberry Pi increases the max bandwidth to ~7 Mbps. Note that this is with 64 byte packets; if you increase the size of the packets, then the bandwidth will also increase up to a max of 97-98 Mbps.
4. pcap will allow the sending of arbitrary packets, made up of a variety of layers, to be sent on an interface.
5. Cutting out a lot of the features of the C side (bandwidth calculations, more accurate bandwidth, etc.) will allow you to increase max throughput to about 15 Mbps.

### Limitations

1. The Raspberry Pi 3 cannot fully utilize a 1 Gbps port, as its onboard Ethernet interface can only handle 100 Mbps, and any attachments that increase the speed (ex. USB to Ethernet adapter) usually max out at around 200-300 Mbps.
2. A Raspberry Pi 3 processor can only put out about 30,000 packets a second (on a min-sized 64 byte packet. The size of the packet will alter this number slightly.) on the wire using standard C networking practices.

### Goals and Context

Our goal is to provide a simple standalone network tester on Raspberry Pi devices. It will consist of two devices: a traffic generator and a packet sniffer. This allows basic network testing without the use of a larger, more expensive traffic generators. The software should be flexible enough to run on any (Unix) machine, but fast enough so that it can run at a reasonable pace on a Raspberry Pi, the lowest benchmark for us.
1.6. Driving Requirements

1. Ability to configure packets using input on Sending Pi, including
    * Type of packets / different layers of a packet
    * MAC address
    * IP address
    * Source and Destination ports
    * Payload

2. Ability to display packet and system information on the Sending Pi, including:
    * CPU usage
    * Bandwidth
    * Utilization of the LED to visually display bandwidth

3. Ability to display packet and system information on the Receiving Pi, including:
    * Total number of packets received
    * Bandwidth currently used
    * IP address
    * MAC address
    * Payload
    * CPU usage (average and per core)
    * Utilization of the LED to visually display bandwidth

4. Ability to easily add more supported packet types

## Solution
### Overview

Python 2.7 was used, as some of the libraries utilized here did not support Python 3+.
For the C files, the compiler used must support the gnu99 or higher standard, and it must be specified using the -std flag. libpcap utilizes some of the types defined in gnu, and these types are not supported in any version of standard C (u_char, etc). Additionally, some gnu additions were used to remove struct alignment, which caused a great deal of trouble when taking packets apart.
Additionally, if this were to be ported to some other system, keep in mind that a couple of POSIX headers were utilized (unistd, pthread, etc.), and while Windows versions of them do exist, compiling for Windows will probably not work out of the box. Also, some Unix-specific files were used to gather information.

 

The Adafruit CharLCD library, a Python library, was used as an interface between the Raspberry Pi 3 and a 16x2 LCD.
Scapy, a Python network generator library, was used on the sending Pi to generate packets on the fly and send them over the network to the receiving Pi; Scapy can be installed through pip. Along with Scapy, you need to install tcpdump and python-crypto in order to properly filter packets; they can be obtained through apt-get.
netifaces was used to obtain source addresses.
daemontools was used to automatically run both the sending and receiving programs at boot and restart them in case of failure.
libpcap, a C interface for capturing packets, was used on the receiving Pi for high bandwidth retrieval.
psutil, a Python library "for retrieving information on running processes and system utilization", was used to update diagnostic information about CPU usage and other miscellaneous items.
enum34, a Python backport of enums, was used instead of custom solutions.
cherrypy was used as the backend of the web server.
Wireshark was used for independent traffic verification and packet analysis. 

netcat was used to open ports, stopping an ICMP "Port Unreachable" response (nc -ulk <port number>).
Alternatively, the Python socket module can be used to open ports by binding sockets to them.

 
### Shared Solutions
#### SEASIDE Structure

The struct that is used to communicate between the C Backend and UI programs has the following layout:
```C
typedef struct {
    uint8_t type;
    uint16_t size;
} __attribute__((packed)) SEASIDE;
```
type: A flag to indicate what type of information you are sending. The current flags are:
    * #define PACKET 0: signifies that a packet was received, which should get copied over to the buffered packet.
    * #define START 1: a flag to start sending out the buffered packet.
    * #define STOP 2: a flag to stop sending out the buffered packet.
    * #define SLEEP_TIME 3: indicates that data holds the amount of time to sleep in between each packet sent out.
    * #define NUMBER_PACKETS 4: the number of packets that the C side has received is sent over, used for diagnostic purposes on the Python side. Not currently implemented.
    * #define SINGLE_PACKET 5: signals the C program to send a single packet.
    * #define GET_PACKET 6: requests the currently buffered packet to be sent back.
    * #define GET_BANDWIDTH 7: requests the current bandwidth usage.
    * #define GET_PACKET_SIZE 8: requests the size of the buffered packet.
    * #define START_SEQUENCE 9: Not currently implemented.
    * #define STOP_SEQUENCE 10: Not currently implemented.
    * #define RESPONSE 11: When a statistic has been requested (7 - GET_BANDWIDTH, 8 - GET_PACKET_SIZE, etc.) the response is sent in a SEASIDE struct with this flag.
size: The length of data. This does not include the size of the header itself. Sometimes it is 0, such as in the case of the start and stop flags.

Along with the SEASIDE struct, there may optionally be other data sent with it, depending on the flag set. For example, a SEASIDE structure sent from the Python side to the C side with a type flag of PACKET and a size field of 64 means that along with the header, there will be an additional 64 bytes sent in the same frame that represents a fully formed packet. This also means that the total size of the frame sent from the Python side to the C side is 67 bytes (1 for type, 2 for size, and 64 bytes for data).

#### IPC Endianness

Please note that any communication between the C Backend and the UI programs are done in the device's natural endianness. The program DOES NOT explicitly convert data to Network Byte Order when talking to each other. If both sides are Little Endian, or both sides are Big Endian, this is not a problem. However, if they differ, then there's a problem. But this shouldn't be a realistic scenario, because this software is built around the assumption that all sides are on the same machine.

#### Shared Files

For a more detailed documentation of each of these files, check the files themselves. The module-level description is replicated here; specific function descriptions are in the files themselves.

Computations: Computations, in our project, are defined as functions retrieve various info that are scattered around the system. These can be files located in os wide dirs, like /sys/, or from user files, like /home/pi/. These can also have a layer of indirection, so we don't have to read the files ourselves, but use a library as an interface. As examples, various computations get the bandwidth on an interface, cpu usage, MAC address, etc.
Conversions: These functions convert the parameter to a different type or convert units.
LCD Input: A wrapper around the Adafruit LCD library. This extends the functionality to allow for easy and generic input that can be reused.
Multithreaded LCD: Functions to safely use an LCD screen with multiple threads. These functions are mostly wrappers for the LCD_Input_Wrapper and Adafruit_CharLCDPlate functions used with a multithreading lock.
SEASIDE: The Python side of SEASIDE interaction. Contains the enum of SEASIDE flags, including unimplemented ones, as well as two functions for sending SEASIDE communications. One function sends without expecting a response and is used to send instructions to the C-side. The other waits for a response and is used to request statistical information such as bandwidth usage.

### Sending Pi

The idea behind the Sending Pi is that we have one "main" backend program running in the background. This program is the one in charge of actually sending packets. In addition to this main program, we have various UI programs that are also running. These are what interact with a user. They get input from the user, and relay it back to the backend program. Using this idea, we can have multiple UI programs, each utilizing a different method of obtaining user input (in our example, we have one UI program in charge of obtaining input from an LCD screen attached to the Pi, and another UI program that hosts a web server). Any of these can relay information back to the backend program, even simultaneously. We can theoretically have as many UI programs as we want. The only limiting factor would be the system resources.

In our implementation, the Sending Pi has three different simultaneous processes running: a C program to send the packets, a Python program to deal with the LCD UI, and a Python Backend for a web server. The general outline for how these programs communicate are as follows:

* The C program is run, and sets up a sort of local "server" on a file. It then listens for any UI programs that attempt to connect, using Unix sockets as a form of IPC.
* It spawns a new thread for each UI program that connects. Each thread is in charge of one specific UI program. It listens for any incoming information, and deals with it accordingly.
* The UI programs, after successfully connecting to the C backend program, start interacting with the user. They pass any relevant information to the C Backend using the SEASIDE Structure.

#### C Backend

The C Backend is in charge of actually putting packets on the wire and interacting with the UI programs to receive input. It first initializes pcap, the library used to send packets. Our main form of IPC is to use Unix sockets. Because of this, it bind()s to /tmp/send_socket. This is the file used a gateway for the UI programs (the UI programs will attempt to connect() to this file). It starts listening for any incoming connections, and accepts each one. It then spawns a new thread to deal with the new connection, and continues to listen for any more incoming connections.

In terms of communication over the socket, the programs use the SEASIDE structure. Currently, communication is only initiated on the UI side. The thread that deals with each UI thread just sits there idly, waiting for input from the socket. Once it receives something, it parses the information and deals with it accordingly. In some cases, it will return a value back over the socket (such as in the case that the packet size or bandwidth was requested). It then continues to listen for any input. And it does this over and over for the entirety of its existence: listening for input and then dealing with the input. If the connection is closed gracefully by the UI program who initiated it, the thread will terminate.

There is one thread that deals with the sending of the packets. However, this packet may be killed and started up again. This is to ensure that any threads that update relevant information (packet, packet length, sleep time, etc.) are not changed mid-send. Once the values have been changed, the thread will be started up again (if it was up before). This thread will not be killed if only diagnostic information is requested from a UI thread (bandwidth, the contents of the packet, etc). In between each sending of a packet, this thread has a time that it should sleep (stored in sleep_seconds and sleep_useconds). However, the thread will not sleep for the entirety of this time. It will sleep in smaller increments, wake, check to see if it should kill itself, and continue sleeping. It does recalculate sleep time in between each wake to remain as accurate as possible.

The C Backend has a few global buffers, the main ones (for this paragraph) being the buffer used to hold the packet, an int to indicate the size of the packet, and the sleep time, and a global mutex. When first started, the packet buffer and the packet size are set to 0, while the sleep time is set to 1 second. The idea is that we will receive input from the UI threads to update and set these variables. We have attempted to make this all multithreading safe, by usage of locks and other methods (which is necessary if you have more than 1 UI thread). Whenever a UI receives input, it parses it, and then locks a global mutex. This is used so that only one UI thread can update the global information (packet, sleep time, etc.) at a time. First, if the sending thread is active, it kills it. It then updates the required information, and if the sending thread was active, it starts it back up again.

#### Python LCD

This Python program is in charge of all UI that is communicated through the LCD screen. When it first starts up, it attempts to connect to the socket created by the C Backend. It keeps retrying until successful. After it is able to connect to it, it spawns off other threads to deal with other parts of the screen. These include polling system data, such as CPU usage and bandwidth, and updating the screen. It then starts polling for user input, and handles that accordingly, either by sending a flag to the C Backend (such as the START and STOP flags), or by changing polling the user for more input (if the user wants to configure a packet/delay).

While we did use the Adafruit LCD library for easy interaction with the screen, we also wrote our own wrapper around that class. This was because while the Adafruit class did provide basic functionality (check to see if a button is pressed, set the screen to this value, etc.) we were looking for more robust solutions to polling the user for input. As such, we wrote a wrapper that introduced a few main functions, which include lcd_input_format(), which takes in a format of a string that you want to poll the user for. For example, if what you're looking for is an IP address from the user, you would pass it lcd_screen.lcd_input_format('%i%i%i.%i%i%i.%i%i%i.%i%i%i'). It then polls the user for input, and returns a string with the fields that you specified to be user-inputted (the %i's) filled out with user values. More information and additional helper functions can be found in the lcd_input.py file, found in the shared_files/ directory.
#### Python Web Server

One other UI that is available with this application is a web interface. You can connect to it through any (somewhat modern) browser. To access it, you just need to set the url to its IP address, and set the port to 8080. As it currently stands, the Sending Pi has a static IP address of 10.0.24.242, so to access it you would go to http://10.0.24.242:8080/. To connect, you must be on the same network as the Pis.

Through this web interface, you can do basically whatever you could using the LCD screen. It was included as an easier way to configure packets, because typing out a MAC address using four directional buttons is a big pain. In addition, you can also save and load custom pcap files, either from the Raspberry Pi or from your local machine.

We used CherryPy for the backend of this server. We found it to be the simplest library for supporting a web application, and was relatively easy to set up. It's used not only to serve pages to the client, but it also acts a sort of middleman for any communication that happens between the user and the C Backend. For example, the user may (behind the scenes) request the bandwidth from the web server. The server then sends a SEASIDE struct to the C Backend, indicating that it's looking for the bandwidth. The C Backend then replies to the server, and the server returns this information back to the web client. For more specific details on how the server works, you can read through sender_files/website/server.py. It's a pretty easy file, overall.

### Receiving Pi

The Receiving Pi has a similar structure to the Sending Pi. A C backend performs the majority of the work while a Python program handles UI from the LCD screen. The C backend handles listening for packets, calculating statistics, and responding to SEASIDE requests from UI programs.

#### C Backend

The C Backend is responsible for listening for incoming packets and keeping track of most information. First, it attempts to lock a file ('/tmp/receive_singleton'), which is used to make sure that only one instance of the program runs at a time. If it fails, it informs the user that an instance of the program is already running and exits. If successful, it proceeds to establish the IPC socket. It uses Unix sockets as IPC between itself and the UI program, bind()ing to '/tmp/receive_socket', which the UI program will connect() to. It then listens for new connections and creates a new thread to handle each new connection. That thread handles requests from the UI side for information such as the current packet or bandwidth information. Communication between the two sides is done through the SEASIDE structure. The connection-handling thread waits idly for input from the socket. On the sending side this input could include instructions on sending behavior, but on the receiving side this is only requests for information that the C program keeps track of. The C program sends back the requested information and then returns to waiting for more input. If the connection is closed gracefully by the UI program, the thread will terminate. The receiving C program currently needs some updating to be able to correctly process all of the SEASIDE flags that have been implemented on the sending side.
2.4.2. Python LCD

The Python program is in charge of UI through the LCD screen. It first locks a file ('/tmp/receive.pid') to ensure that only one instance can run at a time, then attempts to form a connection with the C program. When the connection has been established, it initializes the LCD screen and starts threads to handle displaying to the screen, updating statistics, and listening for user interaction. The main thread then listens for packet information sent by the C program. The display loop uses several multithreading-safe wrapper functions for functions in the Adafruit LCD library to ensure that screen output is handled safely. It uses information from the user interaction thread to determine which information to display, and then retrieves the appropriate screen output from a set of global variables. The statistics loop requests the majority of its information from the C program using SEASIDE and gathers the remaining information itself. The screen output is stored in a variable that can be accessed by the display thread. The user interaction loop listens for a button to be pressed on the LCD screen and then updates the global variable indicating the current screen appropriately. These threads are set up to loop infinitely, and do not return a value.The main thread listens for new packets to parse, requesting the latest packet information from the C program at a set interval using SEASIDE. Once it receives a packet, it parses it to gather information such as source addresses and payload which can be displayed on the screen if the associated button is pressed. The buttons for each screen are as follows:

UP - Summary. Contains a tally of packets received since startup and current bandwidth usage.
DOWN - Payload. Contains the payload of the last received packet, if one was included.
LEFT - Source. Contains the source MAC and IP addresses of the last received packet.
RIGHT - CPU. Contains the current CPU usage, averaged and per core.

The receiving Python program currently needs some updating to match the behavior of the sending program, mainly in proper use of SEASIDE to handle information and in format of the main thread.

### Further Development
#### Additional UIs

Currently, there are two main UIs on the Sending Pi (the webserver and the LCD screen), and one on the Receiving Pi (the LCD screen). If you were to try and implement another UI (for example, a command-line version), it would only require a few additions. We'll talk exclusively about the Sending Pi for simplicity, but if you want to implement another UI for the Receiving Pi, the process would be exactly the same.

We split up the Pi software into two logical components: The C Backend, and any other UI programs. The UI programs do not talk to each other, and are only able to talk to the C Backend through the use of the SEASIDE structure. For you to develop another UI program, it will need to be able to construct a UNIX socket (which is available in most languages out there). The C Backend should already be running at this point. After ensuring that it is running, your UI program will connect to the socket located at /tmp/send_socket (this can be changed in the #define UI_SOCKET located in send.c). You should be able to successfully connect to it if the C Backend is running.

After connecting, the C Backend will start passively listening for you to send it commands. Again, these commands must be packed into a SEASIDE structure. You should check out their structure and how to pack them.

For some commands, no response it needed, so after you send the C Backend a command, it will start listening again. However, some commands do request a response, such as GET_BANDWIDTH. If you send a SEASIDE struct with this flag, the C Backend will interpret it and send back the bandwidth it calculated over the same socket.

In summary, to fully implement another UI, all that must be done is to implement all the SEASIDE flags.

