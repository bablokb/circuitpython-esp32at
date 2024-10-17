Implementation Notes
====================

History and Sources
-------------------

The core of the low-level AT command interface was inspired and copied
in parts from
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


Missing Functions
-----------------

UDP in receiver mode does not expose remote host and port, i.e.
`socket.recvfrom_into()` always returns the initial (local) host/port
configured during `socket.bind()`.

MDNS service discovery is not implemented due to missing support in
the AT command set.

Web workflow is not supported, since it needs native wifi.
