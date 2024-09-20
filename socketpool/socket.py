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

    # state variables for the receiver
    self._recv_size = 0
    self._recv_read = 0

    # state variables for the server
    self._is_server_socket =  False

  @property
  def use_ssl(self) -> bool:
    """ Socket uses SSL-encryption (internal, not part of the core-API) """
    return self._use_ssl

  @use_ssl.setter
  def use_ssl(self,value: bool) -> None:
    """ set SSL-encryption  (internal, not part of the core-API) """
    self._use_ssl = value and self._sock_type != SocketPool.SOCK_DGRAM
    if self._use_ssl:
      self._conn_type = "SSL"

  # pylint: disable=undefined-variable
  def __enter__(self) -> Socket:
    """ No-op used by Context Managers. """
    return self

  # pylint: disable=undefined-variable
  def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    self.close()

  def _get_conn_info(self) -> Tuple[str,int]:
    """ get connection info of socket """

    # Note: this will lock AT
    self._recv_size,host,port = self._impl.get_recv_size(self._link_id)
    self._recv_read = 0
    #print(f"=====> _get_conn_info({host=})")
    #print(f"=====> _get_conn_info({port=})")
    #print(f"=====> _get_conn_info({self._recv_size=})")
    #print(f"=====> _get_conn_info({self._recv_read=})")
    return (host,port)

  # pylint: disable=undefined-variable
  def accept(self) -> Tuple[Socket, Tuple[str, int]]:
    """
    Accept a connection on a listening socket of type SOCK_STREAM,
    creating a new socket of type SOCK_STREAM. Returns a tuple of
    (new_socket, remote_address)
    """
    # no client: throw exception
    link_id = self._impl.check_for_client()
    client_socket = Socket(self._socket_pool)
    client_socket._link_id = link_id
    address = client_socket._get_conn_info()
    return (client_socket,address)

  def bind(self, address: Tuple[str, int]) -> None:
    """ Bind a socket to an address

    Parameters:

      address (tuple) – tuple of (remote_address, remote_port)
    """
    self._impl.multi_connections = True # required by server
    self._impl.start_server(address[1],self._conn_type)
    self._is_server_socket = True

  def connect(self,address: Tuple[str, int]) -> None:
    """ Connect a socket to a remote address

    Parameters:

      address (tuple) – tuple of (remote_address, remote_port)
    """
    self._link_id = self._impl.start_connection(
      address[0],address[1],self._conn_type)

    # reset receiver after connect
    self._recv_size = 0
    self._recv_read = 0

  def close(self) -> None:
    """ Closes this Socket and makes its resources available to its
    SocketPool.
    """
    if self._is_server_socket:
      self._impl.stop_server()
    else:
      self._impl.close_connection(self._link_id)
      self._link_id = None

  def listen(self,backlog: int) -> None:
    """ Set socket to listen for incoming connections

    Parameters:

      backlog (int) – length of backlog queue for waiting connetions
    """

    # this is not implemented by the AT command set, so just ignore
    return

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
    buffer: circuitpython_typing.WriteableBuffer, bufsize: int = 0) -> int:
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

    #print(f"=====> recv_into({bufsize=})")
    if not 0 <= bufsize <= len(buffer):
      raise ValueError("bufsize must be 0 to len(buffer)")
    bytes_to_read = bufsize if bufsize else len(buffer)
    #print(f"=====> recv_into: {bytes_to_read=}")

    # if we don't know the data-size, get it (this will lock AT)
    if not self._recv_size or self._recv_read == self._recv_size:
      self._recv_size,_,_ = self._impl.get_recv_size(self._link_id)
      self._recv_read = 0
      #print(f"=====> recv_into: {self._recv_size=}, {self._recv_read=}")

    # read at most bytes_to_read from socket
    n = self._impl.read(buffer,
                        min(bytes_to_read,self._recv_size-self._recv_read))
    self._recv_read += n
    #print(f"=====> recv_into: {buffer=}, {n=}")
    #print(f"=====> recv_into: {self._recv_size=}, {self._recv_read=}")
    if self._recv_read == self._recv_size:
      self._impl.lock = False
    return n

  # pylint: disable=redefined-builtin
  def send(self, bytes: circuitpython_typing.ReadableBuffer) -> int:
    """
    Send some bytes to the connected remote address. Suits sockets of
    type SOCK_STREAM

    Parameters:
      bytes (bytes) – some bytes to send
    """
    if self._link_id == None:
      raise RuntimeError("socket is not connected")
    self._impl.send(bytes,self._link_id)
    return len(bytes)

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

      flag (bool) – False means non-blocking, True means block
      indefinitely.
    """

    # this is not implemented by the AT command set, so just ignore
    return

  def setsockopt(self, level: int, optname: int, value: int) -> None:
    """ Sets socket options """

    # this is not implemented by the AT command set, so just ignore
    return

  def settimeout(self,value: int) -> None:
    """ Set the timeout value for this socket.

    Parameters:

      value (int) – timeout in seconds. 0 means non-blocking. None
      means block indefinitely.

    """
    # tweak for adafruit_httpserver which tries to set the timeout
    # after we have pending data
    try:
      if self._is_server_socket:
        if value is None:
          value = 0
        self._impl.set_server_timeout(value)
      else:
        self._impl.set_timeout(value,self._link_id)
    except LockError:
      pass

  @property
  def type(self) -> int:
    """ Read-only access to the socket type """
    return self._socket_type
