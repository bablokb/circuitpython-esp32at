# -------------------------------------------------------------------------
# Class Server. This class tries to mimic the class mdns.Server
# of core CircuitPython.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class Server. """

import wifi
from esp32at.transport import Transport

try:
  from typing import Sequence
except ImportError:
  pass

from .remoteservice import RemoteService

try:
  from typing import Tuple
except ImportError:
  pass

class Server:
  """
  The MDNS Server responds to queries for this device’s information
  and allows for querying other devices.
  """

  def __init__(self,radio: wifi.Radio):
    """
    Constructs or returns the mdns.Server for the given
    network_interface. (CircuitPython may already be using it.) Only
    native interfaces are currently supported.
    """
    self._transport = Transport()

    # default hostname. See shared-bindings/mdns/Server.c.
    if radio.run_mode & wifi.Radio.RUN_MODE_STATION:
      mac = radio.mac_address
    else:
      mac = radio.mac_address_ap
    mac3 = ''
    for b in mac[-3:]:
      mac3 += f"{b:02x}:"
    mac3 = mac3[:-1].upper()

    self._hostname = f"cpy-{mac3}"
    self._instance_name = self._hostname

  def deinit(self) -> None:
    """ Stops the server """
    self._transport.send_atcmd("AT+MDNS=0")

  @property
  def hostname(self) -> str:
    """
    Hostname resolvable as <hostname>.local in addition to
    circuitpython.local. Make sure this is unique across all devices
    on the network. It defaults to cpy-###### where ###### is the hex
    digits of the last three bytes of the mac address.
    """
    return self._hostname

  @hostname.setter
  def hostname(self, name: str) -> None:
    """ set the hostname """
    self._hostname = name

  @property
  def instance_name(self) -> str:
    """ Human readable name to describe the device. """
    return self._instance_name

  @instance_name.setter
  def instance_name(self, name: str) -> None:
    """ set the instance name """
    self._instance_name = name

  def find(self,
           service_type: str,
           protocol: str, *,
           timeout: float = 1) -> Tuple[RemoteService]:
    """
    Find all locally available remote services with the given service
    type and protocol.

    This doesn’t allow for direct hostname lookup. To do that, use
    socketpool.SocketPool.getaddrinfo().

    Parameters:

      service_type (str) – The service type such as “_http”

      protocol (str) – The service protocol such as “_tcp”

      timeout (float/int) – Time to wait for responses
    """
    raise NotImplementedError()

  # pylint: disable=dangerous-default-value, unused-argument
  def advertise_service(self, *,
                        service_type: str,
                        protocol: str,
                        port: int,
                        txt_records: Sequence[str] = []) -> None:
    """
    Respond to queries for the given service with the given port.

    service_type and protocol can only occur on one port. Any call
    after the first will update the entry’s port.

    If web workflow is active, the port it uses can’t also be used to
    advertise a service.

    Limitations: Publishing up to 32 TXT records is only supported on
    the RP2040 Pico W board at this time.

    Parameters:

      service_type (str) – The service type such as “_http”

      protocol (str) – The service protocol such as “_tcp”

      port (int) – The port used by the service

      txt_records (Sequence[str]) – An optional sequence of strings to
      serve as TXT records along with the service
    """
    #AT+MDNS=<enable>[,<"hostname">,<"service_type">,<port>]
    #                [,<"instance">][,<"proto">][,<txt_number>]
    #                 [,<"key">,<"value">][...]

    cmd = f'AT+MDNS=1,"{self._hostname}","{service_type}",{port}'

    # this is currently only available in the master-branch:
    #cmd += f',"{self._instance_name}","{protocol}",{len(txt_records)}'
    #for i,value in enumerate(txt_records):
    #  cmd += f',"rec{i}","{value}"'

    # disable MDNS first
    try:
      self._transport.send_atcmd('AT+MDNS=0')
    except: # pylint: disable=bare-except
      pass

    try:
      self._transport.send_atcmd(cmd)
    except Exception as ex:
      raise RuntimeError("could not start mdns-advertising") from ex
