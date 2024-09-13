# -------------------------------------------------------------------------
# query_timeapi.py: simple, non-ssl get requests from worldtimeapi.org.
#
# Note that worldtimeapi.org uses rate-limiting, so don't flood them.
#
# This program needs the adafruit_requests and adafruit_connection_manager
# modules.
#
# You need to create a secrets.py file (have a look at sec_template.py).
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

import time
import board
import busio
import wifi
import socketpool
import adafruit_requests

from pins import *

ITERATIONS = 10
INTERVAL = 100
DEBUG  = False

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

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

# --- connect to AP   --------------------------------------------------------

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

# --- query time-information from worldtimeapi.org   -------------------------

url = secrets['time_api_url']

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool)

for i in range(ITERATIONS):
  response = requests.get(url)
  print(f"{response.json()['datetime']}")
  time.sleep(INTERVAL)
response.close()