circuitpython-esp32at
=====================

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

This library is feature complete with the exceptions noted below. As
always with new projects, the code needs testing in the field to find
any remaining bugs.

From an application point of view the following features are available:

  - co-processor initialization and configuration
  - TCP (with and without SSL)
  - UDP sender (client) and receiver (aka "server")
  - HTTP requests (TCP and SSL)
  - HTTP server (TCP only)<br>
    (**note**: *multiple concurrent connections are broken*)
  - operate as AP

Not implemented:

  - `wifi.radio.stations_ap`: no support from AT commandset
  - MDNS-service discovery: no support from AT commandset
  - TCP-server with SSL: needs indiviual firmware because of certificates
  - MP3 streaming: currently unsupported from core CircuitPython

See also the [examples and test-programs](./examples/README.md) in the
`examples`-folder.


Installation
------------

Currently, you have to install these modules manually, i.e. copy
all folders below `src` to your device.

**Do not install the modules from this repository if you are using a
CircuitPython build that has native wifi support.** (it actually does not
hurt, but these modules will not be used).

See the [Developer's Guide](./doc/dev_guide.md) for more information on
how to use the modules.


Roadmap
-------

  - partial redesign to support concurrent connections
  - optimize performance
  - support sleep and wakeup
  - document building (specialized versions of) the AT-firmware
  - (maybe: implement BLE)


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



Additional Information
----------------------

See [Implementation Notes](./doc/impl_notes.md) for technical information
regarding the interface code.
