# -------------------------------------------------------------------------
# Factory reset: reset non-volatile memory to factory defaults.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

import busio
import wifi
from pins import *

DEBUG  = False

# --- reset settings   ----------------------------------------------------

if hasattr(wifi,"at_version"):
  print("Initializing co-processor with default uart-baudrate")
  uart = busio.UART(PIN_TX, PIN_RX, baudrate=115200, receiver_buffer_size=2048)
  wifi.init(uart,debug=DEBUG,reset_pin=PIN_RST)
  if wifi.at_version:
    print(wifi.at_version)
    wifi.transport.restore_factory_settings()
  else:
    print("Factory reset failed. Please power-cycle your device and try again!")
  if PIN_RST:
    wifi.transport.hard_reset()
  print("Factory reset done. Please power-cycle your device!")
