# -------------------------------------------------------------------------
# Class Packet. This class tries to mimic the class wifi.Packet
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

""" class Packet wrapping the packet parameters. """

# pylint: disable=too-few-public-methods
class Packet:
  """The packet parameters."""

  CH: object # pylint: disable=invalid-name
  """The packet’s channel."""

  LEN: object
  """The packet’s length."""

  RAW: object
  """The packet’s payload."""

  RSSI: object
  """The packet’s rssi."""
