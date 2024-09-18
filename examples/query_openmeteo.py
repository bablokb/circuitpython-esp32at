# -------------------------------------------------------------------------
# query_openmeteo.py: SSL-based get requests from open-meteo.com.
#
# Note that Open-Meteo only updates data every 15 minutes. The first
# column (ts) on output is the timestamp of the data.
#
# To make this work for your location, look up longitude and latitude
# at open-meteo.com (head to "API docs") and add the values to your
# secrets.py.
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
import ssl
import adafruit_requests

import helpers

ITERATIONS = 10
INTERVAL = 60
DEBUG  = False

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- query weather-information from open-meteo.com   ------------------------

helpers.init(DEBUG)
helpers.set_tx_power()
helpers.connect()

url = "".join([
  "https://api.open-meteo.com/v1/forecast?",
  f"latitude={secrets['METEO_LATITUDE']}",
  f"&longitude={secrets['METEO_LONGITUDE']}",
  "&hourly=relativehumidity_2m,",
  "precipitation,pressure_msl,",
  "&current_weather=true",
  "&timezone=auto",
  "&forecast_days=1"
  ])

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool,ssl.create_default_context())

print('ts,T/met °C,H/met %rH,P/met hPa,WMO,Wspd km/s,Wdir °,R mm,elapsed s')
for i in range(ITERATIONS):
  try:
    start = time.monotonic()
    response = requests.get(url)
    duration = time.monotonic() - start
  except RuntimeError as e:
    print(f"request failed: {e}")
    continue

  data = response.json()
  # parse data
  t    = data["current_weather"]["temperature"]
  c    = data["current_weather"]["weathercode"]
  ws   = data["current_weather"]["windspeed"]
  wd   = data["current_weather"]["winddirection"]
  ts   = data["current_weather"]["time"]              # 2022-01-01T12:00
  hour = int(ts[11:13])
  h    = data["hourly"]["relativehumidity_2m"][hour]
  ps   = data["hourly"]["pressure_msl"][hour]
  r    = data["hourly"]["precipitation"][hour]

  # print data
  print(f"{ts},{t:0.1f},{h:0.0f},{ps:0.0f},{c:d},{ws:0.1f},{wd:0.0f},{r:0.1f},{duration:0.3f}")
  time.sleep(INTERVAL)

response.close()
