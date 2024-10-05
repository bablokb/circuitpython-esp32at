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
import wifi
import socketpool
import adafruit_requests

import helpers

ITERATIONS = 10
INTERVAL = 100
DEBUG  = False

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- query time-information from worldtimeapi.org   -------------------------

helpers.init(DEBUG)
helpers.set_tx_power()
helpers.connect()

url = secrets['time_api_url']

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool)

for i in range(ITERATIONS):
  start = time.monotonic()
  response = requests.get(url)
  elapsed = time.monotonic()-start
  print(f"{response.json()['datetime']},{elapsed}")
  time.sleep(INTERVAL-elapsed)
response.close()
