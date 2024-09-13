Examples
========

Overview
--------

This folder contains a number of examples/test-programs that excercise
the library:

  - `scan_network.py`: simple network-scanner for APs
  - `ping.py`: ping a given host by IP or hostname
  - `test_sta.py`: execute all station-relevant methods of `wifi.radio`
  - `udp_logger.py`: send CSV-data using UDP
  - `query_timeapi.py`: HTTP-GET requests (no SSL)
  - `query_openmeteo.py`: HTTPS-GET requests (i.e. with SSL)


secrets.py
----------

Create a file `secrets.py` for various definitions used from the test
programs (credentials, hostnames and so on). Copy `sec_template.py`
and adapt to your needs.


my_pins.py
----------

All examples need pin-definitions, at least for the UART-pins. Either
use the default pins from `pins.py`, or create a file `my_pins.py`
to override the defaults.
