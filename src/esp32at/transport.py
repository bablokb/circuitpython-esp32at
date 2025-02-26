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
  from typing import Optional, Union, Sequence, Tuple
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

CALLBACK_WIFI = const(2)
""" index to callback method """

CALLBACK_STA = const(3)
""" index to callback method """

CALLBACK_SEND = const(4)
""" index to callback method """

PT_OFF = const(0)
""" normal mode (no passthrough) """

PT_AUTO = const(1)
""" switch to passthrough-mode after connect """

PT_ON = const(2)
""" passthrough mode """

class RebootError(Exception):
  """The exception thrown during firmware reboot"""

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

  _MSG_PASSIVE_END = ["OK", "ERROR"]
  """ end-messages in passive-mode """

  # pylint: disable=anomalous-backslash-in-string
  _MSG_REX = [
    "^([0-9]+,)?(CONNECT|CLOSED)",
    "^\+IPD",
    "^WIFI",
    "^\+(DIST_)?STA_",
    "^SEND"
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

    # keep pylint happy by defining variables here
    self._msg_callbacks = [lambda msg: None]*6
    self._passthrough = False
    self._pt_policy = PT_OFF
    self._uart = None
    self._at_retries = 1
    self._reset_pin = None
    self.debug = None
    self._at_version = None
    self.at_version_short = None
    self._multi_connections = None
    self.max_connections = 5
    self.reconn_interval = 1
    self.busy = False
    Transport.transport = self

  # pylint: disable=too-many-branches
  def init(self,
           uart: busio.UART,
           *,
           at_retries: Optional[int] = 1,
           reset: Optional[int] = RESET_ON_FAILURE,
           hard_reset: Optional[int] = RESET_NEVER,
           reset_pin: Optional[circuitpython_typing.Pin] = None,
           persist_settings: Optional[bool] = True,
           reconn_interval: Optional[int] = 1,
           multi_connection: Optional[bool] = True,
           baudrate: Union[int, str] = None,
           debug: bool = False,
           ) -> bool:
    """ initialize hardware, and query AT firmware version """

    self._uart = uart
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
      self.soft_reset()           # this can fail if the firmware is not ready

    # try two times to connect with the ESP32xx co-processor
    connected = False
    for _ in range(2):
      try:
        self.multi_connections = multi_connection

        # query number of supported connections
        reply = self.send_atcmd('AT+CIPSERVERMAXCONN?',
                                filter="^\+CIPSERVERMAXCONN:")
        if reply is None:
          raise RuntimeError("could not query max connections")
        self.max_connections = int(reply[18:])

        # set passive receive-mode
        reply = self.send_atcmd(
          f'AT+CIPRECVTYPE={self.max_connections},1',filter="^OK")
        if reply is None:
          reply = self.send_atcmd(
            'AT+CIPRECVMODE=1',filter="^OK")
          if reply is None:
            raise RuntimeError("could not set passive receive-mode")

        self._get_version()
        connected = True
        self._echo(False)
        break
      except Exception as ex: # pylint: disable=broad-except
        # try to reset the device
        if hard_reset == RESET_ON_FAILURE:
          self.hard_reset()
        elif reset == RESET_ON_FAILURE:
          if isinstance(ex,RebootError):  # give the system some time to boot
            time.sleep(3)
          self.soft_reset()

    if not connected:
      return False

    # configure the co-processor (best effort)
    # also, close left-over connections in the co-processor
    try:
      if not persist_settings: # always on after reset
        self.send_atcmd("AT+SYSSTORE=0")
      self.send_atcmd(f"AT+CWRECONNCFG={reconn_interval},0")
      self.send_atcmd("AT+CIPDINFO=1")
      self.send_atcmd(f"AT+CIPCLOSE={self.max_connections}")
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
      reply = reply.split(":",1)[1]
      self.at_version_short = [int(r) for r in reply.split(".",3)[:3]]
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

  # pylint: disable=too-many-branches,too-many-arguments
  def read_atmsg(self,timeout: float = 0, read_until: str = None,
                 passive=False) -> Tuple[bool, Union[Sequence[str],None]]:
    """
    Read pending AT messages.

    In passive mode, timeout=0 will block. This should be the default,
    since an incomplete send/read will likely trigger a 'busy p...'-message.
    """

    start = time.monotonic()
    if passive and not timeout:
      timeout = 1000000
    result = []

    # wait at most timeout seconds for input
    while time.monotonic() - start < timeout and not self._uart.in_waiting:
      pass

    if not self._uart.in_waiting:   # i.e. we have a timeout
      return False,result

    # read all messages
    processed = False
    if read_until:
      min_waiting = min(1,len(read_until)-1)  # if we wait for a single char
    else:
      min_waiting = 1
    while passive or self._uart.in_waiting > min_waiting:
      if not self._uart.in_waiting > min_waiting:
        continue

      # special processing when parsing until a specific string:
      # read in single-byte mode until EOL or the target-string is read
      if read_until:
        msg = b""
        while True:
          msg += self._uart.read(1)
          if msg[-2:] == b'\r\n':     # EOL: complete msg without <read_until>
            msg = msg[:-2]
            break
          if read_until in msg:
            if self.debug:
              print(f"<--- msg(read_until): '{read_until}'")
            return True, read_until
      else:
        msg = self._uart.readline()[:-2]
      if self.debug:
        print(f"<--- {msg=}")
      if not msg:                           # ignore empty lines
        continue

      # some shortcuts for special messages
      if b'busy p...' in msg:
        result.append("busy p...")
        return False, result
      if b'ESP-ROM' in msg or b'\x1b[0;32m' in msg:
        raise RebootError("firmware boot in progress")

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
          print("     appending to result...")
        if msg in Transport._MSG_PASSIVE_END:
          return True,result
        continue

    # timed out or incomplete response
    if passive:
      return False,result

    # active mode: return processing state, but no messages
    return processed,[]

  # --- send command to the co-processor   -----------------------------------

  def _wait_while_busy(self):
    """ wait while busy-flag is set """
    # TODO: think about timing out with Exception
    if self.debug:
      print("busy... waiting")
    while self.busy:
      self.read_atmsg(passive=False)
    if self.debug:
      print("busy flag cleared")

  # pylint: disable=redefined-builtin,too-many-statements
  def send_atcmd(self, # pylint: disable=too-many-branches
                 at_cmd: str,
                 timeout: float = 0,
                 retries: int = -1,
                 read_until: str = None,
                 filter: str = None,
                 set_busy: bool = False) -> bytes:
    """Send an AT command, check that we got an OK response,
    and then cut out the reply lines to return. We can set
    a variable timeout (how long we'll wait for response) and
    how many times to retry before giving up"""

    if self.debug:
      print(f"send_atcmd({at_cmd}) start -----------")

    # use global defaults
    if retries < 0:
      retries = self._at_retries

    # process pending active messages
    self.read_atmsg(passive=False)

    # input should be cleared, send command
    self.busy and self._wait_while_busy() # pylint: disable=expression-not-assigned
    self.busy = set_busy
    for i in range(retries):
      if self.debug:
        print("--->", at_cmd)
      self._uart.write(bytes(at_cmd, "utf-8"))
      self._uart.write(b"\x0d\x0a")
      # read response
      success, raw_response = self.read_atmsg(
        passive=True,read_until=read_until,timeout=timeout)
      if success:
        break
      if i<retries-1:
        time.sleep(1)

    # process cmd-triggered active messages (if any)
    if not read_until:
      self.read_atmsg(passive=False)

    # final processing
    if self.debug:
      if raw_response is None or isinstance(raw_response,str):
        print(f"raw: {raw_response}")
      else:
        for line in raw_response:
          print(f"raw {line}")
    if not success:
      if self.debug:
        print(f"send_atcmd({at_cmd}) end (TransportError) -----")
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
      if response is None or isinstance(response,str):
        print(f"<--- {response}")
      else:
        for line in response:
          print(f"<--- {line}")
    if self.debug:
      print(f"send_atcmd({at_cmd}) end -------------")
    return response

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
    """ read data from the uart into a buffer """
    mv_buffer = memoryview(buffer)
    mv_target = mv_buffer[0:bufsize]
    if self.debug:
      n = self._uart.readinto(mv_target)
      if n is not None:
        print(f"<--- {n} bytes: {bytes(buffer[:min(n,40)])}...")
      else:
        n = 0
      return n
    return self._uart.readinto(mv_target)

  def read(self, count: int) -> int:
    """ read raw data from the uart """
    return self._uart.read(count)

  # --- hardware tweaks   ----------------------------------------------------

  def _echo(self, echo: bool) -> None:
    """Set AT command echo on or off"""
    if echo:
      self.send_atcmd("ATE1")
    else:
      self.send_atcmd("ATE0")

  # --- connection configuration   -------------------------------------------

  @property
  def multi_connections(self) -> bool:
    """ query multi-connection setting """
    return self._multi_connections

  @multi_connections.setter
  def multi_connections(self, flag: bool) -> None:
    """ enable/disable multi-connections """

    if flag != self._multi_connections:
      reply = self.send_atcmd(f'AT+CIPMUX={int(flag)}',filter="^OK")
      if reply is None:
        raise RuntimeError("could not set connection-mode")
    self._multi_connections = flag

  # --- passthrough mode   ---------------------------------------------------

  @property
  def pt_policy(self) -> int:
    """ query passthrough policy """
    return self._pt_policy

  @pt_policy.setter
  def pt_policy(self,value: int):
    """ set passthrough policy """
    if value == PT_OFF:
      self.passthrough = False
    elif value == PT_AUTO:
      pass
    elif value == PT_ON:
      self.passthrough = True
    else:
      raise ValueError("illegal passthrough policy mode")
    if self.debug:
      print(f"passthrough policy: {value}")
    self._pt_policy = value

  @property
  def passthrough(self) -> bool:
    """ query passthrough mode """

    # we can only query passthrough-mode if we are not in passthrough-mode,
    # so we keep track of it ourselves
    return self._passthrough

  @passthrough.setter
  def passthrough(self, mode: bool) -> None:
    """ set/reset passthrough mode """

    # set passthrough-mode (requires single-connection)
    if mode and not self._passthrough:

      # enter passthrough-mode
      reply = self.send_atcmd(
        f'AT+CIPMODE=1',filter="^OK")
      if not reply:
        raise RuntimeError("Could not enter passthrough-mode")

      reply = self.send_atcmd(
        f'AT+TRANSINTVL=0',filter="^OK")
      if not reply:
        raise RuntimeError("Could not set transfer-interval")

      # activate passthrough-mode
      reply = self.send_atcmd("AT+CIPSEND",set_busy=False) # init passthrough
      if "ERROR" in reply:
        if self.debug:
          print(f"send failed with ERROR")
        self.busy = False
        raise RuntimeError("Could not enter passthrough-mode")
      success, _ = self.read_atmsg(passive=True,read_until='>')
      if not success:
        raise RuntimeError("Could not enter passthrough-mode")
      if self.debug:
        print(f"activated passthrough-mode")

      self._passthrough = True

    # leave passthrough-mode
    elif not mode and self._passthrough:
      # send magic +++ to leave data mode
      time.sleep(0.021)          # wait more than 20ms
      reply = self.write("+++")
      time.sleep(0.021)          # wait more than 20ms
      time.sleep(1)              # wait at least one second

      # leave passthrough-mode
      reply = self.send_atcmd(
        f'AT+CIPMODE=0',filter="^OK")
      if not reply:
        raise RuntimeError("Could not leave passthrough-mode")
      self._passthrough = False
