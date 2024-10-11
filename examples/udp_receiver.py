# -------------------------------------------------------------------------
# udp_receiver: testprogram for circuitpython-esp32at.
#
# This program will listen on a port and receive UDP messages. It is
# called 'receiver' instead of 'server' because there is nothing like
# an UDP-server.
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

import helpers

DURATION = 120
TIMEOUT  = 10
DEBUG  = True

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- send some sample data to remote host   ---------------------------------

helpers.wait_for_console()
helpers.init(DEBUG)
helpers.set_tx_power()
helpers.connect()

port = secrets['udp_lport']   # local port
host = wifi.radio.ipv4_address
print(f"setting up UDP-socket on {host}:{port}")


buffer = bytearray(512)
pool   = socketpool.SocketPool(wifi.radio)
socket = pool.socket(family=socketpool.SocketPool.AF_INET,
                     type=socketpool.SocketPool.SOCK_DGRAM)
socket.bind((host,port))
socket.settimeout(TIMEOUT)

start = time.monotonic()
while time.monotonic() - start < DURATION:
  try:
    size, addr = socket.recvfrom_into(buffer)
    if size:
      #msg = buffer[:size].decode('utf-8')
      #print(f"Received {size} bytes from {addr[0]}:{addr[1]}: {msg}")
      print(f"Received {size} bytes from {addr[0]}:{addr[1]}: {buffer[:size]}")
    else:
      print(f"no data received within {TIMEOUT}s")
  except OSError:
    continue

print("closing UDP-socket and terminating program")
socket.close()
