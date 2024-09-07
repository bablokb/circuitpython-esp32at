# -------------------------------------------------------------------------
# udp_logger: testprogram for circuitpython-esp32at.
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
import microcontroller

ITERATIONS = 100
DEBUG  = False

if board.board_id == "raspberry_pi_pico":
  PIN_TX  = board.GP0
  PIN_RX  = board.GP1
  PIN_RST = None
elif board.board_id == "challenger_rp2350_wifi6_ble5":
  PIN_TX  = board.ESP_RXD
  PIN_RX  = board.ESP_TXD
  PIN_RST = board.ESP_RESET
else:
  print(f"no pin-defs for board {board.board_id}")

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

# --- send some sample data to remote host   ---------------------------------

host = secrets['udp_host']
port = secrets['udp_port']
print(f"setting up UDP-socket for target {host}:{port}")

pool   = socketpool.SocketPool(wifi.radio)
socket = pool.socket(family=socketpool.SocketPool.AF_INET,
                     type=socketpool.SocketPool.SOCK_DGRAM)

loop_start = time.monotonic()
for _ in range(ITERATIONS):
  ts = time.monotonic()
  cputemp = microcontroller.cpu.temperature
  data = f"{ts:6.4f},{cputemp:.1f}\n"
  start = time.monotonic()
  socket.sendto(data.encode('utf-8'),(host,port))
  tx_time = time.monotonic()-start
  print(f"transmitted '{data[:-1]}' in {tx_time:0.3f}s")
loop_end = time.monotonic()

socket.close()
print(f"time pro iteration: {(loop_end-loop_start)/ITERATIONS:0.2f}s")
