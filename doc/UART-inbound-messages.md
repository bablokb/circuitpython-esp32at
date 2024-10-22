AT Response Messages
--------------------

Message    Description

OK         AT command process done and return OK
ERROR      AT command error or error occurred during the execution
SEND OK    Data has been sent to the protocol stack
           (specific to AT+CIPSEND and AT+CIPSENDEX command).
           It doesn’t mean that the data has been sent to the opposite end
SEND FAIL  Error occurred during sending the data to the protocol stack
           (specific to AT+CIPSEND and AT+CIPSENDEX command
SET OK     The URL has been set successfully
           (specific to AT+HTTPURLCFG command)

+<Command Name>:...  Response to the sender that describes AT command process
                     results in details


ESP-AT Message Report (active)
------------------------------

I: ignore
S: send_atcmd
C: callback
R: read_atmsg
?: TBD
6: implement for TCPv6

Flag Message    Description

R    ready                    The ESP-AT firmware is ready
R    busy p…                  Busy processing. The system is in process of handling
                              the previous command, thus CANNOT accept the new input
?    ERR CODE:<0x%08x>        Error code for different commands
I    Will force to restart!!! Module restart right now
I    smartconfig type:<xxx>   Smartconfig type
I    Smart get wifi info      Smartconfig has got the SSID and PASSWORD information
I    +SCRD:<length>,``<reserved data>`` ESP-Touch v2 has got the reserved
                                        information
I    smartconfig connected wifi Smartconfig done. ESP-AT has connected to the Wi-Fi

C    WIFI CONNECTED           Wi-Fi station interface has connected to an AP
C    WIFI GOT IP              Wi-Fi station interface has got the IPv4 address
C6   WIFI GOT IPv6 LL         Wi-Fi station interface has got the IPv6
                              LinkLocal address
C6   WIFI GOT IPv6 GL         Wi-Fi station interface has got the IPv6
                              Global address
C    WIFI DISCONNECT          Wi-Fi station interface has disconnected from an AP
I    +ETH_CONNECTED           Ethernet interface has connected
I    +ETH_GOT_IP              Ethernet interface has got the IPv4 address
I    +ETH_DISCONNECTED        Ethernet interface has disconnected
C    [<conn_id>,]CONNECT      A network connection of which ID
                              is <conn_id> is established (ID=0 by default)
C    [<conn_id>,]CLOSED       A network connection of which ID
                              is <conn_id> ends (ID=0 by default)
I    +LINK_CONN               Detailed connection information of TCP/UDP/SSL
C    +STA_CONNECTED: <sta_mac> A station has connected to the Wi-Fi
                               softAP interface of ESP-AT
C    +DIST_STA_IP: <sta_mac>,<sta_ip>  The Wi-Fi softAP interface
                                       of ESP-AT distributes an IP address
                                       to the station
C    +STA_DISCONNECTED: <sta_mac>      A station disconnected from the Wi-Fi
                                       softAP interface of ESP-AT
R    >                        ESP-AT is waiting for more data to be received
I    Recv <xxx> bytes         ESP-AT has already received <xxx> bytes
                              from the ESP-AT command port
C    +IPD                     Data received (see manual for details)
C    SEND Canceled            Cancel to send in Wi-Fi normal sending mode
I    Have <xxx> Connections   Has reached the maximum connection counts for server
I    +QUITT                   ESP-AT quits from the Wi-Fi Passthrough Mode
I    NO CERT FOUND            No valid device certificate found in custom partition
I    NO PRVT_KEY FOUND        No valid private key found in custom partition
I    NO CA FOUND              No valid CA certificate found in custom partition
?    +TIME_UPDATED            The system time has been updated.
                              Only after sending the AT+CIPSNTPCFG
                              command or power on will this message
                              be outputted if the module fetches a
                              new time from the SNTP server.
I    +MQTT*                   all MQTT messages
I    +WS*                     all websocket messages


BLE Messages
------------

Flag Message          Description

I    +BLECONN         A Bluetooth LE connection established
I    +BLEDISCONN      A Bluetooth LE connection ends
I    +READ            A read operation from Bluetooth LE connection
I    +WRITE           A write operation from Bluetooth LE connection
I    +NOTIFY          A notification from Bluetooth LE connection
I    +INDICATE        An indication from Bluetooth LE connection
I    +BLESECNTFYKEY   Bluetooth LE SMP key
I    +BLESECREQ:<conn_index> Received encryption request which index is <conn_index>
I    +BLEAUTHCMPL:<conn_index>,<enc_result> Bluetooth LE SMP pairing completed
I    +BLUFIDATA:<len>,<data>  The ESP device received customized data from the phone over BluFi
I    +BLESCANDONE     Scan finished
I    +BLESECKEYREQ:<conn_index> The peer has accepted the pairing request,
                                and the ESP device can enter the key.
