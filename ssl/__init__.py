# -------------------------------------------------------------------------
# Module ssl. This module tries to mimic the ssl-module of core
# CircuitPython.
#
# Since all connections including SSL are handled by the co-processer,
# this module won't do a lot.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

"""
ssl - this module tries to mimic the ssl-module of core
CircuitPython.
"""

from .sslcontext import SSLContext
from .sslsocket  import SSLSocket

def create_default_context() -> SSLContext:
  """ Return the default SSLContext. """
  return None
