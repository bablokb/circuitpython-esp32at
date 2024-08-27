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

from .radio import _Radio
from .authmode import AuthMode
from .network import Network
from .packet import Packet
from .monitor import Monitor
from .transport import Transport

try:
  from typing import Optional
except ImportError:
  pass

transport = Transport()
radio = _Radio(transport)
at_version = None # pylint: disable=invalid-name

def init(uart: busio.UART,
         *,
         at_timeout: Optional[float] = 1,
         at_retries: Optional[int] = 1,
         rts_pin: Optional[DigitalInOut] = None,
         reset_pin: Optional[DigitalInOut] = None,
         debug: bool = False,
         ) -> None:
  """ initialize wifi-hardware (i.e. the co-processor """
  global at_version # pylint: disable=invalid-name,global-statement
  transport.init(uart,at_timeout=at_timeout, at_retries=at_retries,
                 rts_pin=rts_pin,reset_pin=reset_pin,debug=debug)
  at_version = transport.at_version # pylint: disable=invalid-name
