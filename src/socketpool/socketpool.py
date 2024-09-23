# -------------------------------------------------------------------------
# Class SocketPool. This class tries to mimic the class socketpool.SocketPool
# of core CircuitPython.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class SocketPool. """

import errno
import time
import gc
from micropython import const

try:
  from typing import Tuple
except ImportError:
  pass

import wifi
from .implementation import _Implementation

class SocketPool:
  """ SocketPool class for ESP32Cx AT commandset """

  # all constants from shared-bindings/socketpool/enum.h
  SOCK_STREAM = const(1)
  SOCK_DGRAM = const(2)
  SOCK_RAW = const(3)

  AF_INET = const(2)
  AF_INET6 = const(10)

  IPPROTO_IP = const(0)
  IPPROTO_ICMP = const(1)
  IPPROTO_TCP = const(6)
  IPPROTO_UDP = const(17)
  IPPROTO_IPV6 = const(41)
  IPPROTO_RAW = const(255)

  TCP_NODELAY = const(1)

  SOL_SOCKET = const(0xfff)

  SO_REUSEADDR = const(0x0004)

  IP_MULTICAST_TTL = const(5)

  EAI_NONAME = const(-2)

  NO_SOCKET_AVAIL = const(255)

  _socketpool = None
  """ The singleton instance """

  # pylint: disable=unused-argument
  def __new__(cls, radio: wifi.radio):
    if SocketPool._socketpool:
      return SocketPool._socketpool
    return super(SocketPool,cls).__new__(cls)

  def __init__(self, radio: wifi.radio) -> None:
    """ Constructor """
    self._radio = radio

  # pylint: disable=redefined-builtin
  def socket(self,
             family: int = AF_INET,
             type: int = SOCK_STREAM,
             proto: int = IPPROTO_IP) -> Socket:
    """
    Create a new socket and return it

    Parameters:

      family (int) – AF_INET or AF_INET6
      type (int) – SOCK_STREAM, SOCK_DGRAM or SOCK_RAW
      proto (int) – IPPROTO_IP, IPPROTO_ICMP, IPPROTO_TCP,
      IPPROTO_UDP, IPPROTO_IPV6or IPPROTO_RAW. Only works with
      SOCK_RAW

    The fileno argument available in socket.socket() in CPython is not supported.
    """
    from .socket import Socket
    return Socket(self,family,type,proto)

  # pylint: disable=too-many-arguments
  def getaddrinfo(self,
                  host: str,
                  port: int,
                  family: int = 0,
                  socktype: int = 0,
                  proto: int = 0,
                  flags: int = 0) -> Tuple[int, int, int, str, Tuple[str, int]]:
    """
    Gets the address information for a hostname and port

    Returns the appropriate family, socket type, socket protocol and
    address information to call socket.socket() and socket.connect()
    with, as a tuple.
    """

    if not isinstance(port, int):
      raise ValueError("Port must be an integer")
    if not family:
      family = SocketPool.AF_INET

    ipaddr = _Implementation().get_host_by_name(host)
    return [(family, socktype, proto, "", (ipaddr, port))]
