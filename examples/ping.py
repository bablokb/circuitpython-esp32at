# -------------------------------------------------------------------------
# Ping: testprogram for circuitpython-esp32at.
#
# You need to create a secrets.py with at least ssid and password:
#
#   secrets = {
#     'ssid' : 'my_ssid',
#     'password' : 'my_password'
#   }
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
import ipaddress

PIN_TX = board.GP0
PIN_RX = board.GP1
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

# --- ping host   ------------------------------------------------------------

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
