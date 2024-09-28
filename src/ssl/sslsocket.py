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
  from typing import Union
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

    # TODO: tell socket that we want SSL
    self._socket.use_ssl = True

    # delegate methods to wrapped socket
    self.__exit__     = socket.__exit__
    self.connect      = socket.connect
    self.settimeout   = socket.settimeout
    self.accept       = socket.accept
    self.bind         = socket.bind
    self.listen       = socket.listen
    self.send         = socket.send
    self.setblocking  = socket.setblocking
    if hasattr(socket,"recv"):
      self.recv         = socket.recv
    self.close        = socket.close
    self.recv_into    = socket.recv_into

  # pylint: disable=undefined-variable
  def __enter__(self) -> SSLSocket:
    """ No-op used by Context Managers. """
    return self
