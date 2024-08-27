# -------------------------------------------------------------------------
# Module ipaddresses. This module tries to mimic the ipaddresses-module of core
# CircuitPython.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

"""
ipaddresses - this module tries to mimic the ipaddresses-module of core
CircuitPython.
"""

try:
  from typing import Union
except ImportError:
  pass

class IPv4Address:
  """ Encapsulates an IPv4 address. """

  def __init__(self,address: Union[int, str, bytes]):
    """ Create a new IPv4Address object encapsulating the address value.

    The value itself can either be bytes or a string formatted address.
    """
    if isinstance(address,str):
      self._bytes = bytes(map(int,address.split('.')))
    elif isinstance(address,int):
      self._bytes = bytes(
        [address >> (i << 3) & 0xFF for i in range(4)[::-1]])
    else:
      self._bytes = bytes

  @property
  def packed(self) -> bytes:
    """ The bytes that make up the address (read-only). """
    return self._bytes

  @property
  def version(self) -> int:
    """ 4 for IPv4, 6 for IPv6 """
    return 4

  def as_string(self) -> str:
    """ IP as a string in dotted notation """
    return '.'.join([str(self._bytes[i]) for i in range(4)])

  def __eq__(self,other: object) -> bool:
    """ Two Address objects are equal if their addresses and address
    types are equal.
    """
    return (getattr(other,"version",0) == self.version and
            hash(self) == hash(other))

  def __hash__(self) -> int:
    """ Returns a hash for the IPv4Address data. """
    return hash(self._bytes)

def ip_address(obj: Union[int, str]) -> IPv4Address:
  """ Return a corresponding IP address object or raise ValueError if
  not possible.
  """
  return IPv4Address(obj)
