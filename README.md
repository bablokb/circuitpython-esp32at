circuitpython-esp32at
=====================

**This is work in progress, fairly complete but not fully tested yet!**

This is an implementation of a CircuitPython core-API compatible
wifi-interface to ESP32C3/ESP32C6 co-processors using AT Commands. It
is meant as a drop-in for CircuitPython builds without native wifi
support.

It provides the following modules:

  - `esp32at`
  - `ipaddress`
  - `mdns`
  - `socketpool`
  - `ssl`
  - `wifi`

The rationale for this project is to transparently support a
co-processor for non-wifi enabled boards, mainly RP2040/RP2350, but
any other board with enough RAM should work as well (the SAMD21 does
not have enough memory, but the SAMD51 works fine).

One major difference with using a co-processor is that the TCP/IP and
SSL-stacks don't use up large amounts of memory in the MCU RAM. The
Pico-W for example can either do networking, or update a display, but
not both (with the exception of trivial examples). In contrast, the
Pico together with an ESP32C3 will work fine.


Status
------

Implemented features:

  - co-processor initialization
  - all modules: `ipaddress`, `wifi`,`ipaddress`, `ssl`, `socketpool`
    (except `socketpool.socket.recvfrom_into` and  `socketpool.socket.sendall`)

From an application point of view:

  - TCP (with and without SSL) and UDP client
  - HTTP requests (TCP and SSL)
  - HTTP server (TCP only)<br>
    (currently untested with multiple concurrent clients)

Not implemented:

  - `wifi.radio.stations_ap`: no support from AT commandset
  - MDNS-service discovery: no support from AT commandset
  - UDP server: planned, needs `socketpool.socket.recvfrom_into`
  - TCP-server with SSL: needs indiviual firmware because of certificates
  - MP3 streaming: currently unsupported from core CircuitPython

See also examples and test-programs in the `examples`-folder.


Installation
------------

Currently, you have to install these modules manually, i.e. copy
the respective folders to your device.

**Do not install the modules from this repository if you are using a
CircuitPython build that has native wifi support.**


Roadmap
-------

  - implement remaining `socketpool.socket`-methods
  - optimize performance


Hardware
--------

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
