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

# pylint: disable=too-many-public-methods,unused-argument,no-self-use,anomalous-backslash-in-string
class _Radio:
  """
  Native wifi radio.

  This class manages the station and access point functionality
  of the native Wifi radio.
  """

  radio = None
  """ the singleton instance"""

  _CONNECT_ERRORS = {
    "1": "connection timeout",
    "2": "wrong password",
    "3": "cannot find the target AP",
    "4": "connection failed"
    }
  """ error codes returned by CWJAP (connect to AP) """

  _CONNECT_STATE_NOT_STARTED = 0
  _CONNECT_STATE_NO_IP = 1
  _CONNECT_STATE_CONNECTED = 2
  _CONNECT_STATE_IN_PROGESS = 3
  _CONNECT_STATE_DISCONNECTED = 4

  def __init__(self,transport: Transport) -> None:
    """ Constructor. """
    if _Radio.radio:
      return
    self._transport = transport
    self._scan_active = False
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None

    self._mac_address_ap = None
    self._listen_interval = 100
    _Radio.radio = self

  @property
  def enabled(self) -> bool:
    """
    True when the wifi radio is enabled.
    If you set the value to False, any open sockets will be closed.
    """
    reply = self._transport.send_atcmd(
      'AT+CWINIT?',filter="^\+CWINIT:")
    if reply is None:
      raise RuntimeError("Bad response to CWINIT?")
    return str(reply[8:],'utf-8') == "1"

  @enabled.setter
  def enabled(self, value: bool) -> None:
    """Change the enabled status"""
    init = str(int(value))
    reply = self._transport.send_atcmd(
      f'AT+CWINIT={init}',filter="^OK")
    if not reply:
      raise RuntimeError("Could not change radio state")
    if not value:
      self._ipv4_address = None
      self._ipv4_gateway = None
      self._ipv4_netmask = None

  @property
  def hostname(self) -> str:
    """ return the hostname from the wifi interface """
    reply = self._transport.send_atcmd(
      'AT+CWHOSTNAME?',filter="^\+CWHOSTNAME:")
    if reply is None:
      raise RuntimeError("could not query hostname")
    return str(reply[12:],'utf-8')

  @property
  def mac_address(self) -> circuitpython_typing.ReadableBuffer:
    """ MAC address for the station."""
    reply = self._transport.send_atcmd(
      'AT+CIPSTAMAC?',filter="^\+CIPSTAMAC:")
    if reply is None:
      raise RuntimeError("could not query MAC-address")
    return reply[12:-1]

  @property
  def tx_power(self) -> float:
    """ Wifi transmission power, in dBm. """
    reply = self._transport.send_atcmd("AT+RFPOWER?",filter="^\+RFPOWER:")
    if reply:
      return int(str(reply[9:],'utf-8').split(',',1)[0])*0.25
    raise RuntimeError("Bad response to RFPOWER?")

  @tx_power.setter
  def tx_power(self,value: int) -> None:
    """ Change tx_power """
    wifi_power = min(80,value*4)
    self._transport.send_atcmd(f"AT+RFPOWER={wifi_power}")

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
    if self._scan_active:
      raise RuntimeError("scan already in progress")
    self._scan_active = True
    for channel in range(start_channel,stop_channel+1):
      if not self._scan_active:
        raise StopIteration
      try:
        replies = self._transport.send_atcmd(
          f"AT+CWLAP=,,{channel}",filter="^\+CWLAP:",timeout=15)
        if not replies:
          continue
        if isinstance(replies,bytes):
          replies = [replies]
        for line in replies:
          info = line[8:].split(b',')
          network = Network()
          network.ssid = str(info[1],'utf-8')
          network.bssid = info[3]
          network.rssi = int(info[2])
          network.channel = int(info[4])
          network.country = ""
          network.authmode = AuthMode.MODE_MAP[int(info[0])]
          yield network
      except:
        raise

  def stop_scanning_networks(self) -> None:
    """Stop scanning for Wifi networks and free any resources used to
    do it.
    """
    self._scan_active = False

  def start_station(self) -> None:
    """Starts a Station."""
    reply = self._transport.send_atcmd(
      f'AT+CWMODE=1',filter="^OK",timeout=5)
    if not reply:
      raise RuntimeError("Could not switch to station-mode")
    return

  def stop_station(self) -> None:
    """Stopts the Station. This will also disable WIFI."""
    reply = self._transport.send_atcmd(
      f'AT+CWMODE=0',filter="^OK",timeout=5)
    if not reply:
      raise RuntimeError("Could not stop station-mode")

    # clear buffered values
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None
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
    # clear buffered values
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None
    return

  def stop_ap(self) -> None:
    """Stops the access point."""
    reply = self._transport.send_atcmd(
      f'AT+CWMODE=0',filter="^OK",timeout=5)
    if not reply:
      raise RuntimeError("Could not stop AP-mode")
    # clear buffered values
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None
    return

  @property
  def ap_active(self) -> bool:
    """True if running as an access point. (read-only)"""
    return False

  # pylint: disable=too-many-locals,unused-variable
  def connect(
    self,
    ssid: Union[str, circuitpython_typing.ReadableBuffer],
    password: Union[str, circuitpython_typing.ReadableBuffer] = b'',
    *,
    channel: int = 0,
    bssid: Union[str, circuitpython_typing.ReadableBuffer, None] = None,
    timeout: Union[float, None] = 15,
    retries: int = 1,
    pci_en: int = 0,
    reconn_interval: int = 1,
    listen_interval: int = 3,
    scan_mode: int = 1,
    pmf: int = 1) -> None:

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

    The channel parameter is ignored.
    (Note: this is different to core API standard behavior).

    If bssid is given and not None, the scan will start at the first
    channel or the one given and connect to the AP with the given
    bssid and ssid.

    Superset of parameters, specific to the ESP32 AT interface:

      retries: retry connection in case of failure
      pci_en: 0|1 connect|don't connect in OPEN and WEP mode
      reconn_interval: interval between reconnections in seconds (def: 1)
      listen_interval: the interval of listening to the AP’s beacon.
                       Unit: AP beacon intervals. Default: 3. Range: [1,100].
      scan_mode: 0|1 fast scan|scan all channels for strongest signal
      pmf: protected management frames (for details, read the docs)
    """

    if bssid is None:
      bssid = ""
    if timeout < 3:
      timeout = 3
    elif timeout > 600:
      timeout = 600

    cmd = f'AT+CWJAP="{ssid}","{password}",{bssid},{pci_en},{reconn_interval},'
    cmd += f'{listen_interval},{scan_mode},{timeout},{pmf}'
    try:
      reply = self._transport.send_atcmd(
        cmd,
        retries=retries,
        timeout=timeout,
        filter="^WIFI GOT IP|^\+CWJAP:")
    except Exception as ex:
      raise ConnectionError(f"{ex}") from ex

    # clear buffered values
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None

    if not reply:
      raise ConnectionError("connection failed (no error code)")
    if b'CWJAP' in reply:
      code = str(reply[7:],'utf-8')
      if code in _Radio._CONNECT_ERRORS:
        reason = _Radio._CONNECT_ERRORS[code]
      else:
        reason = f"unknown error occured (code: {code})"
      raise ConnectionError("connection failed ({reason})")

  @property
  def connected(self) -> bool:
    """ True if connected to an access point (read-only). """
    reply = self._transport.send_atcmd(
        "AT+CWSTATE?",filter="^\+CWSTATE:")
    if reply:
      state = int(str(reply[9:],'utf-8').split(',',1)[0])
      return state == _Radio._CONNECT_STATE_CONNECTED
    raise RuntimeError("Bad response to CWSTATE?")

  @property
  def ipv4_gateway(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the station gateway when connected to an
    access point. None otherwise. (read-only) """
    if self._ipv4_gateway:
      return self._ipv4_gateway
    self.ipv4_address
    return self._ipv4_gateway

  @property
  def ipv4_gateway_ap(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the access point gateway, when enabled. None
    otherwise. (read-only)"""
    return None

  @property
  def ipv4_subnet(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the station subnet when connected to an
    access point. None otherwise. (read-only) """
    if self._ipv4_netmask:
      return self._ipv4_netmask
    self.ipv4_address
    return self._ipv4_netmask

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
    # check for buffered info
    if self._ipv4_address:
      return self._ipv4_address
    replies = self._transport.send_atcmd(f"AT+CIPSTA?",filter="^\+CIPSTA:")
    if not replies:
      return None
    for line in replies:
      key, value = line[8:].split(b':',1)
      value = str(value,'utf-8').strip('"')
      if value == "0.0.0.0":
        continue
      if key == b"ip":
        self._ipv4_address = ipaddress.ip_address(value)
      elif key == b"gateway":
        self._ipv4_gateway = ipaddress.ip_address(value)
      elif key == b"netmask":
        self._ipv4_netmask = ipaddress.ip_address(value)
    return self._ipv4_address

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
    return [self.ipv4_address] if self.ipv4_address else []

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
    ip: Union[ipaddress.IPv4Address, str], # pylint: disable=invalid-name
    *,
    timeout: Union[float, None] = 0.5) -> Union[float, None]:
    """ Ping an IP to test connectivity. Returns echo time in
    seconds. Returns None when it times out.

    Superset of parameters, specific to the ESP32 AT interface: the
    methods not only accepts an IP-address, but also a hostname.

    Limitations: On Espressif, calling ping() multiple times rapidly
    exhausts available resources after several calls. Rather than
    failing at that point, ping() will wait two seconds for enough
    resources to be freed up before proceeding.
    """

    if not isinstance(ip,str):
      ip = ip.as_string()
    reply = self._transport.send_atcmd(
      f'AT+PING="{ip}"',filter="^\+PING:",timeout=5)
    if reply:
      try:
        return float(str(reply[6:],'utf-8'))
      except Exception as ex:
        raise RuntimeError(f"illegal format: {str(reply[6:],'utf-8')}") from ex
    raise RuntimeError("Bad response to PING")
