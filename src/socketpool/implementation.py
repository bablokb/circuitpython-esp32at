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
from collections import namedtuple
from errno import EAGAIN
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

  @multi_connections.setter
  def multi_connections(self, flag: bool) -> None:
    """ enable/disable multi-connections """

    reply = self._t.send_atcmd(f'AT+CIPMUX={int(flag)}',filter="^OK")
    if reply is None:
      raise RuntimeError("could not set connection-mode")

  @property
  def max_connections(self) -> int:
    """ query max-connection setting """

    reply = self._t.send_atcmd('AT+CIPSERVERMAXCONN?',
                               filter="^\+CIPSERVERMAXCONN:")
    if reply is None:
      raise RuntimeError("could not query max connections")
    return int(str(reply[18:],'utf-8'))

  @max_connections.setter
  def max_connections(self, value: int) -> None:
    """ set maximum concurrent connections """

    reply = self._t.send_atcmd(
      f'AT+CIPSERVERMAXCONN={value}',filter="^OK")
    if reply is None:
      raise RuntimeError("could not set max connections")

  def get_connections(self):
    """ query connections """

    replies = self._t.send_atcmd('AT+CIPSTATE?',filter="^\+CIPSTATE:")
    if replies is None:
      return []
    if isinstance(replies,bytes):
      replies = [replies]

    connections = []
    ConnInfo = namedtuple('ConnInfo',
                          'link_id conn_type ip rport lport is_server')
    for line in replies:
      info = str(line[10:],'utf-8').split(',')
      info[0] = int(info[0])
      info[1] = info[1].strip('"')
      info[2] = info[2].strip('"')
      info[3] = int(info[3])
      info[4] = int(info[4])
      info[5] = int(info[5]) == 1
      connections.append(ConnInfo(*info))
    return connections

  def start_connection(self,host:str,port:int,conn_type: str) -> int:
    """ Start connection of the given type. Returns the link-id,
    or -1 if in single-connection mode.
    """

    # check for an existing connection
    connections = self.get_connections()
    if connections:
      if self.multi_connections:
        # check if host:port are already connected
        # which is complicated, so we leave this for later
        pass
      else:
        # for simplicity, just close the existing connection
        self.close_connection(-1)

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
    self._t.wait_for(".*SEND OK|.*SEND FAIL",timeout=5)

  # pylint: disable=no-self-use
  def send_long(self,
           buffer: circuitpython_typing.ReadableBuffer,
           link_id: int) -> int:
    """ Send long buffer """

    if link_id is None:
      raise RuntimeError("illegal state: no connection established yet")

    raise RuntimeError("not implemented yet: buffer is larger than 8192")

  def get_host_by_name(self,
                       hostname: str) -> str:
    """ return IP (as string) from hostname """

    try:
      reply = self._t.send_atcmd(
        f'AT+CIPDOMAIN="{hostname}"',filter="\+CIPDOMAIN:",timeout=5)
      return str(reply[12:-1],'utf-8')
    except:
      reply = None

  def set_timeout(self,value: int, link_id: int) -> None:
    """ set the send-timeout option """

    if link_id is None or link_id == -1:
      cmd = f"AT+CIPTCPOPT=,,{value}"
    else:
      cmd = f"AT+CIPTCPOPT={link_id},,,{value}"
    try:
      self._t.send_atcmd(cmd)
    except:
      pass

  def set_server_timeout(self,value: int) -> None:
    """ set the server-timeout option """

    try:
      self._t.send_atcmd(f"AT+CIPSTO={value}")
    except:
      pass

  @property
  def lock(self) -> bool:
    """ lock-status of AT commands (True if data is pending) """
    return self._t.lock

  @lock.setter
  def lock(self, value: bool) -> None:
    """ set lock status """
    self._t.lock = value

  def get_recv_size(self, link_id:int) -> int:
    """ return size of data available for reading """

    if link_id == -1:
      rex = ".*\+IPD,[^:]+:"
      off = 1
    else:
      rex = f".*\+IPD,{link_id},[^:]+:"
      off = 2
    info = self._t.wait_for(rex,timeout=5,greedy=False)
    self.lock = True
    info = str(info[:-1],'utf-8').split(',')
    return (int(info[off]),info[off+1].strip('"'),int(info[off+2]))

  def read(self,
           buffer: circuitpython_typing.WriteableBuffer, bufsize: int) -> int:
    """ read bufsize bytes from interface """

    # just delegate this to the transport layer
    return self._t.readinto(buffer,bufsize)

  def start_server(self, port: int, conn_type: str) -> None:
    """ start TCP/SSL server on the given port """

    reply = self._t.send_atcmd(
      f'AT+CIPSERVER=1,{port},"{conn_type}",0',filter="^OK")
    if reply is None:
      raise RuntimeError("could not start server")

  def stop_server(self) -> None:
    """ start TCP/SSL server on the given port """

    # delete server and close all connections
    try:
      reply = self._t.send_atcmd(
        'AT+CIPSERVER=0,1',filter="^OK",timeout=5)
    except Exception as ex:
      pass

  def check_for_client(self) -> int:
    """ check for a connection and return link-id """

    if not self._t.input_available:
      raise OSError(EAGAIN)
    try:
      conn = self._t.wait_for(".*,CONNECT",timeout=1,greedy=False)
      return int(str(conn,'utf-8').split(',',1)[0])
    except RuntimeError:
      raise OSError(EAGAIN)
    except ValueError as ex:
      raise RuntimeError(f"check_for_client: {conn=}")
