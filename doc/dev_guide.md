Developer's Guide
=================

Overview
--------

All modules (except `esp32at`) are drop-in replacements of the core
wifi modules from CircuitPython. These are only available on builds
that support wifi, i.e. for boards with an integrated modem. By
keeping the drop-in modules compatible to the core-modules, only a
minimum of special code is necessary to use the replacements.

The modules from this repo implement the communication with the
co-processor in a transparent way for the developer. Besides the
initialization of the UART connection, no special code (compared to a
native wifi implementation) should be necessary:

    import board
    import busio
    import wifi
    
    PIN_TX = board.GP0
    PIN_RX = board.GP1
    DEBUG  = False
    
    if hasattr(wifi,"at_version"):
      uart = busio.UART(PIN_TX, 
                        PIN_RX, baudrate=115200, receiver_buffer_size=2048)
      wifi.init(uart,debug=DEBUG)
      if wifi.at_version:
        print(f"AT version: {wifi.at_version}")
        wifi.radio.start_station()

    # from here on, use the normal core API

The `wifi`-module in this repo is a superset of the core wifi-API. The
sample code above tests if the `at_version` attribute exists before
using it. This will make this code run on native wifi builds as well
as systems using the modules from here.

Note that `wifi.radio` is a singleton, there is no need to pass it
around and it does not matter where you initialize it.

For normal use, there is no need to use any of the superset methods
of this module (besides `wifi.init()`). In fact, you should not use
these methods to stay portable with your code.

The initialization routine `wifi.init()` has a number of
parameters. See the section below for details on how to tweak the
setup.

Experts can use `wifi.transport` to directly access the co-processor
with special AT-commands.


Initialization
--------------

Before use, the interface to the co-processor has to be initialized.
Therefore, the very first statement to execute is `wifi.init()`.

The method has a number of parameters. Most of them are optional, but
for optimal setup they can be tweaked:

  - `uart`: The `busio.UART`-object used for communication. Needs
    an initial baudrate of 115200.
  - `at_retries`: Retries for failing AT commands (failing in the sense
    that not even ERROR is returned). Default: `1`.
  - `reset`: see section below.
  - `hard_reset`: see section below.
  - `reset_pin`: GPIO (`microcontroller.Pin`) connected to
    RESET of the ESP32Cx.
  - `persist_settings`: If `True` (default), settings are saved to
    non-volatile storage of the ESP32Cx. See the AT User's Guide for
    a list of relevant settings. See also the discussion below.
  - `reconn_interval`: Value of the (automatic) reconnection interval. A
    value of zero disables automatic reconnection.
  - `baudrate`: change baudrate temporarily. Format:
     `baudrate` or `"baudrate[,databits,stopbits,parity,flow-control]"`.
     The first alternative does not change any the remaining options.
  - `pt_policy`: Set passthrough-policy. One of
    `[transport.PT_OFF, transport.PT_AUTO, transport.PT_MANUAL]`. Defaults
     to `transport.PT_OFF`. See section below for details.
    `True`. The default AT firmware allows up to five parallel connections.
  - `debug`: If `True`, traces AT requests and responses. Defaults to `False`.
  - `ipv4_dns_defaults`: see section below
  - `country_settings`: see section below


Resets
------

A reset is possible using the singleton `Transport`-object:

    import wifi
    wifi.init(...)
    t = wifi.transport
    t.soft_reset()
    t.hard_reset()

A soft reset is only possible if the communication with the
co-processor is working. A hard reset needs a physical connection
(reset-pin) to reset the device.

During initialization, you can request an automatic reset:

    from esp32at.transport import RESET_NEVER, RESET_ON_FAILURE, RESET_ALWAYS
    wifi.init(...,reset=RESET_ON_FAILURE, hard_reset=RESET_NEVER,...)

The defaults (`reset=RESET_ON_FAILURE` and `hard_reset=RESET_NEVER`) are
the recommended settings.


Baudrate
--------

The initial baudrate is `115200`. You can change this value from
`wifi.init()`, or set it any time using `wifi.transport.baudrate =
...`. Both ways this will change the UART-baudrate, and the configuration
of the co-processor. This setting does not persist. The AT commandset
*does* support changing the baudrate permanently, but this is not
supported since this is a perfect way to shoot yourself in the foot.

Changing the baudrate can cause problems during development. If you
restart the program from the REPL (or with a reset button), the
co-processor usually does not reset and still expects the changed
baudrate.

The best solution is to register an `at_exit()`-method that resests
the co-processor to the default baudrate:

    import atexit
    ...
    def reset_uart():
      from esp32at.transport import Transport
      print("running at_exit() to reset co-processor to default state")
      t = Transport()
      if t.baudrate != 115200:
        t.baudrate = 115200
    ...
    atexit.register(reset_uart)

Another workaround is a hard reset of the co-processor. A third
option is to call `wifi.init()` two times. The first time with the
default initial baudrate, and if the call fails, a second time with
the target baudrate. For this to work, you should leave `reset` at its
default value of `RESET_ON_FAILURE`. See the method `init()` in
One workaround is a hard reset of the co-processor. A second option is
to call `wifi.init()` two times. The first time with the default
initial baudrate, and if the call fails, a second time with the target
baudrate. For this to work, you should leave `reset` at its default
value of `RESET_ON_FAILURE`. See the method `init()` in
 `examples/helpers.py` for some boilerplate code.


Multi-Connections Mode
----------------------

In the default setup, the ESP-AT firmware supports five concurrent
connections.  This library uses multi-connections mode as the
default. Single connection mode has no advantage during normal
operation.

There is one exception: "passthrough-mode" is only available in single
connection mode. The library automatically switches to single
connection mode if the passthrough-policy is `PT_AUTO` or `PT_MANUAL`.


Passthrough-Mode and Passthrough-Policy
---------------------------------------

**Passthrough-Mode is highly experimental. It seems that this mode
results in corrupted data. This is in clarification with Espressif.**

The AT-firmware allows to transparently link the underlying UART to a
socket once a connection is established. This is called "passthrough
mode".  This mode is more efficient because sending and receiving data
does not need AT-command transactions anymore. The drawback is that
this mode only works with a single connection thus this mode is not
suitable if running as a server. But many client-applications only
connect to one server at a time, so passthrough mode is a valid option
for clients.

For short-lived connections passthrough mode has some overhead. Mainly
switching back to normal mode takes more than one second. In addition
detecting a socket closed by the server takes the full timeout set for
the socket. But for persistent connections or for connections that
transfer a lot of data the application will benefit from passthrough
mode. A prominent example is streaming of data.

To use passthrough mode, either call `wifi.init()` with the keyword
parameter `pt_policy=transport.PT_AUTO` or with
`pt_policy=transport.PT_MANUAL`. With the first option the library
will automatically switch to passthrough mode after connecting to a
remote host and will stop passthrough mode once the socket is closed
again. With `PT_MANUAL` the application program must switch manually,
e.g.

    from esp32at.transport import Transport
    ...
    # connect to AP and remote host
    ...
    t = Transport()
    t.passthrough = True
    ...
    t.passthrough = False

While passthrough mode is active, no other API-call to the library
that uses the AT-firmware is possible. This implies that redirects
(HTTP-302) won't work in passthrough mode. The workaround is to handle
redirects manually until the final URL is available (no
'Location'-field in the HTTP-headers) and then switch manually to
passthrough mode. See [stream.py](../examples/stream.py) for an example
implementation.


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

The program `examples/factory_reset.py` will reset all saved settings to
factory defaults.


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


Compiling your own Firmware
---------------------------

A detailed [Firmware Compile Guide](./at_firmware_compile.md) is
available (use the [ESP-01S Firmware Compile
Guide](./at_firmware_compile_esp01s.md) in case you are running an old
ESP8266).

Building a firmware is a matter of about a quarter of an hour. This
is mainly necessary if you want to increase the number of parallel
connections supported by your device. Which in turn is relevant if
you run the device as a server and serve complex websites.


Troubleshooting
---------------

Make sure your co-processor is working correctly. Some of the cheap
Chinese dev-boards have bad antennas and the WLAN connection isn't
stable. This will result in various errors that the library cannot
deal with so it will throw a `RuntimeError`. Also, always check your
cabling. Check that RX/TX are connected correctly and that there is
no physical connection problem. 

First thing to try in case of problems is to power cycle the host MCU
and the co-processor. This can be necessary when switching between
station mode and AP mode or between client and server setups.

Secondly, try to run with default settings. Especially the reset
configuration should be at it's defaults. Also, the baudrate should not
be changed. Ideally, you would run `examples/factory_reset.py` to
reinitialize all settings stored in non-volatile memory.

If this does not help, initialize the co-processor with
`debug=True`. This creates a lot of output but will give important
hints if there is a bug in the communication between host and
co-processor. In case the problem persists, open an issue in the repo
providing the trace-output and as much information as possible. A
simple program reproducing the problem will certainly help to track
down the issue.

**Note that the trace-output will also contain credentials, be sure to
remove them before posting!**
