# -------------------------------------------------------------------------
# udp_client: testprogram for circuitpython-esp32at.
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
import microcontroller

import helpers

ITERATIONS = 100
DEBUG  = False

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

host = secrets['udp_host']
port = secrets['udp_port']
print(f"setting up UDP-socket for target {host}:{port}")

pool   = socketpool.SocketPool(wifi.radio)
socket = pool.socket(family=socketpool.SocketPool.AF_INET,
                     type=socketpool.SocketPool.SOCK_DGRAM)

for i in range(ITERATIONS):
  if i == 1:
    # i==0: the very first sendto will also connect and therefore takes longer
    loop_start = time.monotonic()
  ts = time.monotonic()
  cputemp = microcontroller.cpu.temperature
  data = f"{ts:6.4f},{cputemp:.1f}\n"
  start = time.monotonic()
  socket.sendto(data.encode('utf-8'),(host,port))
  tx_time = time.monotonic()-start
  print(f"transmitted '{data[:-1]}' in {tx_time:0.3f}s")
loop_end = time.monotonic()

socket.close()
print(f"time per iteration: {(loop_end-loop_start)/(ITERATIONS-1):0.3f}s")
