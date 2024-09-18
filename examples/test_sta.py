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

import board
import time
import wifi
import ipaddress
import supervisor

import helpers

DEBUG = False

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- scan network   ---------------------------------------------------------

def scan():
  print("Available WIFI networks:")
  for n in wifi.radio.start_scanning_networks():
    print(f"  {n.ssid:<25}RSSI: {n.rssi} " +
          f"Channel: {n.channel:>2} Auth: {n.authmode:>08b}")
  wifi.radio.stop_scanning_networks()

# --- query station-info   ---------------------------------------------------

def mac_to_str(mac):
  if mac:
    return str(mac,'utf-8').upper()
  else:
    return ""

def get_sta_info(heading):
  # this fails for native wifi or if wifi is off
  try:
    cs = wifi.radio.country_settings
  except:
    cs = "n.a."

  try:
    li = wifi.radio.listen_interval
  except:
    li = "n.a."

  print(f"station attributes ({heading}):")
  print(f"  WIFI enabled:  {wifi.radio.enabled}")
  print(f"  connected:     {wifi.radio.connected}")
  print(f"  country:       {cs}")

  print(f"  hostname:      {wifi.radio.hostname}")
  print(f"  MAC-address:   {mac_to_str(wifi.radio.mac_address)}")
  print(f"  IPv4-Address:  {str(wifi.radio.ipv4_address)}")

  print(f"  Netmask:       {str(wifi.radio.ipv4_subnet)}")
  print(f"  Gateway:       {str(wifi.radio.ipv4_gateway)}")
  print(f"  DNS:           {str(wifi.radio.ipv4_dns)}")
  print(f"  DNS (all):     {wifi.radio.dns}")
  print(f"  listen-int.:   {li}")

# --- set hostname   ---------------------------------------------------------

def set_hostname():
  if 'hostname' in secrets:
    hostname = secrets['hostname']
    print(f"setting hostname to {hostname}")
    wifi.radio.hostname = hostname

# --- ping host   ------------------------------------------------------------

def ping():
  if 'ping_ip' in secrets:
    ip_str  = secrets['ping_ip']
  else:
    ip_str = '8.8.8.8'
  ping_ip = ipaddress.ip_address(ip_str)

  print(f"pinging IP {ip_str} ...")
  for nr in range(1,4):
    ptime = wifi.radio.ping(ping_ip)
    if ptime is None:
      result = "timed out"
    else:
      result = f"{ptime}ms"
    print(f"  {nr=}, time={result}")
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
      if ptime is None:
        result = "timed out"
      else:
        result = f"{ptime}ms"
      print(f"  {nr=}, time={result}")
      time.sleep(1)

# --- disable wifi   ---------------------------------------------------------

def disable():
  print("disabling WIFI ...")
  print(f"  WIFI state: {wifi.radio.enabled}")
  wifi.radio.enabled = False
  print(f"  WIFI state: {wifi.radio.enabled}")
  print(f"  connected: {wifi.radio.connected}")
  get_sta_info("disabled")

  print("enabling WIFI ...")
  wifi.radio.enabled = True
  print(f"  WIFI state: {wifi.radio.enabled}")
  time.sleep(5)
  print(f"  connected: {wifi.radio.connected}")
  get_sta_info("enabled")

# --- stop and restart station   ---------------------------------------------

def restart_station():
  print("stopping station ...")
  wifi.radio.stop_station()
  print(f"  WIFI state: {wifi.radio.enabled}")
  print(f"  connected: {wifi.radio.connected}")
  get_sta_info("stopped")

  time.sleep(2)
  print("starting station ...")
  wifi.radio.start_station()
  print(f"  WIFI state: {wifi.radio.enabled}")
  time.sleep(5)
  print(f"  connected: {wifi.radio.connected}")
  get_sta_info("started")

# --- set static IP addresses   ----------------------------------------------

def set_static_ip():
  if 'ipv4_address' in secrets:
    ipv4_address = ipaddress.ip_address(secrets['ipv4_address'])
    ipv4_subnet  = ipaddress.ip_address(secrets['ipv4_subnet'])
    ipv4_gateway = ipaddress.ip_address(secrets['ipv4_gateway'])
    ipv4_dns     = ipaddress.ip_address(secrets['dns_server'][0])
    print(f"setting static IP: {secrets['ipv4_address']}/{secrets['ipv4_subnet']}")
    wifi.radio.set_ipv4_address(
      ipv4     = ipv4_address,
      netmask  = ipv4_subnet,
      gateway  = ipv4_gateway,
      ipv4_dns = ipv4_dns)
    time.sleep(5)
    get_sta_info("static IP")

    # set all DNS-servers (note: this requires strings, not addresses)
    wifi.radio.dns = secrets['dns_server']
    get_sta_info("all DNS-servers")

# --- start DHCP   -----------------------------------------------------------

def start_dhcp():
  print("switching back to DHCP")
  wifi.radio.start_dhcp()
  while not wifi.radio.ipv4_address:
    time.sleep(1)
  get_sta_info("DHCP restarted")

# --- main   -----------------------------------------------------------------

# wait for serial connection
while not supervisor.runtime.serial_connected:
  time.sleep(1)    
print(f"running on board {board.board_id}")

helpers.init(DEBUG)
helpers.set_tx_power()

scan()
get_sta_info("before connect")
helpers.connect()
set_hostname()
ping()
disable()
restart_station()
set_static_ip()
start_dhcp()
