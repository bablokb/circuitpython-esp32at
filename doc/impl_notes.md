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

MDNS service discovery is not implemented due to missing support in
the AT command set.

Web workflow is not supported, since it needs native wifi.


Streaming
---------

The AT-command interface does not allow direct access to the socket
in stream mode. But passthrough-mode allows direct access to the UART,
so reading data does no longer need individual AT-transactions. See
the [Developer's Guide](./dev_guide.md) for more details.

Direct MP3 playback of streamed data does not work. This is a
limitation of the MP3Decoder implementation.
