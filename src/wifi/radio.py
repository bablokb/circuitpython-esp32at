# -------------------------------------------------------------------------
# Class Radio. This class tries to mimic the class wifi.Radio
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

""" class Radio. """

try:
  from typing import Union, Sequence, Iterable
  import circuitpython_typing
except ImportError:
  pass

import ipaddress
from esp32at.transport import Transport, CALLBACK_WIFI, CALLBACK_STA
from .network import Network
from .authmode import AuthMode

# pylint: disable=too-many-public-methods,unused-argument,no-self-use,anomalous-backslash-in-string, too-many-instance-attributes
class Radio:
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

  # connection states
  _CONNECT_STATE_UNKNOWN = -1
  _CONNECT_STATE_NOT_STARTED = 0
  _CONNECT_STATE_NO_IP = 1
  _CONNECT_STATE_CONNECTED = 2
  _CONNECT_STATE_IN_PROGRESS = 3
  _CONNECT_STATE_DISCONNECTED = 4

  # station/ap mode (can be ORed)
  RUN_MODE_OFF = 0
  RUN_MODE_STATION = 1
  RUN_MODE_AP = 2

  def __new__(cls,transport: Transport):
    if Radio.radio:
      return Radio.radio
    return super(Radio,cls).__new__(cls)

  def __init__(self,transport: Transport) -> None:
    """ Constructor. """
    if Radio.radio:
      return
    self._transport = transport
    self._transport.set_callback(CALLBACK_WIFI,self._wifi_callback)
    self._transport.set_callback(CALLBACK_STA,self._sta_callback)

    self._conn_state = Radio._CONNECT_STATE_UNKNOWN
    self._scan_active = False
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None

    self._ipv4_address_ap = None
    self._ipv4_gateway_ap = None
    self._ipv4_netmask_ap = None

    Radio.radio = self
    self.ipv4_dns_defaults = ['8.8.8.8']  # default ESP32-AT

  def _wifi_callback(self,msg):
    """ callback for Transport.read_atmsg() to set connection state """

    if msg == "WIFI CONNECTED":
      self._conn_state = Radio._CONNECT_STATE_IN_PROGRESS
      if self._transport.debug:
        print("radio: connect in progress")
    elif msg == "WIFI DISCONNECT":
      self._conn_state = Radio._CONNECT_STATE_DISCONNECTED
      if self._transport.debug:
        print("radio: disconnected")
    elif msg == "WIFI GOT_IP":
      self._conn_state = Radio._CONNECT_STATE_CONNECTED
      if self._transport.debug:
        print("radio: fully connected (with IP)")

  def _sta_callback(self,msg):
    """ callback for Transport.read_atmsg() to set station state """

    # TODO: implement!

    msg,args = msg.split(':')   # args have to be trimmed!
    if msg == "+STA_CONNECTED":
      # args[0] is station-MAC
      pass
    elif msg == "DIST_STA_IP":
      # args[0] is station-MAC, args[1] is IP
      pass
    elif msg == "STA_DISCONNECTED":
      # args[0] is station-MAC
      pass

  @property
  def country_settings(self):
    """ query country settings.
    Returns [ignore_ap,country,start_channel,n_channels]. """

    reply = self._transport.send_atcmd("AT+CWCOUNTRY?",
                                      filter="^\+CWCOUNTRY:")
    if not reply:
      raise RuntimeError("could not query country information")
    settings = reply[11:].split(',')
    return [bool(int(settings[0])),
            settings[1].strip('"'),
            int(settings[2]),
            int(settings[3]),
            ]

  # pylint: disable=dangerous-default-value
  @country_settings.setter
  def country_settings(self, value: Sequence = [None,None,None,None]):
    """ configure country settings. Only change provided settings """

    config = self.country_settings
    if not value[0] is None:
      config[0] = str(int(value[0]))
    else:
      config[0] = str(int(config[0]))
    if value[1]:
      config[1] = f'"{value[1]}"'
    else:
      config[1] = f'"{config[1]}"'
    if not value[2] is None:
      config[2] = str(value[2])
    else:
      config[2] = str(config[2])
    if not value[3] is None:
      config[3] = str(value[3])
    else:
      config[3] = str(config[3])

    reply = self._transport.send_atcmd(f"AT+CWCOUNTRY={','.join(config)}",
                            filter="^OK")
    if not reply:
      raise RuntimeError("could not query country information")

  @property
  def run_mode(self) -> int:
    """ query station/AP-mode """
    reply = self._transport.send_atcmd('AT+CWMODE?',filter="^\+CWMODE:")
    if not reply:
      raise RuntimeError("Could not query run-mode")
    return int(reply[8:])

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
    return reply[8:] == "1"

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
      self._ipv4_address_ap = None
      self._ipv4_gateway_ap = None
      self._ipv4_netmask_ap = None

  @property
  def hostname(self) -> str:
    """ return the hostname from the wifi interface """
    reply = self._transport.send_atcmd(
      'AT+CWHOSTNAME?',filter="^\+CWHOSTNAME:")
    if reply is None:
      raise RuntimeError("could not query hostname")
    return reply[12:]

  @hostname.setter
  def hostname(self, name: str) -> None:
    """ configure the hostname """
    reply = self._transport.send_atcmd(
      f'AT+CWHOSTNAME="{name}"',filter="^OK")
    if reply is None:
      raise RuntimeError("could not set hostname (station-mode not active?)")

  @property
  def mac_address(self) -> circuitpython_typing.ReadableBuffer:
    """ MAC address for the station."""
    reply = self._transport.send_atcmd(
      'AT+CIPSTAMAC?',filter="^\+CIPSTAMAC:")
    if reply is None:
      raise RuntimeError("could not query MAC-address")
    return bytes(reply[12:-1],'utf-8')

  @mac_address.setter
  def mac_address(self, value: circuitpython_typing.ReadableBuffer) -> None:
    """ set MAC address for the station."""
    reply = self._transport.send_atcmd(
      f'AT+CIPSTAMAC="{value}"',filter="^OK")
    if reply is None:
      raise RuntimeError("could not set MAC-address")

  @property
  def tx_power(self) -> float:
    """ Wifi transmission power, in dBm. """
    reply = self._transport.send_atcmd("AT+RFPOWER?",filter="^\+RFPOWER:")
    if reply:
      return int(reply[9:].split(',',1)[0])*0.25
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
    reply = self._transport.send_atcmd("AT+CWJAP?",filter="^\+CWJAP:")
    if reply:
      return int(reply[7:].split(',')[6])
    raise RuntimeError("Could not query listen-interval. Not connected?")

  @property
  def mac_address_ap(self) -> circuitpython_typing.ReadableBuffer:
    """ MAC address for the AP."""
    reply = self._transport.send_atcmd(
      'AT+CIPAPMAC?',filter="^\+CIPAPMAC:")
    if reply is None:
      raise RuntimeError("could not query MAC-address")
    return bytes(reply[11:-1],'utf-8')

  @mac_address_ap.setter
  def mac_address_ap(self, value: circuitpython_typing.ReadableBuffer) -> None:
    """ set MAC address for the AP."""
    reply = self._transport.send_atcmd(
      f'AT+CIPAPMAC="{value}"',filter="^OK")
    if reply is None:
      raise RuntimeError("could not set MAC-address")

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
        return
      replies = self._transport.send_atcmd(
        f"AT+CWLAP=,,{channel}",filter="^\+CWLAP:",timeout=15)
      if not replies:
        continue
      if isinstance(replies,str):
        replies = [replies]
      for line in replies:
        info = line[8:].split(',')
        network = Network()
        network.ssid = info[1]
        network.bssid = info[3]
        network.rssi = int(info[2])
        network.channel = int(info[4])
        network.country = ""
        network.authmode = AuthMode.MODE_MAP[int(info[0])]
        yield network

  def stop_scanning_networks(self) -> None:
    """Stop scanning for Wifi networks and free any resources used to
    do it.
    """
    self._scan_active = False

  def start_station(self) -> None:
    """Starts a Station."""

    mode = self.run_mode
    if mode & Radio.RUN_MODE_STATION:
      return

    reply = self._transport.send_atcmd(
      f'AT+CWMODE={mode+Radio.RUN_MODE_STATION}',filter="^OK",timeout=5)
    if not reply:
      raise RuntimeError("Could not start station-mode")
    return

  def stop_station(self) -> None:
    """Stops the Station. This might also disable WIFI."""

    mode = self.run_mode
    if not mode & Radio.RUN_MODE_STATION:
      return

    reply = self._transport.send_atcmd(
      f'AT+CWMODE={mode-Radio.RUN_MODE_STATION}',filter="^OK",timeout=5)
    if not reply:
      raise RuntimeError("Could not stop station-mode")

    # clear buffered values
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None
    return

  # pylint: disable=too-many-branches
  def start_ap(
    self,
    ssid: Union[str, circuitpython_typing.ReadableBuffer],
    password: Union[str, circuitpython_typing.ReadableBuffer] = b'',
    *, channel: int = 1,
    authmode: Iterable[AuthMode] = (),
    max_connections: Union[int, None] = 4,
    hide_ssid: bool = False) -> None:
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

    Superset of parameters, specific to the ESP32 AT interface:

    hide_ssid: hide SSID (default: False)
    """

    # get current mode and return if AP already active
    mode = self.run_mode
    if not mode & Radio.RUN_MODE_AP:
      reply = self._transport.send_atcmd(
        f'AT+CWMODE={mode+Radio.RUN_MODE_AP}',filter="^OK",timeout=5)
      if not reply:
        raise RuntimeError("Could not start AP-mode")

    # clear buffered values if not also running as station
    if not mode & Radio.RUN_MODE_STATION:
      self._ipv4_address = None
      self._ipv4_gateway = None
      self._ipv4_netmask = None

    # map AuthMode to encryption-params
    if not authmode:
      authmode = [AuthMode.OPEN]
    if AuthMode.OPEN not in authmode and AuthMode.PSK not in authmode:
      raise ValueError("unsupported AuthMode")
    if AuthMode.OPEN in authmode:
      if password:
        raise ValueError("open AP with password not allowed")
      ecn = 0
    elif AuthMode.WPA in authmode:
      if AuthMode.WPA2 in authmode:
        ecn = 4
      else:
        ecn = 2
    elif AuthMode.WPA2 in authmode:
      ecn = 3

    # ignore max_connections if unset
    if max_connections is None:
      max_connections = ""

    cmd = (f'AT+CWSAP="{ssid}","{password}",{channel},{ecn},' +
           f'{max_connections},{int(hide_ssid)}')
    reply = self._transport.send_atcmd(cmd,filter="^OK",timeout=5)
    if not reply:
      raise RuntimeError("Could not start AP-mode")

  def stop_ap(self) -> None:
    """Stops the access point."""

    mode = self.run_mode
    if not mode & Radio.RUN_MODE_AP:
      return
    reply = self._transport.send_atcmd(
      f'AT+CWMODE={mode-Radio.RUN_MODE_AP}',filter="^OK",timeout=5)
    if not reply:
      raise RuntimeError("Could not stop station-mode")

    self._ipv4_address_ap = None
    self._ipv4_gateway_ap = None
    self._ipv4_netmask_ap = None

    return

  @property
  def ap_active(self) -> bool:
    """True if running as an access point. (read-only)"""
    return (self.run_mode & Radio.RUN_MODE_AP) > 0

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
      # will return None in case of no errors
      start = time.monotonic()
      reply = self._transport.send_atcmd(
        cmd,
        timeout=timeout,
        retries=retries,
        filter="^\+CWJAP:")
      timeout -= time.monotonic() - start
    except Exception as ex:
      raise ConnectionError(f"{ex}") from ex

    # clear buffered values
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None

    # wait at most timeout seconds for connection
    if not reply:
      start = time.monotonic()
      while (
        self._conn_state != Radio._CONNECT_STATE_CONNECTED and
        time.monotonic() - start < timeout):
        self._transport.read_atmsg(timout=1)
      return

    # otherwise, there is an error
    if 'CWJAP' in reply:
      code = reply[7:]
      if code in Radio._CONNECT_ERRORS:
        reason = Radio._CONNECT_ERRORS[code]
      else:
        reason = f"unknown error occured (code: {code})"
      raise ConnectionError(f"connection failed ({reason})")

  @property
  def connected(self) -> bool:
    """ True if connected to an access point (read-only). """
    reply = self._transport.send_atcmd(
        "AT+CWSTATE?",filter="^\+CWSTATE:")
    if reply:
      state = int(reply[9:].split(',',1)[0])
      return state == Radio._CONNECT_STATE_CONNECTED
    raise RuntimeError("Bad response to CWSTATE?")

  @property
  def ipv4_gateway(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the station gateway when connected to an
    access point. None otherwise. (read-only) """
    if self._ipv4_gateway:
      return self._ipv4_gateway
    self.ipv4_address # pylint: disable=pointless-statement
    return self._ipv4_gateway

  @property
  def ipv4_gateway_ap(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the access point gateway, when enabled. None
    otherwise. (read-only)"""
    if self._ipv4_gateway_ap:
      return self._ipv4_gateway_ap
    self.ipv4_address_ap # pylint: disable=pointless-statement
    return self._ipv4_gateway_ap

  @property
  def ipv4_subnet(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the station subnet when connected to an
    access point. None otherwise. (read-only) """
    if self._ipv4_netmask:
      return self._ipv4_netmask
    self.ipv4_address # pylint: disable=pointless-statement
    return self._ipv4_netmask

  @property
  def ipv4_subnet_ap(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the access point subnet, when enabled. None
    otherwise. (read-only) """
    if self._ipv4_netmask_ap:
      return self._ipv4_netmask_ap
    self.ipv4_address_ap # pylint: disable=pointless-statement
    return self._ipv4_netmask_ap

  @property
  def ipv4_address(self) -> Union[ipaddress.IPv4Address, None]:
    """ IP v4 Address of the station when connected to an access
    point. None otherwise. (read-only)
    """
    # check for buffered info
    if self._ipv4_address:
      return self._ipv4_address
    replies = self._transport.send_atcmd(
      "AT+CIPSTA?",filter="^\+CIPSTA:",timeout=5)
    if not replies:
      return None
    for line in replies:
      key, value = line[8:].split(':',1)
      value = value.strip('"')
      if value == "0.0.0.0":
        continue
      if key == "ip":
        self._ipv4_address = ipaddress.ip_address(value)
      elif key == "gateway":
        self._ipv4_gateway = ipaddress.ip_address(value)
      elif key == "netmask":
        self._ipv4_netmask = ipaddress.ip_address(value)
    return self._ipv4_address

  def set_ipv4_address(
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
    ipv4 = str(ipv4)
    netmask = str(netmask)
    gateway = str(gateway)
    reply = self._transport.send_atcmd(
      f'AT+CIPSTA="{ipv4}","{gateway}","{netmask}"',filter="^OK")
    if reply is None:
      raise RuntimeError("could not set static IP-configuration")

    # clear buffered values
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None

    if ipv4_dns:
      self.ipv4_dns = ipv4_dns

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
    # check for buffered info
    if self._ipv4_address_ap:
      return self._ipv4_address_ap
    replies = self._transport.send_atcmd(
      "AT+CIPAP?",filter="^\+CIPAP:",timeout=5)
    if not replies:
      return None
    for line in replies:
      key, value = line[7:].split(':',1)
      value = value.strip('"')
      if value == "0.0.0.0":
        continue
      if key == "ip":
        self._ipv4_address_ap  = ipaddress.ip_address(value)
      elif key == "gateway":
        self._ipv4_gateway_ap = ipaddress.ip_address(value)
      elif key == "netmask":
        self._ipv4_netmask_ap = ipaddress.ip_address(value)
    return self._ipv4_address_ap

  def set_ipv4_address_ap(
    self, *,
    ipv4: ipaddress.IPv4Address,
    netmask: ipaddress.IPv4Address,
    gateway: ipaddress.IPv4Address) -> None:
    """ Sets the IP v4 address of the access point. Must include the
    netmask and gateway.
    """

    ipv4 = str(ipv4)
    netmask = str(netmask)
    gateway = str(gateway)
    reply = self._transport.send_atcmd(
      f'AT+CIPAP="{ipv4}","{gateway}","{netmask}"',filter="^OK")
    if reply is None:
      raise RuntimeError("could not set static IP-configuration")

    # clear buffered values
    self._ipv4_address_ap = None
    self._ipv4_gateway_ap = None
    self._ipv4_netmask_ap = None

  @property
  def addresses_ap(self) -> Sequence[str]:
    """ Address(es) of the access point when enabled. Empty sequence
    when disabled. (read-only)
    """
    return [self.ipv4_address_ap] if self.ipv4_address_ap else []

  @property
  def ipv4_dns(self) -> ipaddress.IPv4Address:
    """ IP v4 Address of the DNS server to be used. """
    reply = self._transport.send_atcmd("AT+CIPDNS?",filter="^\+CIPDNS:")
    if reply:
      dns = reply[8:].split(',')[1].strip('"')
      return ipaddress.ip_address(dns)
    return None

  @ipv4_dns.setter
  def ipv4_dns(self,value: ipaddress.IPv4Address) -> None:
    """ IP v4 Address of the DNS server to be used. """
    self.dns = [str(value), self.ipv4_dns_defaults[0]]

  @property
  def dns(self) -> Sequence[str]:
    """ Addresses of the DNS server to be used. """
    reply = self._transport.send_atcmd("AT+CIPDNS?",filter="^\+CIPDNS:")
    if reply:
      dns = reply[8:].split(',')[1:]
      return [d.strip('"') for d in dns]
    return []

  @dns.setter
  def dns(self,addresses: Sequence[str]) -> None:
    """ Addresses of the DNS server to be used. """
    args = '1'   # enable manual DNS
    for addr in addresses:
      args += f',"{addr}"'
    if len(addresses) < 2:
      args += f',"{self.ipv4_dns_defaults[0]}"'
    reply = self._transport.send_atcmd(f"AT+CIPDNS={args}",filter="^OK")
    if reply is None:
      raise RuntimeError("could not set static IPv4-DNS")

  @property
  def ap_info(self) -> Union[Network, None]:
    """ Network object containing BSSID, SSID, authmode, channel,
    country and RSSI when connected to an access point. None
    otherwise.
    """
    reply = self._transport.send_atcmd("AT+CWJAP?",filter="^\+CWJAP:")
    if not reply:
      return None

    info = reply[7:].split(',')
    if len(info) == 1:
      return None  # probably not connected

    ssid = info[0].strip('"')
    reply = self._transport.send_atcmd(
      f'AT+CWLAP="{ssid}"',filter="^\+CWLAP:",timeout=15)
    if not reply:
      return None
    info = reply[8:].split(',')
    network = Network()
    network.ssid = ssid
    network.bssid = info[3]
    network.rssi = int(info[2])
    network.channel = int(info[4])
    network.authmode = AuthMode.MODE_MAP[int(info[0])]
    try:
      network.country = self.country_settings[1]
    except: # pylint: disable=bare-except
      network.country = ''
    return network

  @property
  def stations_ap(self) -> None:
    """ In AP mode, returns list of named tuples, each of which
    contains:

    mac: bytearray (read-only)
    rssi: int (read-only)
    ipv4_address: ipv4_address (read-only, None
    if station connected but no address assigned yet or self-assigned
    address)

    Not implemented in AT command set.
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
    reply = self._transport.send_atcmd(
      'AT+CWDHCP=1,1',filter="^OK")
    if not reply:
      raise RuntimeError("Could not start DHCP")
    # clear buffered values
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None

  def stop_dhcp(self) -> None:
    """ Stops the station DHCP client. Needed to assign a static IP
    address.
    """
    reply = self._transport.send_atcmd(
      'AT+CWDHCP=0,1',filter="^OK")
    if not reply:
      raise RuntimeError("Could not stop DHCP")
    # clear buffered values
    self._ipv4_address = None
    self._ipv4_gateway = None
    self._ipv4_netmask = None

  def start_dhcp_ap(self) -> None:
    """ Starts the access point DHCP server. """
    reply = self._transport.send_atcmd(
      'AT+CWDHCP=1,2',filter="^OK")
    if not reply:
      raise RuntimeError("Could not start DHCP (AP)")

  def stop_dhcp_ap(self) -> None:
    """ Stops the access point DHCP server. Needed to assign a static
    IP address.
    """
    reply = self._transport.send_atcmd(
      'AT+CWDHCP=0,2',filter="^OK")
    if not reply:
      raise RuntimeError("Could not stop DHCP (AP)")

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
      ip = str(ip)
    try:
      reply = self._transport.send_atcmd(
        f'AT+PING="{ip}"',filter="^\+PING:",timeout=5)
      if reply:
        if 'TIMEOUT' in reply:
          return None
        try:
          return float(reply[6:])
        except Exception as ex:
          raise RuntimeError(f"illegal format: {reply[6:]}") from ex
      return None
    except: # pylint: disable=bare-except
      return None
