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

  # pylint: disable=too-many-arguments
  def start_connection(self,host:str,port:int,
                       conn_type: str,
                       timeout: int,
                       address: Tuple[str,int] = None) -> int:
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

    # parameters: connection-type, remote host, remote port
    params = f'"{conn_type}","{host}",{port}'
    if address:
      if not "UDP" in conn_type:
        raise ValueError("address supplied and conn_type not UDP")
      # mode==2: dynamic remote host/port (address here is local!)
      #          host/port must be valid, but value is not relevant
      #          local: port,2,host (order is different than above)
      params += f',{address[1]},2,"{address[0]}"'

    reply = self._t.send_atcmd(
      f'AT+{cmd}={params}',filter="([0-9],)?CONNECT",timeout=timeout)
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

  # pylint: disable=no-self-use, unused-argument
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
      return None

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

  def get_recv_size(self, link_id:int, timeout: float) -> int:
    """ return size of data available for reading """

    if timeout is None:
      # we don't want to wait for ever...
      timeout = 60
    if link_id == -1:
      rex = ".*\+IPD,[^:]+:"
      off = 1
    else:
      rex = f".*\+IPD,{link_id},[^:]+:"
      off = 2
    info = self._t.wait_for(rex,timeout=timeout,greedy=False)
    self.lock = True
    info = str(info[:-1],'utf-8').split(',') # remove trailing ':' and split
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
      self._t.send_atcmd('AT+CIPSERVER=0,1',filter="^OK",timeout=5)
    except:
      pass

  def check_for_client(self,check_ipd: bool = False) -> int:
    """ check for a connection and return link-id """

    if not self._t.input_available:
      raise OSError(EAGAIN)
    try:
      # sometimes there is a second connect before the IPD
      if check_ipd:
        rex = ".*\+IPD,([0-9],)?[^:]+:|.*,CONNECT"
        info = self._t.wait_for(rex,timeout=1,greedy=False)
        if b"CONNECT" in info:
          # a second connect, return link_id,None
          return int(str(info,'utf-8').split(',',1)[0]),None
        # else: an IPD message
        self.lock = True
        info = str(info[:-1],'utf-8').split(',') # remove trailing ':' and split
        # return link_id,(size,host,port)
        if len(info) == 5:
          # with link_id
          return int(info[1]),(int(info[2]),info[3].strip('"'),int(info[4]))
        # else: # without link_id
        return -1,(int(info[1]),info[2].strip('"'),int(info[3]))

      # else: only check for a CONNECT
      rex = ".*,CONNECT"
      conn = self._t.wait_for(rex,timeout=1,greedy=False)
      link_id = int(str(conn,'utf-8').split(',',1)[0])
      return link_id,None
    except RuntimeError:
      raise OSError(EAGAIN) # pylint: disable=raise-missing-from
    except ValueError as ex:
      raise RuntimeError(f"check_for_client: {conn=}") from ex
