# -------------------------------------------------------------------------
# Ping: testprogram for circuitpython-esp32at.
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
import ipaddress

import helpers

DEBUG  = False

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- ping host   ------------------------------------------------------------

helpers.init(DEBUG)
helpers.set_tx_power()
helpers.connect()

if 'ping_ip' in secrets:
  ip_str  = secrets['ping_ip']
else:
  ip_str = '8.8.8.8'
ping_ip = ipaddress.ip_address(ip_str)

print(f"pinging IP {ip_str} ...")
for nr in range(1,4):
  ptime = wifi.radio.ping(ping_ip)
  print(f"  {nr=}, time={ptime}ms")
  time.sleep(1)

# pinging by hostname is not part of the core API
if hasattr(wifi,"at_version"):
  if 'ping_host' in secrets:
    ping_host = secrets['ping_host']
  else:
    ping_host = 'www.circuitpython.org'

  print(f"pinging host {ping_host} ...")
  for nr in range(1,4):
    ptime = wifi.radio.ping(ping_host)
    print(f"  {nr=}, time={ptime}ms")
    time.sleep(1)
