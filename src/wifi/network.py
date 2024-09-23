# -------------------------------------------------------------------------
# Class Network. This class tries to mimic the class wifi.Network
# of core CircuitPython.
#
# Don't use this class directly.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class Network. """

# pylint: disable=too-few-public-methods
class Network:
  """
    A wifi network provided by a nearby access point.

    You cannot create an instance of wifi.Network. They are returned
    by wifi.Radio.start_scanning_networks.
  """

  ssid: str
  """String id of the network"""

  bssid: bytes
  """BSSID of the network (usually the AP’s MAC address)"""

  rssi: int
  """Signal strength of the network"""

  channel: int
  """Channel number the network is operating on"""

  country: str
  """String id of the country code"""

  authmode: str
  """String id of the authmode"""
