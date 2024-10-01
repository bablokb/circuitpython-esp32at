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
from digitalio import DigitalInOut
from micropython import const

try:
  import circuitpython_typing
  from typing import Optional, Union, Sequence
except ImportError:
  pass

RESET_NEVER = const(0)
""" don't reset during init """

RESET_ON_FAILURE = const(1)
""" reset on failure during init """

RESET_ALWAYS = const(2)
""" always reset during init """

CALLBACK_CONN = const(0)
""" index to callback method """

CALLBACK_IPD = const(1)
""" index to callback method """

CALLBACK_PROMPT = const(2)
""" index to callback method """

CALLBACK_WIFI = const(3)
""" index to callback method """

CALLBACK_STA = const(4)
""" index to callback method """

CALLBACK_SEND = const(5)
""" index to callback method """

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

  _MSG_PASSIVE_END = ["OK", "ERROR", "busy p...", "SEND OK", "SEND FAIL"]
  """ end-messages in passive-mode """

  # pylint: disable=anomalous-backslash-in-string
  _MSG_REX = [
    "^([0-9]+,)?(CONNECT|CLOSED)",
    "^\+IPD",
    "^>",
    "^WIFI",
    "^\+(DIST_)?STA_",
    "^SEND Cancelled"
    ]
  """ regex for messages, indices must match callback indices """


  def __new__(cls):
    if Transport.transport:
      return Transport.transport
    return super(Transport,cls).__new__(cls)

  def __init__(self):
    """ Do nothing constructor. Use init() for hardware-setup """
    if Transport.transport:
      return
    self._msg_callbacks = [lambda msg: None]*6
    self._lock = False
    self._uart = None
    self._at_timeout = 1
    self._at_retries = 1
    self._reset_pin = None
    self.debug = None
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
    self.debug = debug
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
      self._at_version = reply
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
      # pylint: disable=anomalous-backslash-in-string
      reply = self.send_atcmd("AT+UART_CUR?",filter="^\+UART_CUR:")
      if not reply:
        return
      old_baudrate = reply[10:].split(',')
    except: # pylint: disable=bare-except
      return

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
    if reply == "OK":
      # RST command acknowleged
      if self.debug:
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
      if self.debug:
        print("waiting 3 seconds for hard reset")
      time.sleep(3)  # give it a few seconds to wake up
      self._uart.baudrate = 115200
      self._uart.reset_input_buffer()
      return True
    return False

  # --- message processing   -------------------------------------------------

  def set_callback(self,index,func):
    """ configure callback for given CB index """
    self._msg_callbacks[index] = func

  def read_atmsg(self,timeout: float = -1,
                 passive=False) -> Tuple[bool, Union[Sequence[str],None]]:
    """ read pending AT messages """

    # use global defaults
    if timeout < 0:
      timeout = self._at_timeout

    result = []

    # wait at most timeout seconds for input
    start = time.monotonic()
    while time.monotonic() - start < timeout and not self._uart.in_waiting:
      pass

    if not self._uart.in_waiting:
      return False,result

    # read all messages
    while self._uart.in_waiting:
      msg = self._uart.readline()[:-2]
      if self.debug:
        print(f"<--- {msg=}")
      if not msg:                           # ignore empty lines
        continue
      msg = str(msg,'utf-8')

      # even in passive mode the AT-firmware sends unrelated messages
      # so check for messages with callback first
      processed = False
      if msg not in Transport._MSG_PASSIVE_END:
        for index,rex in enumerate(Transport._MSG_REX):
          if re.match(rex,msg):
            if self.debug:
              print(f"     callback processing for '{msg}'")
            self._msg_callbacks[index](msg)
            processed = True
            break

      # in passive mode just return everything until OK/ERROR
      if not processed and passive:
        result.append(msg)
        if self.debug:
          print(f"     appending to result...")
        if msg in Transport._MSG_PASSIVE_END:
          return msg!='busy p...',result
        continue

    # timed out or incomplete response
    if passive:
      return False,result

    # in active mode the return value is not relevant
    return True,[]

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
      raise LockError("AT commands are locked (pending data)")

    # use global defaults
    if timeout < 0:
      timeout = self._at_timeout
    if retries < 0:
      retries = self._at_retries


    # process pending active messages
    self.read_atmsg(passive=False,timeout=0)

    # input should be cleared, send command
    for i in range(retries):
      if self.debug:
        print("--->", at_cmd)
      self._uart.write(bytes(at_cmd, "utf-8"))
      self._uart.write(b"\x0d\x0a")
      # read response
      success, raw_response = self.read_atmsg(passive=True,timeout=timeout)
      if success:
        break
      if i<retries-1:
        time.sleep(1)

    # process pending active messages
    self.read_atmsg(passive=False,timeout=0)

    # final processing
    if self.debug:
      for line in raw_response:
        print(f"raw: {line}")
    if not success:
      # special case, ping also does not return an OK on timeout
      # if "AT+PING" in at_cmd and b"ERROR\r\n" in raw_response:
      raise TransportError(f"AT-command {at_cmd} failed ({raw_response=})")

    # check for filter
    if filter:
      response = [msg for msg in raw_response if re.match(filter,msg)]
      if len(response) == 0:
        response = None
      elif len(response) == 1:
        response = response[0]
    else:
      response = raw_response
    if self.debug:
      if isinstance(response,str):
        print(f"<--- {response}")
      else:
        for line in response:
          print(f"<--- {line}")
    return response

  # --- wait for specific texts (prompt, result)   ---------------------------

  def wait_for(self,rex: str, greedy: bool=True, timeout: float = -1) -> bytes:
    """ wait for specific text, specified as regex """

    # use global defaults
    if timeout < 0:
      timeout = self._at_timeout

    txt = ""
    stamp = time.monotonic()
    while (time.monotonic() - stamp) < timeout:
      if self._uart.in_waiting:
        txt += self._uart.read(self._uart.in_waiting if greedy else 1)
        if re.match(rex,txt):
          if self.debug:
            print(f"match: {txt=}")
          return txt
    if self.debug:
      print(f"no match: {txt=}")
    raise RuntimeError(f"timeout waiting for {rex}. {txt=}")

  # --- write bytes to the interface   ---------------------------------------

  def write(self,
            buffer: circuitpython_typing.ReadableBuffer) -> None:
    """ write bytes to the UART-interface """
    if self.debug:
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
    if self.debug:
      n = self._uart.readinto(mv_target)
      print(f"<--- {n} bytes: {buffer[:min(n,40)]}...")
      return n
    return self._uart.readinto(mv_target)

  # --- hardware tweaks   ----------------------------------------------------

  def _echo(self, echo: bool) -> None:
    """Set AT command echo on or off"""
    if echo:
      self.send_atcmd("ATE1")
    else:
      self.send_atcmd("ATE0")
