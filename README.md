circuitpython-esp32at
=====================

**This is work in progress and not usable yet!**

This is an implementation of a CircuitPython core-API compatible
wifi-interface to ESP32C3/ESP32C6 co-processors using AT Commands.

It provides the following modules:

  - `wifi`
  - `ipaddress`
  - `socketpool`
  - `ssl (??)`

**Do not install the modules from this repository if you are using a
CircuitPython build that has native wifi support.**


Status
------

Implement features:

  - co-processor initialization
  - `wifi.tx_power` (getter and setter)
  - `wifi.connect()` and `wifi.connected`
  - module `ipaddress` (not tested yet)


Required Hardware
-----------------

The code has been tested with an ESP32C3 Qtpy and
ESP32C3-Super-Mini. You need to install the official AT firmware
provided by Espressif, see
<https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/index.html>. It
should also work with the ESP32C6 and possibly other ESP32 as well.

The MCU running CircuitPython needs an UART-connection with the ESP32
co-processor. The Espressif documentation has detailed instructions
for flashing the firmware and setting up the hardware connection.


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
      print(f"AT version: {wifi.at_version}")

    # use the normal core API

The `wifi`-module in this repo is a superset of the core wifi-API. The sample
code above tests for the `at_version` attribute, which is not available in
the core API so this code-snippet will also work with native wifi.

For normal use, there is no need to use any of the additional methods
of this module (besides `wifi.init()`). In fact, you should not use
these methods to stay portable with your code.

Experts can use `wifi.transport` to directly access the co-processor
with special AT-commands.


Implementation Notes
--------------------

Most of the low-level AT command code was inspired and copied from
<https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol>. That
code was initially developed for the ESP8266. The current code will
probably not work with these old devices anymore.

The AT command set does not support all features of the core wifi
API. This is not a real drawback, since depending on the platform this
is also true for native implementations. See the comments in the code
for details.