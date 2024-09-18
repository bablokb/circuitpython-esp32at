# -------------------------------------------------------------------------
# Template secrets.py file. Copy to secrets.py and configure as needed.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

secrets = {
  # WLAN credentials
  'ssid' : 'my_ssid',
  'password' : 'my_password',

  # transmit power
  #'tx_power': 15,

  # optional parameters for wifi.init()
  #'ipv4_dns_defaults': ['4.4.4.4', '208.67.222.222', '208.67.220.220'],
  #'country_settings': [False,'xx',1,13],
  #'at_timeout': 1,
  #'at_retries': 1,
  #'reset': False,
  #'persist_settings': True,
  #'reconn_interval': 1,
  #'multi_connection': False,
  #'baudrate': 460800,

  # settings for test_sta.py
  'hostname': 'test',
  'ipv4_address': '192.168.41.10',
  'ipv4_subnet': '255.255.255.0',
  'ipv4_gateway': '192.168.41.10',
  'dns_server': ['4.4.4.4', '208.67.222.222', '208.67.220.220'],

  # settings for other test programs
  'time_api_url': 'http://worldtimeapi.org/api/ip', # query_timeapi.py
  'udp_host': '192.168.41.20',                      # udp_logger.py
  'udp_port': 6500,                                 # udp_logger.py
  'METEO_LATITUDE': 53.1234,                        # query_openmeteo.py
  'METEO_LONGITUDE': 14.3210                        # query_openmeteo.py
  }
