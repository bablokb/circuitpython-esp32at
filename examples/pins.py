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

# global defaults
PIN_RST = None
PINS_SD = None
PIN_RTS = None
PIN_CTS = None

# defaults for Pico-family
if 'pico' in board.board_id:
  PINS_SD = [
    board.GP10,  # CLK
    board.GP11,  # MOSI
    board.GP12,  # MISO
    board.GP9,   # CS
  ]

# use defaults, depending on board
if board.board_id == "raspberry_pi_pico":
  PIN_TX  = board.GP0
  PIN_RX  = board.GP1
elif board.board_id == "raspberry_pi_pico2":
  # Pico2 with PiCowBell (using Stemma/Qt for UART)
  PIN_TX  = board.GP4
  PIN_RX  = board.GP5
elif board.board_id == "pimoroni_pico_plus2":
  # Pico Plus 2 using SP/CE pins
  PIN_TX  = board.SPICE_SCK  # GP34
  PIN_RX  = board.SPICE_CS   # GP33
elif hasattr(board,"ESP_TX"):
  PIN_TX  = board.ESP_TX
  PIN_RX  = board.ESP_RX
  if hasattr(board,"ESP_RESET"):
    PIN_RST = board.ESP_RESET
elif hasattr(board,"TX"):
  PIN_TX  = board.TX
  PIN_RX  = board.RX

# override with values from my_pins, if available
try:
  from my_pins import *
except:
  pass
