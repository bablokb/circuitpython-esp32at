# -------------------------------------------------------------------------
# ap_webserver.py: setup an AP and run a simple http-server.
#
# This program needs the ehttpserver module (available via circup).
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
secrets = helpers.secrets

DEBUG  = False
INTERVAL = 10  # for list of connected stations

# --- run server   -----------------------------------------------------------

helpers.wait_for_console()
helpers.init(DEBUG,start_station=False)
helpers.set_tx_power()

import gc
import wifi
import mdns
import socketpool

from ehttpserver import Server, Response, route

class MyServer(Server):

  # --- request-handler for /   -----------------------------------------------

  @route("/","GET")
  def _handle_main(self,path,query_params, headers, body):
    """ handle request for main-page """
    return Response("<b>Hello, world!</b>", content_type="text/html")

  # --- run AP   -------------------------------------------------------------

  def start_ap(self):
    """ start AP-mode """

    print("stopping station")
    wifi.radio.stop_station()
    print("starting AP")
    wifi.radio.start_ap(ssid=secrets["ap_ssid"],
                        password=secrets["ap_password"],
                        authmode=[wifi.AuthMode.PSK,wifi.AuthMode.WPA2])

  # --- run server   ---------------------------------------------------------

  def run_server(self):

    server = mdns.Server(wifi.radio)
    server.hostname = secrets["ap_hostname"]
    server.advertise_service(service_type="_http",
                             protocol="_tcp", port=80)
    pool = socketpool.SocketPool(wifi.radio)
    print(f"starting {server.hostname}.local ({wifi.radio.ipv4_address_ap})")
    with pool.socket() as server_socket:
      yield from self.start(server_socket)

# --- some helper functions   ------------------------------------------------

def mac_to_str(mac):
  if mac:
    result = ""
    for b in mac:
      result += f"{b:02x}:"
    return result[:-1].upper()
  else:
    return ""

# minimal implementation of asyncio.sleep() as a generator
def asyncio_sleep(seconds):
  start_time = time.monotonic()
  while time.monotonic() - start_time < seconds:
    yield

# list stations connected to AP
def print_stations():
  while True:
    stations = wifi.radio.stations_ap
    if stations:
      print("connected stations:")
      for station in stations:
        print(f"{mac_to_str(station.mac_address)}: {station.ipv4_address}")
    yield from asyncio_sleep(INTERVAL)

# --- main   -----------------------------------------------------------------

myserver = MyServer()
myserver.start_ap()
print(f"Listening on http://{wifi.radio.ipv4_address_ap}:80")

for _ in zip(print_stations(),myserver.run_server()):
  pass
