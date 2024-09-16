circuitpython-esp32at
=====================

**This is work in progress and only partially usable yet!**

This is an implementation of a CircuitPython core-API compatible
wifi-interface to ESP32C3/ESP32C6 co-processors using AT Commands. It
is meant as a drop-in for CircuitPython builds without native wifi
support (btw: a Pico with C3 will do better than a Pico-W, since the
network stack on the Pico-W will use up a large amount of the
available memory).

It provides the following modules:

  - `esp32at`
  - `ipaddress`
  - `socketpool`
  - `ssl`
  - `wifi`

Currently, you have to install these modules manually, i.e. copy
the respective folders to your device.

**Do not install the modules from this repository if you are using a
CircuitPython build that has native wifi support.**


Status
------

Implemented features:

  - co-processor initialization
  - network scanning (`wifi.radio.start_scanning_networks()`)
  - connecting (`wifi.radio.connect()` and `wifi.radio.connected`)
  - pinging (`wifi.radio.ping()`)
  - all `wifi.radio` station-methods and properties
  - modules `ipaddress`, `ssl`
  - `socketpool.SocketPool` (including DNS-lookup)
  - `socket.connect()`, `socket.close()`, `socket.sendto()`
  - UDP client working
  - HTTP get requests (TCP and SSL) working
  - HTTP server (TCP) working (not tested with multiple concurrent clients)

See also examples and test-programs in the `examples`-folder.

Roadmap:

  - implement `ssl` and `socketpool`: full TCP/IP client functions
    available
  - implement `wifi.radio` AP-methods
  - optimize performance


Required Hardware
-----------------

Tested with the following boards:

  - Pico and [Adafruit Qt-Py ESP32C3](https://www.adafruit.com/product/5405)<br>
    Nice and small.
  - [Adafruit Itsy-Bitsy M4 Express](https://www.adafruit.com/product/3800) and ESP32C3-Super-Mini<br>
    The Super-Mini is probably the cheapest solution available.
  - Pico and [Lilygo T-01 C3](https://www.lilygo.cc/products/t-01c3)<br>
    A minimalistic C3-board. Same footprint as the famous ESP-01S board.
    Because the standard AT-command port pins are not available, this
    boards needs a special, self-compiled AT-firmware.
  - [Challenger+RP2350 Wifi6/BLE5](https://ilabs.se/challenger-rp2350-wifi-ble/)<br>
    Feather-sized, integrated solution.

The Challenger has an integrated ESP32C6 and the AT firmware is
already installed. For the other boards, you need to download and
flash the official AT firmware provided by Espressif, see
<https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/index.html>.

The MCU running CircuitPython needs an UART-connection with the ESP32Cx
co-processor. The Espressif documentation has detailed instructions
for flashing the firmware and setting up the hardware connection.

Note that both the Qt-Py ESP32C3 as well as the ESP32C3-Super-Mini have
badly designed on-board antennas. If they don't connect to your AP, try
reducing the TX power.


Software
--------

The aim is that the modules from this repo will implement the
communication with the co-processor in a transparent way for the
developer. Besides the initialization of the UART connection, no
special code (compared to a native wifi implementation) should be
necessary:

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

    # use the normal core API

The `wifi`-module in this repo is a superset of the core wifi-API. The sample
code above tests for the `at_version` attribute, which is not available in
the core API so this code-snippet will also work with native wifi.

For normal use, there is no need to use any of the additional methods
of this module (besides `wifi.init()`). In fact, you should not use
these methods to stay portable with your code.

The initialization routine `wifi.init()` has a number of parameters. See
the [Implementation Notes](./impl_notes.md) for details on how to tweak
the setup.

Experts can use `wifi.transport` to directly access the co-processor
with special AT-commands.


Additional Information
----------------------

See [Implementation Notes](./impl_notes.md) for technical information
regarding the interface code.
