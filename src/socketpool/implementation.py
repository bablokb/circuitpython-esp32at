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
try:
  from typing import Tuple, Sequence, Union
  import circuitpython_typing
except ImportError:
  pass

import ipaddress
from esp32at.transport import Transport, CALLBACK_SEND

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
    self._ready_for_data = False
    self._send_pending = False
    self._t.set_callback(CALLBACK_SEND,self._send_callback)
    _Implementation._impl = self

  def get_connections(
    self,
    link_id = None) -> Union[namedtuple,Sequence[namedtuple]]:
    """ query connections """

    if self._t.at_version_short[0] > 2:
      cmd = "CIPSTATE"
      postfix  = "?"
      offset = 10
    else:
      cmd = "CIPSTATUS"
      postfix  = ""
      offset = 11
    replies = self._t.send_atcmd(f'AT+{cmd}{postfix}',filter=f"^\+{cmd}:")
    if replies is None:
      if link_id is None:
        return []
      return None
    if isinstance(replies,str):   # single connection returned
      replies = [replies]

    connections = []
    ConnInfo = namedtuple('ConnInfo',
                          'link_id conn_type ip rport lport is_server')
    for line in replies:
      info = line[offset:].split(',')
      info[0] = int(info[0])
      info[1] = info[1].strip('"')
      info[2] = info[2].strip('"')
      info[3] = int(info[3])
      info[4] = int(info[4])
      info[5] = int(info[5]) == 1
      if link_id is None:
        connections.append(ConnInfo(*info))
      elif link_id == info[0]:
        return ConnInfo(*info)
    return connections

  # pylint: disable=too-many-arguments
  def start_connection(self,
                       link_id: int,
                       host:str,port:int,
                       conn_type: str,
                       address: Tuple[str,int] = None) -> bool:
    """ Start connection of the given type. """

    # check for an existing connection
    # connections = self.get_connections()

    if self._t.multi_connections:
      lid_parm = f"{link_id},"
    else:
      lid_parm = ""

    # for SSL, set the SNI (server name indication). Otherwise clear it.
    reply = None
    if "SSL" in conn_type:
      try:
        _ = ipaddress.ip_address(host)   # don't set SNI for IP-address
        reply = self._t.send_atcmd(
          f'AT+CIPSSLCSNI={lid_parm}""',filter="^OK")
      except:
        reply = self._t.send_atcmd(
          f'AT+CIPSSLCSNI={lid_parm}"{host}"',filter="^OK")
    else:
      reply = self._t.send_atcmd(
        f'AT+CIPSSLCSNI={lid_parm}""',filter="^OK")
    if reply is None:
      raise RuntimeError("could not set/clear server name indication (SNI)")

    # parameters: connection-type, remote host, remote port
    params = f'{lid_parm}"{conn_type}","{host}",{port}'
    if address:
      if not "UDP" in conn_type:
        raise ValueError("address supplied and conn_type not UDP")
      # mode==2: dynamic remote host/port (address here is local!)
      #          host/port must be valid, but value is not relevant
      #          local: port,2,host (order is different than above)
      params += f',{address[1]},2,"{address[0]}"'

    # CIPSTART seems to timeout after 15s
    reply = self._t.send_atcmd(
      f'AT+CIPSTART={params}',filter="^OK")
    return not reply is None

  def close_connection(self,link_id: int) -> None:
    """ Close connection (best effort) """

    if self._t.multi_connections:
      lid_parm = f"={link_id}"
    else:
      lid_parm = ""

    try:
      self._t.send_atcmd(f"AT+CIPCLOSE{lid_parm}")
    except:
      pass

  def _send_callback(self,msg):
    """ callback for send status """
    if self._t.debug:
      print(f"implementation._send_callback(): {msg}")
    self._t.busy = False

  def send(self,
           buffer: circuitpython_typing.ReadableBuffer,
           link_id: int) -> None:
    """ Send up to 8192 bytes """

    if self._t.passthrough:
      self._t.write(buffer)
      return

    if link_id is None:
      raise RuntimeError("illegal state: no connection established yet")

    if len(buffer) > 8192:
      self.send_long(buffer,link_id)
      return

    if self._t.multi_connections:
      lid_parm = f"{link_id},"
    else:
      lid_parm = ""

    cmd = f"AT+CIPSEND={lid_parm}{len(buffer)}"

    reply = self._t.send_atcmd(cmd,set_busy=True)     # init send
    if "ERROR" in reply:                              # link_id could be closed
      if self._t.debug:
        print(f"send failed with ERROR for {link_id}")
      self._t.busy = False
      raise OSError(f"send failed for {link_id}")
    success, _ = self._t.read_atmsg(passive=True,read_until='>')
    if success:
      self._t.write(buffer)                             # write data to uart
    else:
      raise OSError(f"send failed with ERROR for {link_id}")

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
        f'AT+CIPDOMAIN="{hostname}"',filter="\+CIPDOMAIN:")
      return reply[12:-1]
    except:
      return None

  def set_timeout(self,value: int, link_id: int) -> None:
    """ set the send-timeout option """

    if self._t.multi_connections:
      lid_parm = f"{link_id},"
    else:
      lid_parm = ""

    try:
      self._t.send_atcmd(f"AT+CIPTCPOPT={lid_parm},,{value}")
    except:
      pass

  def set_server_timeout(self,value: int) -> None:
    """ set the server-timeout option """

    try:
      self._t.send_atcmd(f"AT+CIPSTO={value}")
    except:
      pass

  def recv_data(self,
                buffer: circuitpython_typing.WriteableBuffer, bufsize: int,
                link_id: int) -> int:
    """ read pending data """

    if self._t.multi_connections:
      lid_parm = f"{link_id},"
    else:
      lid_parm = ""

    # request data: AT sends CIPRECVDATA with length and data
    cmd = f"AT+CIPRECVDATA={lid_parm}{bufsize}"
    result = self._t.send_atcmd(cmd,read_until="+CIPRECVDATA:")
    if result != "+CIPRECVDATA:":
      raise RuntimeError("failed reading data")

    # read actual length from interface
    # we expect length,"ip",port,data
    txt = b""
    commas = 0
    while True:
      c = self._t.read(1) # pylint: disable=invalid-name
      if c == b',':
        if commas == 2: # we already have two, this is our third comma
          break
        commas += 1
      txt += c
    act_len,host,port = str(txt,'utf-8').split(",")
    act_len = int(act_len)
    host = host.strip('"')
    port = int(port)
    return self.read(buffer,act_len),host,port

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
