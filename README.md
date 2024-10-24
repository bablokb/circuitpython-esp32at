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

A prerequisite for using *circuitpython-esp32at* is an ESP device
running the AT-firmware. The details are covered in the document
[Hardware and Firmware](./doc/hardware_firmware.md). The co-processor
must be connected to the MCU running CircuitPython with a dedicated
UART-connection.


Status
------

**This is the main branch, which is actively under development. The
code in this branch might or might not work.  For productive use,
switch to branch 1.1.x or use one of the published releases!**

This library is feature complete with the exceptions noted below. As
always with new projects, the code needs testing in the field to find
any remaining bugs.

From an application point of view the following features are available:

  - co-processor initialization and configuration
  - TCP (with and without SSL)
  - UDP sender (client) and receiver (aka "server")
  - HTTP requests (TCP and SSL)
  - HTTP server (TCP only)<br>
  - operate as AP

Not implemented (see also the [implementation notes](./doc/impl_notes.md):

  - web-workflow: this *requires* native wifi
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

See the [Developer's Guide](./doc/dev_guide.md) for more information
on how to use the modules. **This guide also contains a section about
troubleshooting, please read it before creating an issue.**


Roadmap
-------

  - optimize performance
  - support sleep and wakeup
  - (maybe: implement BLE)


Additional Information
----------------------

See [Implementation Notes](./doc/impl_notes.md) for technical information
regarding the interface code.
