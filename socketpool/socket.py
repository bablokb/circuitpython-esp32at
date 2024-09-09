# -------------------------------------------------------------------------
# Class Socket. This class tries to mimic the class socketpool.Socket
# of core CircuitPython.
#
# Don't use this class directly, use socketpool.socket() instead.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class Socket. """

from .socketpool import SocketPool
from .implementation import _Implementation

class Socket:
  """ Class Socket """

  # pylint: disable=redefined-builtin,too-many-arguments,unused-argument
  def __init__(
    self,
    socket_pool: SocketPool,
    family: int = SocketPool.AF_INET,
    type: int = SocketPool.SOCK_STREAM,
    proto: int = 0,
    fileno: Optional[int] = None,
    ):
    """ Constructor.

    Since the AT commandset only provides connections, not sockets, we
    have no explicit AT-call at this stage.
    """

    if family != SocketPool.AF_INET:
      raise ValueError("Only AF_INET family supported")
    self._impl = _Implementation()
    self._socket_pool = socket_pool
    self._radio = self._socket_pool._radio
    self._sock_type = type
    self._use_ssl = False
    self._link_id = None
    #self.settimeout(0)
    if self._sock_type == SocketPool.SOCK_DGRAM:
      self._conn_type = "UDP"
    elif self._use_ssl:
      self._conn_type = "SSL"
    else:
      self._conn_type = "TCP"

  @property
  def use_ssl(self) -> bool:
    """ Socket uses SSL-encryption (internal, not part of the core-API) """
    return self._use_ssl

  @use_ssl.setter
  def use_ssl(self,value: bool) -> None:
    """ set SSL-encryption  (internal, not part of the core-API) """
    self._use_ssl = value and self._sock_type != SocketPool.SOCK_DGRAM

  # pylint: disable=undefined-variable
  def __enter__(self) -> Socket:
    """ No-op used by Context Managers. """
    return self

  # pylint: disable=undefined-variable
  def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    self.close()

  # pylint: disable=undefined-variable
  def accept(self) -> Tuple[Socket, Tuple[str, int]]:
    """
    Accept a connection on a listening socket of type SOCK_STREAM,
    creating a new socket of type SOCK_STREAM. Returns a tuple of
    (new_socket, remote_address)
    """
    raise NotImplementedError("socket.accept(): not implemented yet!")

  def bind(self, address: Tuple[str, int]) -> None:
    """ Bind a socket to an address

    Parameters:

      address (tuple) – tuple of (remote_address, remote_port)
    """
    raise NotImplementedError("socket.bind(): not implemented yet!")

  def connect(self,address: Tuple[str, int]) -> None:
    """ Connect a socket to a remote address

    Parameters:

      address (tuple) – tuple of (remote_address, remote_port)
    """
    self._link_id = self._impl.start_connection(
      address[0],address[1],self._conn_type)

  def close(self) -> None:
    """ Closes this Socket and makes its resources available to its
    SocketPool.
    """
    self._impl.close_connection(self._link_id)

  def listen(self,backlog: int) -> None:
    """ Set socket to listen for incoming connections

    Parameters:

      backlog (~int) – length of backlog queue for waiting connetions
    """
    raise NotImplementedError("socket.listen(): not implemented yet!")

  def recvfrom_into(
    self,
    buffer: circuitpython_typing.WriteableBuffer) -> Tuple[int, Tuple[str, int]]:
    """ Reads some bytes from a remote address.

    Returns a tuple containing * the number of bytes received into the
    given buffer * a remote_address, which is a tuple of ip address
    and port number

    Parameters:
        buffer (object) – buffer to read into
    """
    raise NotImplementedError("socket.recvfrom_into(): not implemented yet!")

  def recv_into(
    self,
    buffer: circuitpython_typing.WriteableBuffer, bufsize: int) -> int:
    """
    Reads some bytes from the connected remote address, writing into
    the provided buffer. If bufsize <= len(buffer) is given, a maximum
    of bufsize bytes will be read into the buffer. If no valid value
    is given for bufsize, the default is the length of the given
    buffer.

    Suits sockets of type SOCK_STREAM.
    Returns an int of number of bytes read.

    Parameters:

      buffer (bytearray) – buffer to receive into
      bufsize (int) – optionally, a maximum number of bytes to read.
    """
    raise NotImplementedError("socket.recv_into(): not implemented yet!")

  # pylint: disable=redefined-builtin
  def send(self, bytes: circuitpython_typing.ReadableBuffer) -> int:
    """
    Send some bytes to the connected remote address. Suits sockets of
    type SOCK_STREAM

    Parameters:
      bytes (bytes) – some bytes to send
    """
    raise NotImplementedError("socket.send(): not implemented yet!")

  def sendall(self, bytes: circuitpython_typing.ReadableBuffer) -> None:
    """ Send some bytes to the connected remote address. Suits sockets
    of type SOCK_STREAM

    This calls send() repeatedly until all the data is sent or an
    error occurs. If an error occurs, it’s impossible to tell how much
    data has been sent.

    Parameters:
        bytes (bytes) – some bytes to send
    """
    raise NotImplementedError("socket.sendall(): not implemented yet!")

  def sendto(self,
             bytes: circuitpython_typing.ReadableBuffer,
             address: Tuple[str, int]) -> int:
    """
    Send some bytes to a specific address. Suits sockets of type SOCK_DGRAM

    Parameters:
      bytes (bytes) – some bytes to send
      address (tuple) – tuple of (remote_address, remote_port)
    """
    if self._conn_type != "UDP":
      raise RuntimeError("wrong socket-type (not UDP)")

    if self._link_id == None:
      # contrary to the documentation, we do need a connection
      self.connect(address)
    self._impl.send(bytes,self._link_id)
    return len(bytes)

  def setblocking(self,flag: bool) -> Union[int, None]:
    """ Set the blocking behaviour of this socket.

    Parameters:

      flag (~bool) – False means non-blocking, True means block
      indefinitely.
    """
    raise NotImplementedError("socket.setblocking(): not implemented yet!")

  def setsockopt(self, level: int, optname: int, value: int) -> None:
    """ Sets socket options """
    raise NotImplementedError("socket.setsockopt(): not implemented yet!")

  def settimeout(self,value: int) -> None:
    """ Set the timeout value for this socket.

    Parameters:

      value (int) – timeout in seconds. 0 means non-blocking. None
      means block indefinitely.
    """
    raise NotImplementedError("socket.settimeout(): not implemented yet!")

  @property
  def type(self) -> int:
    """ Read-only access to the socket type """
    return self._socket_type
