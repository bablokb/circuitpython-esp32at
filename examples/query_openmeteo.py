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
import gc
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

helpers.wait_for_console()
helpers.init(DEBUG)
helpers.set_tx_power()
helpers.connect()

url = "".join([
  "https://api.open-meteo.com/v1/forecast?",
  f"latitude={secrets['METEO_LATITUDE']}",
  f"&longitude={secrets['METEO_LONGITUDE']}",
  "&hourly=relativehumidity_2m,",
  "precipitation,",
  "pressure_msl",
  "&current=temperature_2m,",
  "precipitation,",
  "weather_code,",
  "wind_speed_10m,",
  "wind_direction_10m",
  "&timezone=auto",
  "&forecast_days=1"
  ])

if DEBUG:
  print(f"{url=}")

print(f"free memory before session: {gc.mem_free()}")
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool,ssl.create_default_context())
print(f"free memory after  session: {gc.mem_free()}")

print('\nts,T/met °C,H/met %rH,P/met hPa,WMO,Wspd km/s,Wdir °,R mm,send s,recv s,memfree')
for i in range(ITERATIONS):
  try:
    start = time.monotonic()
    response = requests.get(url,timeout=5)
    memfree = gc.mem_free()
    send_duration = time.monotonic() - start
  except RuntimeError as e:
    print(f"request failed: {e}")
    continue

  start = time.monotonic()
  data = response.json()
  recv_duration = time.monotonic() - start
  # parse data
  t    = data["current"]["temperature_2m"]
  c    = data["current"]["weather_code"]
  ws   = data["current"]["wind_speed_10m"]
  wd   = data["current"]["wind_direction_10m"]
  ts   = data["current"]["time"]              # 2022-01-01T12:00
  hour = int(ts[11:13])
  h    = data["hourly"]["relativehumidity_2m"][hour]
  ps   = data["hourly"]["pressure_msl"][hour]
  r    = data["hourly"]["precipitation"][hour]

  # print data
  print(f"{ts},{t:0.1f},{h:0.0f},{ps:0.0f},{c:d},{ws:0.1f},{wd:0.0f},{r:0.1f},{send_duration:0.3f},{recv_duration:0.3f},{memfree}")

  response.socket.close()
  elapsed = time.monotonic()-start
  if i < ITERATIONS-1:
    time.sleep(max(0,INTERVAL-elapsed))
