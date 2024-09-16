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


Initialization
--------------

Before use, the interface to the co-processor has to be initialized.
Therefore, the very first statement to execute is `wifi.init()`.

The method has a number of parameters. Most of them are optional, but
for optimal setup they can be tweaked:

  - `uart`: The `busio.UART`-object used for communication. Needs to
    be setup with baudrate=115200.
  - `at_timeout`: The global default timeout for a response to an AT
    command. The default value of `1` should be ok.
  - `at_retries`: Retries for failing AT commands. Available for
    historical reasons and currently with default `1`.
  - `reset`: Send the reset command to the co-processor during init.
    If `reset_pin` is defined, also execute a hard reset.
  - `reset_pin`: GPIO (`microcontroller.Pin`) connected to
    RESET of the ESP32Cx.
  - `persist_settings`: If `True` (default), settings are saved to
    non-volatile storage of the ESP32Cx. See the AT User's Guide for
    a list of relevant settings. See also the discussion below.
  - `reconn_interval`: Value of the (automatic) reconnection interval. A
    value of zero disables automatic reconnection.
  - `multi_connection`: Support multiple parallel connections. Default is
    `False`. Support is implemented, but absolutely untested. The default
    AT firmware allows up to five parallel connections.
  - `baudrate`: temporarely set a different baudrate than the default
    value of 115200. **TO BE IMPLMENTED**.
  - `debug`: If `True`, traces AT requests and responses. Defaults to `False`.
  - `ipv4_dns_defaults`: see section below
  - `country_settings`: see section below


Persistent Settings
-------------------

The default AT firmware saves a number of settings automatically to
non-volatile storage. Most prominent examples are WLAN credentials or things
like station-mode vs. AP-mode. The advantage of this procedure is that
you don't have to provide credentials in your program once the device is
set up. The drawback is that after a power-on-reset the device is not
in a reproducible state.

To prevent storing settings, you can pass the parameter
`persist_settings=False` to `wifi.init()`.


Automatic Connects
------------------

The default behavior of the firmware is to automatically reconnect to the
same AP as the last time. This works only if settings are stored *and*
the `reconn_interval`-parameter from `wifi.init()` is not zero.


Default DNS-Servers
-------------------

The Espressif chip uses two hardwired DNS-servers if you don't provide
explicit alternatives (208.67.222.222 and 8.8.8.8). If the DHCP-server
does not provide at least two DNS-servers, you end up using a
DNS-server you maybe don't want to use.

You can pass your own default DNS-servers to `wifi.init()`:

    wifi.init(...,ipv4_dns_defaults=["dns1","dns2"],...)


Country Specific Settings
-------------------------

The parameter `country_settings` control the country/region specific
settings of the wifi-radio. You can set four parameters:

  - `ignore_ap`: if False, use the settings from the AP
  - `country`: country-code
  - `start_channel`: first valid channel
  - `n_channels`: number of channels

To configure the settings, pass in a list with four values. The default
value is `[False,None,None,None]`: this will configure all values from
the AP once the device is connected.

If the device should run as AP, make sure to configure all values according
to the relevant local laws.
