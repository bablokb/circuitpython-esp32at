# -------------------------------------------------------------------------
# Class SSLContext. This class tries to mimic the class ssl.SSLContext
# of core CircuitPython.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

""" class SSLContext. """

import socketpool
from .sslsocket import SSLSocket

try:
  from typing import Union
except ImportError:
  pass

class SSLContext:
  """ Settings related to SSL that can be applied to a socket by
  wrapping it. This is useful to provide SSL certificates to specific
  connections rather than all of them.
  """

  def __init__(self):
    """ constructor """

  def load_cert_chain(self,certfile: str, keyfile: str) -> None:
    """ Load a private key and the corresponding certificate.

    The certfile string must be the path to a single file in PEM
    format containing the certificate as well as any number of CA
    certificates needed to establish the certificate’s
    authenticity. The keyfile string must point to a file
    containing the private key.
    """

  def load_verify_locations(self,
    cafile: Union[str, None] = None,
    capath: Union[str, None] = None,
    cadata: Union[str, None] = None) -> None:
    """
    Load a set of certification authority (CA) certificates used to
    validate other peers’ certificates.

    Parameters:

    cafile (str) – path to a file of contcatenated CA certificates in
    PEM format. Not implemented.

    capath (str) – path to a directory of CA certificate files in PEM
    format. Not implemented.

    cadata (str) – A single CA certificate in PEM format. Limitation:
    CPython allows one or more certificates, but this implementation
    is limited to one.
    """

  def set_default_verify_paths(self) -> None:
    """Load a set of default certification authority (CA) certificates."""

  @property
  def check_hostname(self) -> bool:
    """ Whether to match the peer certificate’s hostname. """
    return False

  @check_hostname.setter
  def check_hostname(self, value:bool) -> None:
    return None

  def wrap_socket(
    self,
    sock: socketpool.Socket,
    *,
    server_side: bool = False,
    server_hostname: Union[str, None] = None) -> SSLSocket:
    """
    Wraps the socket into a socket-compatible class that handles SSL
    negotiation. The socket must be of type SOCK_STREAM.
    """
