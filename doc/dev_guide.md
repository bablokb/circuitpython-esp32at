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

One workaround is a hard reset of the co-processor. A second option is
to call `wifi.init()` two times. The first time with the default
initial baudrate, and if the call fails, a second time with the target
baudrate. For this to work, you should leave `reset` at its default
value of `RESET_ON_FAILURE`. See the method `init()` in
`examples/helpers.py` for some boilerplate code.


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
