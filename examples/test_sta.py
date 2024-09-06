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
import supervisor

DEBUG = False
if board.board_id == "raspberry_pi_pico":
  PIN_TX  = board.GP0
  PIN_RX  = board.GP1
  PIN_RST = None
elif board.board_id == "challenger_rp2350_wifi6_ble5":
  PIN_TX  = board.ESP_RXD
  PIN_RX  = board.ESP_TXD
  PIN_RST = board.ESP_RESET
else:
  raise RuntimeError(f"no pin-defs for board {board.board_id}")

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- set TX power if requested   --------------------------------------------

def set_tx_power():
  print(f"TX power: {wifi.radio.tx_power}")
  if 'tx_power' in secrets:
    print(f"changing TX power to {secrets['tx_power']}")
    wifi.radio.tx_power = secrets['tx_power']
    print(f"TX power: {wifi.radio.tx_power}")

# --- scan network   ---------------------------------------------------------

def scan():
  print("Available WIFI networks:")
  for n in wifi.radio.start_scanning_networks():
    print(f"  {n.ssid:<25}RSSI: {n.rssi} " +
          f"Channel: {n.channel:>2} Auth: {n.authmode:>08b}")
  wifi.radio.stop_scanning_networks()

# --- connect to AP   --------------------------------------------------------

def connect():
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

# --- query station-info   ---------------------------------------------------

def ipv4_to_str(address):
  if address:
    return '.'.join([str(address.packed[i]) for i in range(4)])
  else:
    return ""

def mac_to_str(mac):
  if mac:
    return str(mac,'utf-8').upper()
  else:
    return ""

def get_sta_info(heading):
  print(f"station attributes ({heading}):")
  print(f"  WIFI enabled:  {wifi.radio.enabled}")
  print(f"  connected:     {wifi.radio.connected}")
  print(f"  hostname:      {wifi.radio.hostname}")
  print(f"  MAC-address:   {mac_to_str(wifi.radio.mac_address)}")
  print(f"  IPv4-Address:  {ipv4_to_str(wifi.radio.ipv4_address)}")
  print(f"  Netmask:       {ipv4_to_str(wifi.radio.ipv4_subnet)}")
  print(f"  Gateway:       {ipv4_to_str(wifi.radio.ipv4_gateway)}")
  print(f"  DNS:           {ipv4_to_str(wifi.radio.ipv4_dns)}")
  print(f"  DNS (all):     {wifi.radio.dns}")
  try:
    print(f"  listen-int.: {wifi.radio.listen_interval}")
  except Exception as ex:
    print(f"listen_interval failed: {ex}")

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

# test for esp32at-library and init co-processor
if hasattr(wifi,"at_version"):
  uart = busio.UART(PIN_TX, PIN_RX, baudrate=115200, receiver_buffer_size=2048)
  wifi.init(uart,debug=DEBUG,reset_pin=PIN_RST)
  if not wifi.at_version:
    raise RuntimeError("could not setup co-processor")
  print(wifi.at_version)
  wifi.radio.start_station()

set_tx_power()
scan()
get_sta_info("before connect")
connect()
set_hostname()
ping()
disable()
restart_station()
set_static_ip()
start_dhcp()
