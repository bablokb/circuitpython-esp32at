# -------------------------------------------------------------------------
# Class ScannedNetworks. This class tries to mimic the class wifi.ScannedNetworks
# of core CircuitPython.
#
# This class is not used by this implementation.
#
# Don't use this class directly.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class ScannedNetwork """

from . import Network

try:
  from typing import Iterator, Sequence
except ImportError:
  pass

class ScannedNetworks:
  """
  Iterates over all wifi.Network objects found while scanning. This
  object is always created by a wifi.Radio.

  Should not be instantiated directly. Use wifi.Radio.start_scanning_networks.
  """

  def __init__(self,networks: Sequence[Network]) -> None:
    self._networks = networks
    self._index = 0

  def __iter__(self) -> Iterator[Network]:
    """
    Returns itself since it is the iterator.
    """
    return self

  def __next__(self) -> Network:
    """
    Returns the next wifi.Network. Raises StopIteration if scanning is
    finished and no other results are available.
    """
    self._index += 1
    if self._index < len(self._networks):
      return self._networks[self._index]
    raise StopIteration
