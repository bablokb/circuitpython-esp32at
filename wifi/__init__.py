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

from .radio import Radio
from .authmode import AuthMode
from .network import Network
from .packet import Packet
from .monitor import Monitor
from esp32at.transport import Transport

try:
  from typing import Optional
except ImportError:
  pass

transport = Transport()
radio = Radio(transport)
at_version = None # pylint: disable=invalid-name

def init(uart: busio.UART,
         *,
         ipv4_dns_defaults: Optional[Sequence[str]] = [],
         **kwargs,
         ) -> None:
  """ initialize wifi-hardware (i.e. the co-processor """
  global at_version, radio # pylint: disable=invalid-name,global-statement

  if len(ipv4_dns_defaults):
    radio.ipv4_dns_defaults = ipv4_dns_defaults
  transport.init(uart,**kwargs)
  at_version = transport.at_version # pylint: disable=invalid-name
