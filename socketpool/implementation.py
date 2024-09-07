# -------------------------------------------------------------------------
# Class _Implementation. Low-level helper-functions for SocketPool and Socket.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class Implementation. """

import time
try:
  from typing import Tuple
  import circuitpython_typing
except ImportError:
  pass

from esp32at.transport import Transport

# pylint: disable=anomalous-backslash-in-string,bare-except
class _Implementation:
  """ Low-level helpers for SocketPool and Socket """

  _impl = None
  """ The singleton instance """

  def __new__(cls):
    if _Implementation._impl:
      return _Implementation._impl
    return super(_Implementation,cls).__new__(cls)

  def __init__(self) -> None:
    """ Constructor """
    self._t = Transport()  # get transport-singleton

  @property
  def multi_connections(self) -> bool:
    """ query multi-connection setting """

    reply = self._t.send_atcmd('AT+CIPMUX?',filter="^\+CIPMUX:")
    if reply is None:
      raise RuntimeError("could not query connection-mode")
    return str(reply[8:],'utf-8') == "1"

  def start_connection(self,host:str,port:int,conn_type: str) -> int:
    """ Start connection of the given type. Returns the link-id,
    or -1 if in single-connection mode.
    """

    if self.multi_connections:
      cmd = "CIPSTARTEX"
    else:
      cmd = "CIPSTART"

    # TODO: don't hardcode timeout
    reply = self._t.send_atcmd(
      f'AT+{cmd}="{conn_type}","{host}",{port}',filter="CONNECT",
        timeout=5)
    if reply is None:
      raise RuntimeError("could not start connection")
    if b',' in reply:
      return int(str(reply,'utf-8').split(',',1)[0])
    return -1

  def close_connection(self,link_id: int) -> None:
    """ Close connection (best effort) """

    if link_id is None or link_id == -1:
      cmd = "AT+CIPCLOSE"
    else:
      cmd = f"AT+CIPCLOSE={link_id}"
    try:
      # TODO: don't hardcode timeout
      self._t.send_atcmd(cmd,timeout=5)
    except:
      pass

  def send(self,
           buffer: circuitpython_typing.ReadableBuffer,
           link_id: int) -> None:
    """ Send up to 8192 bytes """

    if link_id is None:
      raise RuntimeError("illegal state: no connection established yet")

    if len(buffer) > 8192:
      self.send_long(buffer,link_id)
      return

    if link_id == -1:
      cmd = f"AT+CIPSEND={len(buffer)}"
    else:
      cmd = f"AT+CIPSEND={link_id},{len(buffer)}"

    # TODO: check for connect
    self._t.send_atcmd(cmd)
    self._t.wait_for(".*>",timeout=5)
    self._t.write(buffer)
    self._t.wait_for(".*SEND OK|.*ERROR",timeout=5)

  # pylint: disable=no-self-use
  def send_long(self,
           buffer: circuitpython_typing.ReadableBuffer,
           link_id: int) -> int:
    """ Send long buffer """

    if link_id is None:
      raise RuntimeError("illegal state: no connection established yet")

    raise RuntimeError("not implemented yet: buffer is larger than 8192")
