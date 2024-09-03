Implementation Notes
====================

History and Sources
-------------------

The core of the low-level AT command interface was inspired and copied from
<https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol>. That
code was initially developed for the ESP8266. The current code will
probably not work with these old devices anymore.

The AT command set does not support all features of the core wifi
API. This is not a real drawback, since depending on the platform this
is also true for native implementations. See the comments in the code
for details.

The opposite is true as well: the AT command set has additional
features that are not part of the core CircuitPython API. Some of
these features are implemented in class `Transport`, see below for
some notes.


Default DNS-Servers
-------------------

The Espressif chip uses two hardwired DNS-servers if you don't provide
explicit alternatives (208.67.222.222 and 8.8.8.8). If the DHCP-server
does not provide at least two DNS-servers, you end up using a
DNS-server you maybe don't want to use.

You can pass your own default DNS-servers to `wifi.init()`:

    wifi.init(...,ipv4_dns_defaults=["dns1","dns2"]
