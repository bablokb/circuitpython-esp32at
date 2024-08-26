# -------------------------------------------------------------------------
# Class AuthMode. This class tries to mimic the class wifi.AuthMode
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

""" class AuthMode with auth-mode constants. """

# pylint: disable=too-few-public-methods
class AuthMode:
  """ auth-mode constants """

  OPEN = 1
  """Open network. No authentication required."""

  WEP = 1 << 1
  """Wired Equivalent Privacy."""

  WPA = 1 << 2
  """Wireless Protected Access."""

  WPA2 = 1 << 3
  """Wireless Protected Access 2."""

  WPA3 = 1 << 4
  """Wireless Protected Access 3."""

  PSK = 1 << 5
  """Pre-shared Key. (password)"""

  ENTERPRISE = 1 << 6
  """Each user has a unique credential."""
