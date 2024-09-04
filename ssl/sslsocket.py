# -------------------------------------------------------------------------
# Class SSLSocket. This class tries to mimic the class ssl.SSLSocket
# of core CircuitPython.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class SSLSocket. """

try:
  import circuitpython_typing
  from typing import Union, Tuple
except ImportError:
  pass

class SSLSocket:
  """
  Implements TLS security on a subset of socketpool.Socket
  functions. Cannot be created directly. Instead, call wrap_socket on
  an existing socket object.

  Provides a subset of CPython’s ssl.SSLSocket API. It only
  implements the versions of recv that do not allocate bytes
  objects.
  """

  def __hash__(self) -> int:
    """ Returns a hash for the Socket. """

  # pylint: disable=undefined-variable
  def __enter__(self) -> SSLSocket:
    """ No-op used by Context Managers. """

  def __exit__(self, exc_type, exc_value, traceback) -> None:
    """
    Automatically closes the Socket when exiting a context. See
    Lifetime and ContextManagers for more info.
    """

  # pylint: disable=undefined-variable
  def accept(self) -> Tuple[SSLSocket, Tuple[str, int]]:
    """
    Accept a connection on a listening socket of type SOCK_STREAM,
    creating a new socket of type SOCK_STREAM. Returns a tuple of
    (new_socket, remote_address)
    """

  def bind(self, address: Tuple[str, int]) -> None:
    """ Bind a socket to an address

    Parameters:

      address (tuple) – tuple of (remote_address, remote_port)
    """

  def close(self) -> None:
    """ Closes this Socket """

  def connect(self, address: Tuple[str, int]) -> None:
    """ Connect a socket to a remote address

     Parameters:

       address (tuple) – tuple of (remote_address, remote_port)
     """

  def listen(self,backlog: int) -> None:
    """ Set socket to listen for incoming connections

    Parameters:

      backlog (~int) – length of backlog queue for waiting connetions
    """

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

  # pylint: disable=redefined-builtin
  def send(self, bytes: circuitpython_typing.ReadableBuffer) -> int:
    """
    Send some bytes to the connected remote address. Suits sockets of
    type SOCK_STREAM

    Parameters:

      bytes (~bytes) – some bytes to send
    """

  def settimeout(self, value: int) -> None:
    """ Set the timeout value for this socket.

    Parameters:

      value (~int) – timeout in seconds. 0 means non-blocking. None
      means block indefinitely.
    """

  def setblocking(self,flag: bool) -> Union[int, None]:
    """ Set the blocking behaviour of this socket.

    Parameters:

      flag (~bool) – False means non-blocking, True means block
      indefinitely.
    """
