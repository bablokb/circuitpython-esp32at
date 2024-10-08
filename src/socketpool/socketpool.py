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

from micropython import const

try:
  from typing import Tuple
  import circuitpython_typing
except ImportError:
  pass

import wifi
from esp32at.transport import Transport, CALLBACK_CONN, CALLBACK_IPD
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

    # keep track of connections
    self._t.set_callback(CALLBACK_CONN,self._conn_callback)
    self._t.set_callback(CALLBACK_IPD,self._ipd_callback)
    self.connections = [None]*self._t.max_connections
    self.conn_inbound = []

  def _conn_callback(self,msg):
    """ callback for connection messages """

    # check for CONNECT or CLOSED
    msg = msg.split(',')
    if len(msg) == 1:
      link_id, action = -1,msg[0]
    else:
      link_id, action = int(msg[0]),msg[1]
    if self._t.debug:
      print(f"socket: {action} for {link_id}")

    if action == 'CONNECT':
      if link_id == -1:
        sock._link_id = -1               # pylint: disable=protected-access
        if self.connections[0]:
          sock = self.connections[0]
        else:
          sock = Socket(self._socket_pool)
          self.connections[0] = sock
      else:
        sock._link_id = link_id          # pylint: disable=protected-access
        sock = Socket(self._socket_pool)
        self.connections[link_id] = sock
        self.conn_inbound.append(link_id)

    else:
      # TODO: read buffer until empty (add to close()??)
      self.connections[link_id] = None
      if link_id in self.conn_inbound:
        self.conn_inbound.remove(link_id)

  def _ipd_callback(self,msg):
    """ callback for IPD messages """
    if self._t.debug:
      print(f"socket: data-prompt: {msg}")

    # must be +IPD,<length> or +IPD,<link_id>,<length>
    msg = msg.split(',')
    if len(msg) == 2:
      link_id = 0
      data_prompt = -1,int(msg[1])
    else:
      link_id = int(msg[0])
      data_prompt = int(msg[1]),int(msg[2])
    self.connections[link_id].data_prompt = data_prompt

  # pylint: disable=redefined-builtin, unused-variable
  def socket(self,
             family: int = AF_INET,
             type: int = SOCK_STREAM,
             proto: int = IPPROTO_IP) -> circuitpython_typing.Socket:
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
    from .socket import Socket   # pylint: disable=import-outside-toplevel
    return Socket(self,family,type,proto)

  # pylint: disable=too-many-arguments, no-self-use
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
