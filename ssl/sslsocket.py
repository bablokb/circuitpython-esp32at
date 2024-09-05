# -------------------------------------------------------------------------
# Class SSLSocket. This class tries to mimic the class ssl.SSLSocket
# of core CircuitPython.
#
# This is currently just a wrapper for SocketPool.Socket
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class SSLSocket. """

try:
  from circuitpython_typing.socket import CircuitPythonSocketType
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

  # pylint: disable=too-many-instance-attributes
  def __init__(self, socket: CircuitPythonSocketType,
               server_side: bool = False,
               server_hostname: Union[str, None] = None) -> None:
    self._socket = socket
    self._server_side = server_side
    self._server_hostname = server_hostname

    # delegate methods to wrapped socket
    self.__exit__ = socket.__exit__
    self.connect = socket.connect
    self.settimeout = socket.settimeout
    self.send = socket.send
    self.recv = socket.recv
    self.close = socket.close
    self.recv_into = socket.recv_into

    # For sockets that come from software socketpools (like the
    # esp32api), they track the interface and socket pool. We need to
    # make sure the clones do as well
    # TODO: delete if not needed
    self._interface = getattr(socket, "_interface", None)
    self._socket_pool = getattr(socket, "_socket_pool", None)

  # pylint: disable=undefined-variable
  def __enter__(self) -> SSLSocket:
    """ No-op used by Context Managers. """
    return self

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

  def listen(self,backlog: int) -> None:
    """ Set socket to listen for incoming connections

    Parameters:

      backlog (~int) – length of backlog queue for waiting connetions
    """

  def setblocking(self,flag: bool) -> Union[int, None]:
    """ Set the blocking behaviour of this socket.

    Parameters:

      flag (~bool) – False means non-blocking, True means block
      indefinitely.
    """
