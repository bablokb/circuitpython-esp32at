# -------------------------------------------------------------------------
# stream_mp3.py: stream mp3-music from an internet radio station.
#
# The program does not play the mp3-stream directly due to a limitation
# in MP3Decoder. It writes the data to an attached SD-card for later
# playback.
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

import atexit
import busio
import sdcardio
import socketpool
import ssl
import storage
import time
import wifi
import gc

import adafruit_requests

if hasattr(wifi,"at_version"):
  from esp32at.transport import Transport, PT_AUTO
import helpers
from pins import *

# local configuration
DEBUG  = False
DURATION = 60
BUF_SIZE = 1024

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
  secrets['baudrate']  = 921600            # for higher throughput
  #secrets['baudrate']  = 1500000
  secrets['uart_buffer_size'] = max(2*BUF_SIZE,16384)
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

if not PINS_SD:
  raise ValueError("PINS_SD not defined")

# --- mount SD-card   ---------------------------------------------------------

def mount_sd():
  """mount SD-sdcard"""
  spi = busio.SPI(PINS_SD[0],PINS_SD[1],PINS_SD[2])    # CLK, MOSI, MISO
  sdcard = sdcardio.SDCard(spi,PINS_SD[3],1_000_000)   # CS
  vfs    = storage.VfsFat(sdcard)
  storage.mount(vfs, "/sd")
  atexit.register(at_exit,sdcard)
  print("SD-card mounted successfully")

# --- exit processing   -------------------------------------------------------

def at_exit(sdcard):
  """ cleanup """
  print("at_exit: cleanup of sd-mount")
  storage.umount("/sd")
  sdcard.deinit()

# --- setup streaming   -------------------------------------------------------

helpers.wait_for_console()
mount_sd()
helpers.init(DEBUG)
helpers.set_tx_power()
helpers.connect()

url = secrets['mp3_url']
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool)

# dynamically create output-filename
now = time.localtime()
tstamp = (f"{now.tm_year:02d}-" +
          f"{now.tm_mon:02d}-" +
          f"{now.tm_mday:02d}_" +
          f"{now.tm_hour:02d}-" +
          f"{now.tm_min:02d}-" +
          f"{now.tm_sec:02d}")
fname = f"/sd/{tstamp}.mp3"
outfile = open(fname,"w+b")

buf = bytearray(BUF_SIZE)

print(f"downloading {DURATION}s from url: {url}")
print(f"downloading mp3 to {fname}")

#manually take care of redirects
while True:
  response = requests.get(url, allow_redirects=False)
  if 'location' in response.headers:
    url = response.headers['location']
    print(f"redirected to {url}")
    response.socket.close()
  else:
    response.socket.close()
    break

# now switch passthrough-policy
if hasattr(wifi,"at_version"):
  Transport().pt_policy = PT_AUTO

print(f"downloading {DURATION}s from (final) url: {url}")
gc.collect()
with requests.get(url, timeout=10, allow_redirects=True,
                  headers={"connection": "close"},stream=True) as response:
  print("headers:")
  for header,value in response.headers.items():
    print(f"  {header}: {value}")

  print(f"starting download via...")

  total = 0
  end = time.monotonic() + DURATION
  while time.monotonic() < end:
    try:
     count = response.socket.recv_into(buf)
     if count:
       outfile.write(buf[:count])    # don't flush: too slow
       total += count
       print(f"saved {count}/{total} bytes to {fname}")
     else:
       print("oops: no bytes received")
    except Exception as ex:
      print(f"exception during download: {ex}")
      break
    except KeyboardInterrupt:
      print("download interrupted!")
      break
  print("stopped download")
  print(f"{total} bytes written to {fname} ({8*total/1024/DURATION}kb/s)")
  response.close()

print(f"closing {fname}")
outfile.close()
