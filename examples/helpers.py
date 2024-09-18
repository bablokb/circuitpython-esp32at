# -------------------------------------------------------------------------
# Shared helper-functions for all examples.
#
# You need to create a secrets.py file (have a look at sec_template.py).
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

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- initialize co-processor   ----------------------------------------------

def init(DEBUG=False,start_station=True):
  """ initialize co-processor """

  if hasattr(wifi,"at_version"):
    uart = busio.UART(PIN_TX, PIN_RX, baudrate=115200, receiver_buffer_size=2048)
    wifi.init(uart,debug=DEBUG,reset_pin=PIN_RST)
    if not wifi.at_version:
      raise RuntimeError("could not setup co-processor")
    print(wifi.at_version)
    if start_station:
      wifi.radio.start_station()

# --- set TX power if requested   --------------------------------------------

def set_tx_power():
  """ set TX power """
  if 'tx_power' in secrets:
    print(f"TX power: {wifi.radio.tx_power}")
    print(f"changing TX power to {secrets['tx_power']}")
    wifi.radio.tx_power = secrets['tx_power']
    print(f"TX power: {wifi.radio.tx_power}")

# --- connect to AP   --------------------------------------------------------

def connect():
  """ connect to AP with given ssid """

  print(f"connecting to AP {secrets['ssid']} ...")
  if 'timeout' in secrets:
    timeout = secrets['timeout']
  else:
    timeout = 5
  if 'retries' in secrets:
    retries = secrets['retries']
  else:
    retries = 3

  state = wifi.radio.connected
  print(f"  connected: {state}")
  if not state:
    # ESP32xx defaults to automatic reconnection to old AP. It will
    # disconnect first if already connected to an AP.
    #
    # Note: you can pass retries to wifi.radio.connect, but that is not portable
    for _ in range(retries):
      try:
        wifi.radio.connect(secrets['ssid'],
                           secrets['password'],
                           timeout = timeout
                           )
        break
      except ConnectionError as ex:
        print(f"{ex}")
    print(f"  connected: {wifi.radio.connected}")
