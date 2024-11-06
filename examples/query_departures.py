# -------------------------------------------------------------------------
# query_departures.py: SSL-based get requests from v6.db.transport.rest.
#
# This example will query departures of public transportation in Germany
# using an SSL-based get request. The server is hosted and shares the
# IP with many other servers. Therefore the client has to send the SNI
# (server name indication) in the ClientHello message.
#
# The response of the server is very large, so this program uses json_stream
# to parse the response on the fly.
#
# You can find a complete application here:
# https://github.com/bablokb/cp-departure-monitor
#
# This program needs the following libraries:
#   - adafruit_requests
#   - adafruit_connection_manager
#   - adafruit_json_stream
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
from collections import namedtuple
import adafruit_requests
import adafruit_json_stream as json_stream

import helpers

ITERATIONS = 10
INTERVAL = 60
CHUNK_SIZE = 1024
MAX_LINES  = 10
DEBUG  = False

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- trace memory   -------------------------------------------------------

def mem_free(label):
  """ print free memory """
  gc.collect()
  print(f"{label}: {gc.mem_free()}")

# --- parse iso-time   -----------------------------------------------------

def parse_time(tm):
  """ parse iso-timestamp """

  the_date, the_time = tm.split('T')
  #year,month,mday   = the_date.split('-')
  hour,minute        = the_time.split(':')[0:2]

  offset = the_time[-6:]
  sign = 1 if offset[0] == '+' else -1
  offset = sign*3600*int(offset[1:3])+sign*60*int(offset[4:])
  return [hour,minute,offset]

# --- parse data   -----------------------------------------------------------

def parse_response(resp):
  """ parse response """

  info = []
  DepInfo = namedtuple('DepInfo',
                       'plan delay line dir cancelled')
  jdata = json_stream.load(resp.iter_content(CHUNK_SIZE))

  for dep in jdata["departures"]:
    stat_name = dep["stop"]["name"]
    cancelled = dep["when"] is None
    hour,minute,offset = parse_time(dep["plannedWhen"])
    plan  = ":".join([hour,minute])
    delay = dep["delay"]
    if delay:
      delay = int(int(delay)/60)
    else:
      delay = 0
    dir  = dep["direction"]
    line = dep["line"]["name"]
    info.append(DepInfo(plan,delay,line,dir,cancelled))

  # get update-timepoint (robust code, might not exist)
  updated = jdata["realtimeDataUpdatedAt"]
  if updated:
    updated = int(updated)+offset
  mem_free("free memory after parsing response")
  return info,updated

# --- print data   -----------------------------------------------------------

def print_response(deps,updated):
  """ print (subset) of departures """

  # create template
  template  = f"{{t}}{{s}}{{d:>3.3}} {{name:<8.8}} {{dir}}"

  n_max = min(len(deps),MAX_LINES)
  print("-"*60)
  for d in deps[:n_max]:
    if d.cancelled:
      sign = ' '
      delay = 'XXX'
    elif d.delay > 0:
      sign = '+'
      delay = str(d.delay)
    elif d.delay < 0:
      sign = '-'
      delay = str(-d.delay)
    else:
      sign = ' '
      delay = ' '
    print(template.format(t=d.plan,s=sign,
                          d=delay,name=d.line,dir=d.dir))
  if n_max < len(deps):
    print(f"  ... {len(deps)-n_max} lines omitted ...")

  ts = time.localtime(updated)
  print(f"--- at: {ts.tm_hour:02}:{ts.tm_min:02}:{ts.tm_sec:02}","-"*43)

# --- query departures from v6.db.transport.rest   ------------------------

helpers.wait_for_console()
helpers.init(DEBUG)
helpers.set_tx_power()
helpers.connect()

URL_PREFIX = 'https://v6.db.transport.rest/stops'
URL_SUFFIX = 'departures?linesOfStops=false&remarks=false&pretty=false'
STATION_ID = 8005676 # Starnberg, Bavaria
DURATION   = 120     # check the next two hours

url = f"{URL_PREFIX}/{STATION_ID}/{URL_SUFFIX}&duration={DURATION}"

mem_free("free memory before session")
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool,ssl.create_default_context())
mem_free("free memory after  session")

for i in range(ITERATIONS):
  try:
    mem_free("free memory before get")
    start = time.monotonic()
    response = requests.get(url)
    send_duration = time.monotonic() - start
    print(f"send: {send_duration:0.1f}s")
    mem_free("free memory after get")
    if response.status_code != 200:
      print(f"request failed with: {response.status_code} ({str(response.reason,'utf-8')})")
      response.socket.close()
      time.sleep(INTERVAL)
      continue
  except RuntimeError as e:
    print(f"request failed with exception: {e}")
    response.socket.close()
    time.sleep(INTERVAL)
    continue

  try:
    mem_free("free memory before parse")
    start = time.monotonic()
    data, upd_time = parse_response(response)
    parse_duration = time.monotonic() - start
    print(f"parse: {parse_duration:0.1f}s")
    mem_free("free memory after parse")
    # print data
    print_response(data,upd_time)
    mem_free("free memory after print")
  except Exception as e:
    print(f"reading response failed: {e}")
  finally:
    # response.close() does not close the socket
    response.socket.close()
    mem_free("free memory after closing socket")

  # wait for next iteration
  time.sleep(INTERVAL)

print(f"program finished after {ITERATIONS} iterations!")
