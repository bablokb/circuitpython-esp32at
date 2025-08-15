# -------------------------------------------------------------------------
# iperf3_client.py: Test performance with iperf3.
#
# This program needs the iperf-module from
# https://github.com/bablokb/circuitpython-iperf
#
# You need to create a secrets.py file (have a look at sec_template.py).
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

import iperf
import helpers

DEBUG       = False
ITERATIONS  = 3
INTERVAL    = 5
UDP         = False          # iperf -u|--udp: use UDP transfers
REVERSE     = False          # iperf -R|--reverse: host is sending
LENGTH      = 4096           # iperf -l|--length: length of buffer
TTIME       = 10             # iperf -t|--time: transmit-time

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- main   ------------------------------------------------------------------

helpers.wait_for_console()
helpers.init(DEBUG)
helpers.set_tx_power()
helpers.connect()

hostname = secrets['iperf3_hostname']

for i in range(ITERATIONS):
  iperf.client(hostname,debug=DEBUG,
               udp=UDP,reverse=REVERSE,length=LENGTH,ttime=TTIME)
  time.sleep(INTERVAL)
