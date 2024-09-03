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

PIN_TX = board.GP0
PIN_RX = board.GP1
DEBUG  = False

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  secrets = {}

# --- test if we don't have native wifi   ------------------------------------

if hasattr(wifi,"at_version"):
  uart = busio.UART(PIN_TX, PIN_RX, baudrate=115200, receiver_buffer_size=2048)
  wifi.init(uart,debug=DEBUG,at_timeout=0.5)
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
