# -------------------------------------------------------------------------
# Module mdns. This module tries to mimic the mdns-module of core
# CircuitPython.
#
# Limitation: the AT commandset does not support discovery.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

"""
mdns - this module tries to mimic the mdns-module of core
CircuitPython.

Limitation: the AT commandset does not support discovery.
"""

from .server import Server
from .remoteservice import RemoteService
