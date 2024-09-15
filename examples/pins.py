# -------------------------------------------------------------------------
# pins.py: default pins used from the test programs.
#
# Instead of changing this file, create a file 'my_pins.py' instead.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

import board

# use defaults, depending on board
if board.board_id == "raspberry_pi_pico":
  PIN_TX  = board.GP0
  PIN_RX  = board.GP1
  PIN_RST = None
elif board.board_id == "challenger_rp2350_wifi6_ble5":
  PIN_TX  = board.ESP_TX
  PIN_RX  = board.ESP_RX
  PIN_RST = board.ESP_RESET
elif hasattr(board,"TX"):
  PIN_TX  = board.TX
  PIN_RX  = board.RX
  PIN_RST = None

# override with values from my_pins, if available
try:
  from my_pins import *
except:
  pass
