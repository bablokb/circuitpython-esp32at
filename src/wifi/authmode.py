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

  @classmethod
  def get_modes(cls,mode: int) -> Sequence[AuthMode]:
    """ return list of modes """

    result = []
    for m in _AUTH_MAP.keys():
      if m & mode:
        result.append(_AUTH_MAP[m])
    return result

  def __repr__(self) -> str:
    """ string representation """
    return _HASH_MAP[hash(self)]

AuthMode.OPEN = AuthMode() # 1
"""Open network. No authentication required."""

AuthMode.WEP = AuthMode() # 1 << 1
"""Wired Equivalent Privacy."""

AuthMode.WPA = AuthMode() # 1 << 2
"""Wireless Protected Access."""

AuthMode.WPA2 = AuthMode() # 1 << 3
"""Wireless Protected Access 2."""

AuthMode.WPA3 = AuthMode() # 1 << 4
"""Wireless Protected Access 3."""

AuthMode.PSK = AuthMode() # 1 << 5
"""Pre-shared Key. (password)"""

AuthMode.ENTERPRISE = AuthMode() # 1 << 6
"""Each user has a unique credential."""

_AUTH_MAP = {
  1:    AuthMode.OPEN,
  1<<1: AuthMode.WEP,
  1<<2: AuthMode.WPA,
  1<<3: AuthMode.WPA2,
  1<<4: AuthMode.WPA3,
  1<<5: AuthMode.PSK,
  1<<6: AuthMode.ENTERPRISE,
  }

_HASH_MAP = {
  hash(AuthMode.OPEN): "wifi.AuthMode.OPEN",
  hash(AuthMode.WEP): "wifi.AuthMode.WEP",
  hash(AuthMode.WPA): "wifi.AuthMode.WPA",
  hash(AuthMode.WPA2): "wifi.AuthMode.WPA2",
  hash(AuthMode.WPA3): "wifi.AuthMode.WPA3",
  hash(AuthMode.PSK): "wifi.AuthMode.PSK",
  hash(AuthMode.ENTERPRISE): "wifi.AuthMode.ENTERPRISE",
  }
