# -------------------------------------------------------------------------
# Class _Radio. This class tries to mimic the class wifi.Radio
# of core CircuitPython.
#
# Don't use this class directly, use wifi.radio instead.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class _Radio. """

try:
  from typing import Union, Sequence, Iterable
  import circuitpython_typing
except ImportError:
  pass

import ipaddress
from .network import Network
from .authmode import AuthMode
from .transport import Transport

# pylint: disable=too-many-public-methods,unused-argument,no-self-use
class _Radio:
  """
  Native wifi radio.

  This class manages the station and access point functionality
  of the native Wifi radio.
  """

  radio = None
  """ the singleton instance"""

  def __init__(self,transport: Transport) -> None:
    """ Constructor. """
    if _Radio.radio:
      return
    self._transport = transport
    self._enabled = False
    self._hostname = ""
    self._tx_power = 0
    self._mac_address = None
    self._mac_address_ap = None
    self._listen_interval = 100
    _Radio.radio = self

  @property
  def enabled(self) -> bool:
    """
    True when the wifi radio is enabled.
    If you set the value to False, any open sockets will be closed.
    """
    return self._enabled

  @enabled.setter
  def enabled(self, value: bool) -> None:
    """Change the enabled status"""
    self._enabled = value

  @property
  def hostname(self) -> str:
    """ return the hostname from the wifi interface """
    return self._hostname

  @property
  def mac_address(self) -> circuitpython_typing.ReadableBuffer:
    """ MAC address for the station."""
    return self._mac_address

  @property
  def tx_power(self) -> float:
    """ Wifi transmission power, in dBm. """
    replies = self._transport.send_atcmd(
      "AT+RFPOWER?",timeout=0.5).split(b"\r\n")
    for reply in replies:
      if reply.startswith(b"+RFPOWER:"):
        return int(str(reply[9:],'utf-8').split(',')[0])*0.25
    raise RuntimeError("Bad response to RFPOWER?")

  @tx_power.setter
  def tx_power(self,value: int) -> None:
    """ Change tx_power """
    wifi_power = min(80,value*4)
    self._transport.send_atcmd(f"AT+RFPOWER={wifi_power}",timeout=0.5)

  @property
  def listen_interval(self) -> int:
    """Wifi power save listen interval, in DTIM periods,
    or 100ms intervals if TWT is supported.
    """
    return self._listen_interval

  @property
  def mac_address_ap(self) -> circuitpython_typing.ReadableBuffer:
    """ MAC address for the AP."""
    return self._mac_address_ap

  def start_scanning_networks(
    self,*, start_channel: int = 1,
    stop_channel: int = 11) -> Iterable[Network]:
    """Scans for available wifi networks over the given channel range.
    Make sure the channels are allowed in your country.
    """
    return []

  def stop_scanning_networks(self) -> None:
    """Stop scanning for Wifi networks and free any resources used to do it."""
    return

  def start_station(self) -> None:
    """Starts a Station."""
    return

  def stop_station(self) -> None:
    """Stopts the Station."""
    return

  def start_ap(
    self,
    ssid: Union[str, circuitpython_typing.ReadableBuffer],
    password: Union[str, circuitpython_typing.ReadableBuffer] = b'',
    *, channel: int = 1,
    authmode: Iterable[AuthMode] = (),
    max_connections: Union[int, None] = 4) -> None:
    """
    Starts running an access point with the specified ssid and password.

    If channel is given, the access point will use that channel
    unless a station is already operating on a different channel.

    If authmode is not None, the access point will use the given
    authentication modes. If a non-empty password is given, authmode
    must not include OPEN. If authmode is not given or is an empty
    iterable, (wifi.AuthMode.OPEN,) will be used when the password is
    the empty string, otherwise authmode will be (wifi.AuthMode.WPA,
    wifi.AuthMode.WPA2, wifi.AuthMode.PSK).

    Limitations: On Espressif, authmode with a non-empty password must
    include wifi.AuthMode.PSK, and one or both of wifi.AuthMode.WPA
    and wifi.AuthMode.WPA2.  The length of password must be 8-63
    characters if it is ASCII, or exactly 64 hexadecimal characters if
    it is the hex form of the 256-bit key.

    If max_connections is given, the access point will allow up to
    that number of stations to connect.
    """
    return

  def stop_ap(self) -> None:
    """Stops the access point."""
    return

  @property
  def ap_active(self) -> bool:
    """True if running as an access point. (read-only)"""
    return False

  def connect(
    self,
    ssid: Union[str, circuitpython_typing.ReadableBuffer],
    password: Union[str, circuitpython_typing.ReadableBuffer] = b'',
    *,
    channel: int = 0,
    bssid: Union[str, circuitpython_typing.ReadableBuffer, None] = None,
    timeout: Union[float, None] = None) -> None:

    """
    Connects to the given ssid and waits for an ip
    address. Reconnections are handled automatically once one
    connection succeeds.

    The length of password must be 0 if there is no password, 8-63
    characters if it is ASCII, or exactly 64 hexadecimal characters if
    it is the hex form of the 256-bit key.

    By default, this will scan all channels and connect to the access
    point (AP) with the given ssid and greatest signal strength
    (rssi).

    If channel is non-zero, the scan will begin with the given channel
    and connect to the first AP with the given ssid. This can speed up
    the connection time significantly because a full scan doesn’t
    occur.

    If bssid is given and not None, the scan will start at the first
    channel or the one given and connect to the AP with the given
    bssid and ssid.
    """
    return

  @property
  def connected(self) -> bool:
    """ True if connected to an access point (read-only). """
    return False

  @property
  def ipv4_gateway(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the station gateway when connected to an
    access point. None otherwise. (read-only) """
    return None

  @property
  def ipv4_gateway_ap(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the access point gateway, when enabled. None
    otherwise. (read-only)"""
    return None

  @property
  def ipv4_subnet(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the station subnet when connected to an
    access point. None otherwise. (read-only) """
    return None

  @property
  def ipv4_subnet_ap(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the access point subnet, when enabled. None
    otherwise. (read-only) """
    return None

  @property
  def ipv4_address(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the station when connected to an access
    point. None otherwise. (read-only)
    """
    return None

  @ipv4_address.setter
  def ipv4_address(
    self,*,
    ipv4: ipaddress.IPv4Address,
    netmask: ipaddress.IPv4Address,
    gateway: ipaddress.IPv4Address,
    ipv4_dns: Union[ipaddress.IPv4Address, None]) -> None:
    """ Sets the IP v4 address of the station. Must include the
    netmask and gateway. DNS address is optional. Setting the address
    manually will stop the DHCP client.

    Note

    In the raspberrypi port (RP2040 CYW43), the access point needs to
    be started before the IP v4 address can be set.
    """
    return

  @property
  def addresses(self) -> Sequence[str]:
    """ Address(es) of the station when connected to an access
    point. Empty sequence when not connected. (read-only)
    """
    return []

  @property
  def ipv4_address_ap(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the access point, when enabled. None
    otherwise. (read-only)
    """
    return None

  @ipv4_address_ap.setter
  def ipv4_address_ap(
    self, *,
    ipv4: ipaddress.IPv4Address,
    netmask: ipaddress.IPv4Address,
    gateway: ipaddress.IPv4Address) -> None:
    """ Sets the IP v4 address of the access point. Must include the
    netmask and gateway.
    """

  @property
  def addresses_ap(self) -> Sequence[str]:
    """ Address(es) of the access point when enabled. Empty sequence
    when disabled. (read-only)
    """
    return []

  @property
  def ipv4_dns(self) -> ipaddress.IPv4Address:
    """ IP v4 Address of the DNS server to be used. """
    return None

  @ipv4_dns.setter
  def ipv4_dns(self,value: ipaddress.IPv4Address) -> None:
    """ IP v4 Address of the DNS server to be used. """
    return None

  @property
  def dns(self) -> Sequence[str]:
    """ Addresses of the DNS server to be used. """
    return []

  @dns.setter
  def dns(self,addresses: Sequence[str]) -> None:
    """ Addresses of the DNS server to be used. """
    return None

  @property
  def ap_info(self) -> Union[Network, None]:
    """ Network object containing BSSID, SSID, authmode, channel,
    country and RSSI when connected to an access point. None
    otherwise.
    """
    return None

  @property
  def stations_ap(self) -> None:
    """ In AP mode, returns list of named tuples, each of which
    contains:

    mac: bytearray (read-only)
    rssi: int (read-only)
    ipv4_address: ipv4_address (read-only, None
    if station connected but no address assigned yet or self-assigned
    address)
    """
    return None

  def start_dhcp(
    self, *,
    ipv4: bool = True,
    ipv6: bool = False) -> None:
    """ Starts the station DHCP client.

    By default, calling this function starts DHCP for IPv4 networks
    but not IPv6 networks. When the the ipv4 and ipv6 arguments are
    False then the corresponding DHCP client is stopped if it was
    active.
    """
    return None

  def stop_dhcp(self) -> None:
    """ Stops the station DHCP client. Needed to assign a static IP
    address.
    """
    return None

  def start_dhcp_ap(self) -> None:
    """ Starts the access point DHCP server. """
    return None

  def stop_dhcp_ap(self) -> None:
    """ Stops the access point DHCP server. Needed to assign a static
    IP address.
    """
    return None

  def ping(
    self,
    ip: ipaddress.IPv4Address, # pylint: disable=invalid-name
    *,
    timeout: Union[float, None] = 0.5) -> Union[float, None]:
    """ Ping an IP to test connectivity. Returns echo time in
    seconds. Returns None when it times out.

    Limitations: On Espressif, calling ping() multiple times rapidly
    exhausts available resources after several calls. Rather than
    failing at that point, ping() will wait two seconds for enough
    resources to be freed up before proceeding.
    """
    return None
