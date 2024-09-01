# -------------------------------------------------------------------------
# Class Transport. This class implements the low-level interface to the
# co-processor.
#
# The sole instance of this class is available as wifi.transport
#
# Most of this code is from
# https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class Transport. """

import time
import re

import busio
from digitalio import Direction, DigitalInOut

try:
  from typing import Optional
except ImportError:
  pass

class TransportError(Exception):
  """The exception thrown when we didn't get acknowledgement to an AT command"""

class Transport:
  """ Low-level interface to the AT-commandset of the ESP32xx.  The
  ESP module must be pre-programmed with AT command firmware. See
  https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/index.html
  and
  https://github.com/espressif/esp-at
  """

  # pylint: disable=too-many-public-methods, too-many-instance-attributes
  MODE_STATION = 1
  MODE_SOFTAP = 2
  MODE_SOFTAPSTATION = 3
  TYPE_TCP = "TCP"
  TCP_MODE = "TCP"
  TYPE_UDP = "UDP"
  TYPE_SSL = "SSL"
  TLS_MODE = "SSL"
  STATUS_APCONNECTED = 2  # CIPSTATUS method
  STATUS_SOCKETOPEN = 3  # CIPSTATUS method
  STATUS_SOCKET_OPEN = 3  # CIPSTATE method
  STATUS_SOCKETCLOSED = 4  # CIPSTATUS method
  STATUS_SOCKET_CLOSED = 4  # CIPSTATE method
  STATUS_NOTCONNECTED = 5  # CIPSTATUS method

  transport = None
  """ the singleton instance """

  def __init__(self):
    """ Do nothing constructor. Use init() for hardware-setup """
    if Transport.transport:
      return
    self._uart = None
    self._at_timeout = 1
    self._at_retries = 1
    self._reset_pin = None
    self._debug = None
    self._at_version = None
    Transport.transport = self

  def init(self,
           uart: busio.UART,
           *,
           at_timeout: Optional[float] = 1,
           at_retries: Optional[int] = 1,
           reset_pin: Optional[DigitalInOut] = None,
           debug: bool = False,
           ):
    """ initialize hardware, and query AT firmware version """

    self._uart = uart
    self._at_timeout = at_timeout
    self._at_retries = at_retries
    self._reset_pin = reset_pin
    self._debug = debug

    if self._reset_pin:
      self._reset_pin.direction = Direction.OUTPUT
      self._reset_pin.value = True

    # try to connect with the ESP32xx co-processor
    for _ in range(3):
      try:
        try:
          self._get_version()
        except TransportError:
          # try to reset the device
          self.hard_reset()
          self.soft_reset()
          continue

        self._echo(False)
        return
      except TransportError:
        pass  # retry

  # --- query AT firmware version   ------------------------------------------

  def _get_version(self) -> None:
    """Request the AT firmware version string and parse out the
    version number"""
    reply = self.send_atcmd("AT+GMR",filter="^AT version:")
    if reply:
      self._at_version = str(reply, "utf-8")
    else:
      raise TransportError("could not query AT version")

  @property
  def at_version(self) -> str:
    """ the AT firmware version """
    return self._at_version

  # --- soft, hard, factory resets   -----------------------------------------

  def soft_reset(self, timeout: int = 5) -> bool:
    """Perform a software reset by AT command. Returns True
    if we successfully performed, false if failed to reset"""
    try:
      reply = self.send_atcmd("AT+RST", timeout=timeout)
      if reply == b'OK':
        return True
    except TransportError:
      pass  # fail, see below
    return False

  def restore_factory_settings(self) -> None:
    """Send factory restore settings request"""
    self.send_atcmd("AT+RESTORE", timeout=5)

  def hard_reset(self) -> None:
    """Perform a hardware reset by toggling the reset pin, if it was
    defined in the initialization of this object"""
    if self._reset_pin:
      self._reset_pin.direction = Direction.OUTPUT
      self._reset_pin.value = False
      time.sleep(0.1)
      self._reset_pin.value = True
      time.sleep(3)  # give it a few seconds to wake up
      self._uart.reset_input_buffer()

  # --- send command to the co-processor   -----------------------------------

  # pylint: disable=redefined-builtin,too-many-statements
  def send_atcmd(self, # pylint: disable=too-many-branches
                 at_cmd: str,
                 timeout: float = -1,
                 retries: int = -1,
                 filter = None) -> bytes:
    """Send an AT command, check that we got an OK response,
    and then cut out the reply lines to return. We can set
    a variable timeout (how long we'll wait for response) and
    how many times to retry before giving up"""

    # use global defaults
    if timeout < 0:
      timeout = self._at_timeout
    if retries < 0:
      retries = self._at_retries

    finished = False
    for _ in range(retries):
      time.sleep(0.1)  # wait for uart data
      self._uart.reset_input_buffer()  # flush it
      if self._debug:
        print("--->", at_cmd)
      self._uart.write(bytes(at_cmd, "utf-8"))
      self._uart.write(b"\x0d\x0a")
      stamp = time.monotonic()
      raw_response = b""
      while (time.monotonic() - stamp) < timeout:
        if self._uart.in_waiting:
          raw_response += self._uart.read(1)
          if raw_response[-4:] == b"OK\r\n":
            finished = True
            break
          if raw_response[-7:] == b"ERROR\r\n":
            finished = True
            break
          if "AT+CWJAP=" in at_cmd or "AT+CWJEAP=" in at_cmd:
            if b"WIFI GOT IP\r\n" in raw_response:
              finished = True
              break
          if b"ERR CODE:" in raw_response:
            finished = True
            break

      if finished:
        break
      # special case, AT+CWJAP= does not return an ok :P
      if "AT+CWQAP=" in at_cmd and b"WIFI DISCONNECT" in raw_response:
        finished = True
        break
      # special case, ping also does not return an OK on timeout
      if "AT+PING" in at_cmd and b"ERROR\r\n" in raw_response:
        finished = True
        break
      # special case, does return OK but in fact it is busy
      if (
          "AT+CIFSR" in at_cmd
          and b"busy" not in raw_response
          and raw_response[-4:] == b"OK\r\n"
      ):
        finished = True
        break
      time.sleep(1)

    # final processing
    if self._debug:
      print("<--- (raw)", raw_response)
    if not finished:
      raise TransportError(f"AT-command {at_cmd} failed")

    # split results by lines
    if filter:
      response = raw_response[:-2].split(b"\r\n")
      response = [r for r in response if re.match(filter,r)]
      if len(response) == 0:
        response = None
      elif len(response) == 1:
        response = response[0]
    else:
      response = raw_response
    if self._debug:
      print("<---", response)
    return response

  # --- hardware tweaks   ----------------------------------------------------

  def _echo(self, echo: bool) -> None:
    """Set AT command echo on or off"""
    if echo:
      self.send_atcmd("ATE1")
    else:
      self.send_atcmd("ATE0")
