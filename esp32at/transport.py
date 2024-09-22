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
  import circuitpython_typing
  from typing import Optional, Union
except ImportError:
  pass

RESET_NEVER = 0
""" don't reset during init """

RESET_ON_FAILURE = 1
""" reset on failure during init """

RESET_ALWAYS = 2
""" always reset during init """

class LockError(Exception):
  """ The exception thrown when the AT command processor is locked """

class TransportError(Exception):
  """The exception thrown when we didn't get acknowledgement to an AT command"""

# pylint: disable=too-many-public-methods, too-many-instance-attributes
class Transport:
  """ Low-level interface to the AT-commandset of the ESP32xx.  The
  ESP module must be pre-programmed with AT command firmware. See
  https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/index.html
  and
  https://github.com/espressif/esp-at
  """

  transport = None
  """ the singleton instance """

  def __new__(cls):
    if Transport.transport:
      return Transport.transport
    return super(Transport,cls).__new__(cls)

  def __init__(self):
    """ Do nothing constructor. Use init() for hardware-setup """
    if Transport.transport:
      return
    self._lock = False
    self._uart = None
    self._at_timeout = 1
    self._at_retries = 1
    self._reset_pin = None
    self._debug = None
    self._at_version = None
    self.reconn_interval = 1
    Transport.transport = self

  def init(self,
           uart: busio.UART,
           *,
           at_timeout: Optional[float] = 1,
           at_retries: Optional[int] = 1,
           reset: Optional[int] = RESET_ON_FAILURE,
           hard_reset: Optional[int] = RESET_NEVER,
           reset_pin: Optional[circuitpython_typing.Pin] = None,
           persist_settings: Optional[bool] = True,
           reconn_interval: Optional[int] = 1,
           multi_connection: Optional[bool] = False,
           baudrate: Union[int, str] = None,
           debug: bool = False,
           ) -> bool:
    """ initialize hardware, and query AT firmware version """

    self._uart = uart
    self._at_timeout = at_timeout
    self._at_retries = at_retries
    self._debug = debug
    self.reconn_interval = reconn_interval

    if reset_pin:
      self._reset_pin = DigitalInOut(reset_pin)
      self._reset_pin.switch_to_output(True)
    else:
      hard_reset = RESET_NEVER

    # check if a reset is requested
    if hard_reset == RESET_ALWAYS:
      self.hard_reset()
    elif reset == RESET_ALWAYS:
      self.soft_reset()

    # try two times to connect with the ESP32xx co-processor
    connected = False
    for _ in range(2):
      try:
        self._get_version()
        connected = True
        self._echo(False)
        break
      except TransportError:
        # try to reset the device
        if hard_reset == RESET_ON_FAILURE:
          self.hard_reset()
        elif reset == RESET_ON_FAILURE:
          self.soft_reset()

    if not connected:
      return False

    # configure the co-processor (best effort)
    try:
      self.send_atcmd("AT+CIPDINFO=1")
      if not persist_settings: # always on after reset
        self.send_atcmd("AT+SYSSTORE=0")
      self.send_atcmd(f"AT+CWRECONNCFG={reconn_interval},0")
      self.send_atcmd(f"AT+CIPMUX={int(multi_connection)}")
    except: # pylint: disable=bare-except
      pass

    # configure non-default baudrate
    if not baudrate is None:
      self.baudrate = baudrate
    return True

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

  @property
  def baudrate(self) -> int:
    """ query current baudrate """
    return self._uart.baudrate

  @baudrate.setter
  def baudrate(self, value: str) -> None:
    """ set (temporary) baudrate of co-processor and UART (best effort) """
    try:
      reply = self.send_atcmd("AT+UART_CUR?",filter="^\+UART_CUR:")
      if not reply:
        return True
      old_baudrate = str(reply[10:],'utf-8').split(',')
    except:
      return True

    baudrate = str(value).split(',')
    len_parms = len(baudrate)
    if len_parms < 2:
      baudrate.append(old_baudrate[1])   # databits
    if len_parms < 3:
      baudrate.append(old_baudrate[2])   # stopbits
    if len_parms < 4:
      baudrate.append(old_baudrate[3])   # parity
    if len_parms < 5:
      baudrate.append(old_baudrate[4])   # flow control

    reply = self.send_atcmd(f"AT+UART_CUR={','.join(baudrate)}",filter="^OK")
    if reply:
      self._uart.baudrate = int(baudrate[0])

  # --- soft, hard, factory resets   -----------------------------------------

  def soft_reset(self, timeout: int = 5) -> bool:
    """Perform a software reset by AT command. Returns True
    if we successfully performed, false if failed to reset"""
    try:
      reply = self.send_atcmd("AT+RST", timeout=timeout,filter="^OK")
    except TransportError:
      reply = ""
    if reply == b"OK":
      # RST command acknowleged
      if self._debug:
        print("waiting 3 seconds for reset")
      time.sleep(3)  # in case of a reboot
    self._uart.baudrate = 115200
    self._uart.reset_input_buffer()
    return reply == b'OK'

  def restore_factory_settings(self) -> None:
    """Send factory restore settings request"""
    self.send_atcmd("AT+RESTORE", timeout=5)

  def hard_reset(self) -> None:
    """Perform a hardware reset by toggling the reset pin, if it was
    defined in the initialization of this object"""
    if self._reset_pin:
      self._reset_pin.value = False
      time.sleep(0.1)
      self._reset_pin.value = True
      if self._debug:
        print("waiting 3 seconds for hard reset")
      time.sleep(3)  # give it a few seconds to wake up
      self._uart.baudrate = 115200
      self._uart.reset_input_buffer()
      return True
    return False

  # --- send command to the co-processor   -----------------------------------

  @property
  def lock(self) -> bool:
    """ lock-status of AT commands (True if data is pending) """
    return self._lock

  @lock.setter
  def lock(self, value: bool) -> None:
    """ set lock status """
    self._lock = value

  # pylint: disable=redefined-builtin,too-many-statements
  def send_atcmd(self, # pylint: disable=too-many-branches
                 at_cmd: str,
                 timeout: float = -1,
                 retries: int = -1,
                 filter: str = None) -> bytes:
    """Send an AT command, check that we got an OK response,
    and then cut out the reply lines to return. We can set
    a variable timeout (how long we'll wait for response) and
    how many times to retry before giving up"""

    if self.lock:
      raise LockError("AT commands are locked (pendig data)")

    # use global defaults
    if timeout < 0:
      timeout = self._at_timeout
    if retries < 0:
      retries = self._at_retries

    finished = False
    for i in range(retries):
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
      if i < retries-1:  # wait before retrying
        time.sleep(1)

    # final processing
    if self._debug:
      print("<--- (raw)", raw_response)
    if not finished:
      raise TransportError(f"AT-command {at_cmd} failed ({raw_response=})")

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

  # --- wait for specific texts (prompt, result)   ---------------------------

  def wait_for(self,rex: str, greedy: bool=True, timeout: float = -1) -> bytes:
    """ wait for specific text, specified as regex """

    # use global defaults
    if timeout < 0:
      timeout = self._at_timeout

    txt = b""
    stamp = time.monotonic()
    while (time.monotonic() - stamp) < timeout:
      if self._uart.in_waiting:
        txt += self._uart.read(self._uart.in_waiting if greedy else 1)
        if re.match(rex,txt):
          if self._debug:
            print(f"{txt=}")
          return txt
    if self._debug:
      print(f"{txt=}")
    raise RuntimeError(f"timeout waiting for {rex}. {txt=}")

  # --- write bytes to the interface   ---------------------------------------

  def write(self,
            buffer: circuitpython_typing.ReadableBuffer) -> None:
    """ write bytes to the UART-interface """
    if self._debug:
      print(f"---> {len(buffer)} bytes: {buffer[:min(len(buffer),40)]}...")
    self._uart.reset_input_buffer()
    self._uart.write(buffer)

  # --- read bytes from the interface into a buffer   ------------------------

  @property
  def input_available(self) -> bool:
    """ check for available input (read-only) """
    return self._uart.in_waiting > 0

  def readinto(self,
               buffer: circuitpython_typing.WriteableBuffer,
               bufsize: int) -> int:
    """ read data from the uart """
    mv_buffer = memoryview(buffer)
    mv_target = mv_buffer[0:bufsize]
    if self._debug:
      n = self._uart.readinto(mv_target)
      print(f"<--- n bytes: {mv_target[:min(n,40)]}...")
    return

  # --- hardware tweaks   ----------------------------------------------------

  def _echo(self, echo: bool) -> None:
    """Set AT command echo on or off"""
    if echo:
      self.send_atcmd("ATE1")
    else:
      self.send_atcmd("ATE0")
