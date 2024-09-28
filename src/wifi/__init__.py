# -------------------------------------------------------------------------
# Module wifi. This module tries to mimic the wifi-module of core
# CircuitPython.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

"""
wifi - this module tries to mimic the wifi-module of core
CircuitPython.
"""

import busio
from digitalio import Direction, DigitalInOut

from esp32at.transport import Transport
from .radio import Radio
from .authmode import AuthMode
from .network import Network
from .packet import Packet
from .monitor import Monitor

try:
  from typing import Optional, Sequence
except ImportError:
  pass

transport = Transport()
radio = Radio(transport)
at_version = None # pylint: disable=invalid-name

# pylint: disable=dangerous-default-value
def init(uart: busio.UART,
         *,
         ipv4_dns_defaults: Optional[Sequence[str]] = [],
         country_settings: Optional = [0,None,None,None],
         **kwargs,
         ) -> bool:
  """ initialize wifi-hardware (i.e. the co-processor """
  global at_version # pylint: disable=invalid-name,global-statement

  rc = transport.init(uart,**kwargs) # pylint: disable=invalid-name
  if rc:
    at_version = transport.at_version # pylint: disable=invalid-name
    if ipv4_dns_defaults:
      radio.ipv4_dns_defaults = ipv4_dns_defaults
    radio.country_settings = country_settings
  return rc
