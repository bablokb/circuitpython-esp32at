# -------------------------------------------------------------------------
# Class RemoteService. This class tries to mimic the class mdns.RemoteService
# of core CircuitPython.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class RemoteService. """

import ipaddress
try:
  from typing import Union
except ImportError:
  pass

class RemoteService:
  """
  Encapsulates information about a remote service that was found
  during a search. This object may only be created by a
  mdns.Server. It has no user-visible constructor.

  Cannot be instantiated directly. Use mdns.Server.find.
  """

  @property
  def hostname(self) -> str:
    """ The hostname of the device (read-only),. """
    raise NotImplementedError()

  @property
  def instance_name(self) -> str:
    """
    The human readable instance name for the service. (read-only)
    """
    raise NotImplementedError()

  @property
  def service_type(self)-> str:
    """ The service type string such as _http. (read-only) """
    raise NotImplementedError()

  @property
  def protocol(self) -> str:
    """ The protocol string such as _tcp. (read-only) """
    raise NotImplementedError()

  @property
  def port(self) -> int:
    """ Port number used for the service. (read-only) """
    raise NotImplementedError()

  @property
  def ipv4_address(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the remote service. None if no A records are found. """
    raise NotImplementedError()

  @property
  def __del__(self) -> None:
    """ Deletes the RemoteService object. """
    raise NotImplementedError()
