Support Hardware and Firmware
=============================

Espressif maintains their ESP-AT project currently for a number of
hardware platforms, mainly ESP32C2, ESP32C3, ESP32C6, and
ESP32. Support for older hardware (ESP8266) is very limited and
the available firmware source is only maintained up to version
2.2.x.x. Pre-built firmware is also not available. As a consequence,
not every platform is recommended.


Hardware Overview
-----------------

  - ESP32C3: **Fully supported, highly recommended, first choice**.<br>
    Boards with an ESP32C3 are small and cost-efficient and widely available.
  - ESP32C6: **Fully supported, recommended, second choice**.<br>
    Bigger and not as cost-efficient as ESP32C3 boards, but they
    support WIFI6.
  - ESP32: **Fully supported, not recommended**.<br>
    ESP32 based boards are usually larger and more expensive than ESP32C3 boards.
  - ESP-01S: **Partly supported, not recommended**<br>
    These are very cheap and small boards, but they only support the operation
    as a TCP/SSL/UDP client. Also, you have to build your own firmware
    (see [ESP-01S Firmware Compile Guide](./at_firmware_compile_esp01s.md))


Firmware
--------

Official, released firmware is available from
<https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/Get_Started/Downloading_guide.html> (replace the 'esp32c3' in the link with your platform).
You can also go to the 'Releases' page of the Espressif ESP-AT project:
<https://github.com/espressif/esp-at/releases>.

The downloaded zip-file has a folder called "factory", and in this
folder is a combined binary firmware that has to be flashed to address 0x0.

Flashing the firmware is a one-time task and documented in
<https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/Get_Started/Downloading_guide.html#flash-at-firmware-into-your-device>.


The modules of this repository have been tested with the following
firmware versions:

  - v3.3.0.0 (ESP32C3)
  - v3.4.0.0 (ESP32C6)
  - v4.0.0.0 (ESP32C6)
  - v2.2.2.0 (ESP8266)

Old versions (1.x.x, often pre-installed on ESP8266-devices) will
definitely not work.

Starting with v3.3.0.0, there are no major relevant differences
between the firmware versions. The master branch (currently post
4.0.0.0) did add some new functions regarding MDNS
service-announcement. This will be implemented as soon there is an
officially released version available.

The downladed factory firmware can be changed with the [at.py
utility](https://github.com/espressif/esp-at/blob/master/tools/at.py)
provided by Espressif. This is useful for changing settings like the
default pins or the country code used by the firmware. You will find
some examples in the board specific notes below.

As an alternative, you can compile your own firmware using the
[Firmware Compile Guide](./at_firmware_compile.md).


Board-specific Notes
====================

The boards below have all been tested. This does not imply that other
boards don't work.


Qt-Py ESP32C3
-------------

This product from Adafruit (shop:
[Adafruit Qt-Py ESP32C3](https://www.adafruit.com/product/5405)) is
small and works with the stock ESP32C3 firmware (select the 'MINI-1'
variant).

![](./esp32c3-qtpy.jpg)

Pins:

  - RX: GPIO6 (labeled 'SCL')
  - TX: GPIO7 (labeled 'MO')
  - RST: n.a.

If this board does not connect to your AP, try reducing the TX power.

To connect the board using the Stemma/Qt connector, you have to modify
the firmware to use RX:GPI05 and TX:GPIO6:

    at.py modify_bin -tx 6 -rx 5 --cts_pin -1 --rts_pin -1 \
            -in ESP32C3-AT-Factory-Firmware-v3.3.0.0.bin \
            -o  ESP32C3-AT-Qtpy-Stemma-Firmware-v3.3.0.0.bin

This command takes the factory-firmware as input and creates a modified
firmware as output.


ESP32C3-SuperMini
-----------------

The Super-Mini is probably the cheapest solution available. The problem
is the quality of the antenna. Some boards work perfectly fine, others
have problems connecting. Sometimes reducing the TX power helps.

![](./esp32c3-supermini.jpg)

The boards work down to 3.3V, so they can be operated and powered by
the 3V3 pin of the MCU (unless some other power hungry devices are
connected).

Pins:

  - RX: GPIO6 (labeled '6')
  - TX: GPIO7 (labeled '7')
  - RST: n.a.

A small support PCB from <https://github.com/bablokb/pcb-esp32c3-adapter>
allows to connect to the SuperMini using a Stemma/Qt-cable. The power pin
of the Stemma/Qt is connected to 3V3 but a jumper on the back allows
switching this to the 5V pin.

![](./esp32c3-adapter.png)

Since many boards allow to connect various peripherals to their pins,
the host MCU could also use Stemma if changing pin functions is possible.
The Pico together with a PiCowbell is an example. The standard I2C
pins of this interface (GP4 and GP5) can be repurposed as UART and
the SuperMini can then be connected using a simple Stemma/Qt cable.

![](./picowbell+adapter.jpg)


Lilygo T-01 C3
--------------

The [Lilygo T-01 C3](https://www.lilygo.cc/products/t-01c3) is a
minimalistic C3-board. It has the same footprint and pinout as the
famous ESP-01S board.

![](./lilygo-t01-c3.jpg)

The device needs stable 3.3V. Otherwise, it works just fine and is the
best choice.

Pins (2x4 header):

  - RX: GPIO20 (labeled 'RXD', pin 4)
  - TX: GPIO21 (labeled 'TXD', pin 5)
  - RST: pin 7

Because the standard AT-command port pins are not available on the
device, some changes are necessary using the at.py utility:

    at.py modify_bin -un 0 -cc DE -tx 21 -rx 20 --cts_pin -1 --rts_pin -1 \
             -in ESP32C3-AT-Factory-Firmware-v3.3.0.0.bin \
             -o  lilygo-t01c3-at-firmware-3.3.1.0.bin

This command changes the AT-UART from UART1 to UART0 (using `-un 0`,
the country code (using `-cc DE`), and the RX/TX pins to
GPIO20/GPIO21.


Challenger+RP2350 Wifi6/BLE5
----------------------------

This is a Feather-sized, integrated solution with an ESP32C6, see
[Challenger+RP2350
Wifi6/BLE5](https://ilabs.se/challenger-rp2350-wifi-ble/).  Due to the
integration no extra cables are necessary. Highly recommended!

![](./challenger+rp2350_wifi.jpg)

The Challenger has 8MB PSRAM and 8MB flash. The AT firmware for the
ESP32C6 is already installed.

For TX, RX and RST the `board`-module defines suitable pins:

  - RX:  `board.ESP_RX`
  - TX:  `board.ESP_TX`
  - RST: `board.ESP_RESET`


ESP32C6-Mini
------------

This is a minimal C6-board similar to the ESP32C3-SuperMini. It is
less common, a bit larger, and suffers from the same
quality-problems. Since it is also more expensive than the SuperMini
there is no reason to use this board unless you need WIFI6.

![](./esp32c6-mini.jpg)

The board works with the standard factory firmware.

Pins:

  - RX: GPIO6 (labeled '6')
  - TX: GPIO7 (labeled '7')
  - RST: n.a.


MuseLab Nano-ESP32-C6
---------------------

[This
board](https://github.com/wuxx/nanoESP32-C6/blob/master/README_en.md)
is very large (despite the fact that it is called "nano") and
available with different flash-sizes. The board works fine but is not
recommended due to it's size.

![](./esp32c6-nano.jpg)

Pins:

  - RX: GPIO6 (labeled '6')
  - TX: GPIO7 (labeled '7')
  - RST: pin 3 on header left of ESP-chip


DFRobot Fire-Beetle ESP32-D-V4.0
--------------------------------

[The Fire-Beetle](https://wiki.dfrobot.com/FireBeetle_ESP32_IOT_Microcontroller(V3.0)__Supports_Wi-Fi_&_Bluetooth__SKU__DFR0478) uses an ESP32-WROOM-ESP32D.

As a co-processor this board is oversized and overequipped (16MB of flash).
It works fine with the factory firmware for the ESP32-WROOM-32.

![](./esp32-wroom-32d.jpg)

Pins:

  - RX: GPI16 (labeled 'DI/IO16')
  - TX: GPI17 (labeled 'LRCK/IO17')
  - RST: pin 1 on header left of the Micro-USB socket (ESP32-chip facing down)


ESP-01S
-------

A very common, but old board based on the ESP8266. Since it only supports
client operations, it is not really recommended. But it will work fine
for these use cases. Otherwise, replace the ESP-01S with the compatible Lilygo
T-01-C3.

![](./esp01s.jpg)

(in the image you can see the [Maker Pi Pico
Board](https://www.cytron.io/c-development-tools/c-maker-series/p-maker-pi-pico-simplifying-raspberry-pi-pico-for-beginners-and-kits)
from Cytron, which has a socket made for the ESP-01S - very nice!).

The big advantage of this board is it's very low price and the small
form-factor.

Espressif does not release a pre-built firmware for 8266-devices
anymore, so you have to build your own firmware. See [ESP-01S
Firmware Compile Guide](./at_firmware_compile_esp01s.md) for details.
