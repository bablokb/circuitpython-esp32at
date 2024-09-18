# -------------------------------------------------------------------------
# Scan available networks: testprogram for circuitpython-esp32at.
#
# You need to create a secrets.py file (have a look at sec_template.py),
# but only if you need to set TX power.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

import wifi

import helpers

DEBUG  = False

# --- scan network   ---------------------------------------------------------

helpers.init(DEBUG)
helpers.set_tx_power()

print("Available WIFI networks:")
for n in wifi.radio.start_scanning_networks():
  print(f"  {n.ssid:<25}RSSI: {n.rssi} Channel: {n.channel}")
wifi.radio.stop_scanning_networks()
