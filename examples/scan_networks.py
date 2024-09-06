# -------------------------------------------------------------------------
# Scan available networks: testprogram for circuitpython-esp32at.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

import board
import busio
import wifi

DEBUG  = False
if board.board_id == "raspberry_pi_pico":
  PIN_TX  = board.GP0
  PIN_RX  = board.GP1
  PIN_RST = None
elif board.board_id == "challenger_rp2350_wifi6_ble5":
  PIN_TX  = board.ESP_RXD
  PIN_RX  = board.ESP_TXD
  PIN_RST = board.ESP_RESET
else:
  raise RuntimeError(f"no pin-defs for board {board.board_id}")

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  secrets = {}

# --- test if we don't have native wifi   ------------------------------------

if hasattr(wifi,"at_version"):
  uart = busio.UART(PIN_TX, PIN_RX, baudrate=115200, receiver_buffer_size=2048)
  wifi.init(uart,debug=DEBUG,reset_pin=PIN_RST)
  if not wifi.at_version:
    raise RuntimeError("could not setup co-processor")
  print(wifi.at_version)
  wifi.radio.start_station()

# --- set TX power if requested   --------------------------------------------

print(f"TX power: {wifi.radio.tx_power}")
if 'tx_power' in secrets:
  print(f"changing TX power to {secrets['tx_power']}")
  wifi.radio.tx_power = secrets['tx_power']
  print(f"TX power: {wifi.radio.tx_power}")

# --- scan network   ---------------------------------------------------------

print("Available WIFI networks:")
for n in wifi.radio.start_scanning_networks():
  print(f"  {n.ssid:<25}RSSI: {n.rssi} Channel: {n.channel}")
wifi.radio.stop_scanning_networks()
