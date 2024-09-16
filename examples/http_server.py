# -------------------------------------------------------------------------
# http_server.py: setup and run a simple http-server.
#
# The server code is from examples/httpserver_methods.py of the repo
# https://github.com/adafruit/Adafruit_CircuitPython_HTTPServer.
#
# This program needs the adafruit_httpserver module.
#
# You need to create a secrets.py file (have a look at sec_template.py).
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-esp32at
#
# -------------------------------------------------------------------------

import time
import board
import busio
import wifi
import socketpool

from pins import *

DEBUG  = False

# Get wifi details and more from a secrets.py file
try:
  from secrets import secrets
except ImportError:
  print("WiFi secrets are kept in secrets.py, please add them there!")
  raise

# --- test if we don't have native wifi   ------------------------------------

if hasattr(wifi,"at_version"):
  uart = busio.UART(PIN_TX, PIN_RX, baudrate=115200, receiver_buffer_size=2048)
  wifi.init(uart,debug=DEBUG,reset_pin=PIN_RST)
  if not wifi.at_version:
    raise RuntimeError("could not setup co-processor")
  print(wifi.at_version)
  wifi.radio.start_station()

# --- set TX power if requested   --------------------------------------------

print(f"TX power: {wifi.radio.tx_power}")
if 'tx_power' in secrets:
  print(f"changing TX power to {secrets['tx_power']}")
  wifi.radio.tx_power = secrets['tx_power']
  print(f"TX power: {wifi.radio.tx_power}")

# --- connect to AP   --------------------------------------------------------

print(f"connecting to AP {secrets['ssid']} ...")
if 'timeout' in secrets:
  timeout = secrets['timeout']
else:
  timeout = 5
if 'retries' in secrets:
  retries = secrets['retries']
else:
  retries = 3

state = wifi.radio.connected
print(f"  connected: {state}")
if not state:
  # ESP32xx defaults to automatic reconnection to old AP. It will
  # disconnect first if already connected to an AP.
  #
  # Note: you can pass retries to wifi.radio.connect, but that is not portable
  for _ in range(retries):
    try:
      wifi.radio.connect(secrets['ssid'],
                         secrets['password'],
                         timeout = timeout
                         )
      break
    except ConnectionError as ex:
      print(f"{ex}")
  print(f"  connected: {wifi.radio.connected}")

# --- run server   -----------------------------------------------------------

# SPDX-FileCopyrightText: 2023 Michał Pokusa
#
# SPDX-License-Identifier: Unlicense

from adafruit_httpserver import (
  Server, Request, JSONResponse, GET, POST, PUT, DELETE
)

pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, debug=True)

objects = [
    {"id": 1, "name": "Object 1"},
]

@server.route("/api", [GET, POST, PUT, DELETE], append_slash=True)
def api(request: Request):
  """
  Performs different operations depending on the HTTP method.
  """

  # Get objects
  if request.method == GET:
    return JSONResponse(request, objects)

  # Upload or update objects
  if request.method in [POST, PUT]:
    uploaded_object = request.json()

    # Find object with same ID
    for i, obj in enumerate(objects):
      if obj["id"] == uploaded_object["id"]:
        objects[i] = uploaded_object
        return JSONResponse(
          request, {"message": "Object updated", "object": uploaded_object}
          )
    # If not found, add it
    objects.append(uploaded_object)
    return JSONResponse(
      request, {"message": "Object added", "object": uploaded_object}
      )

  # Delete objects
  if request.method == DELETE:
    deleted_object = request.json()

    # Find object with same ID
    for i, obj in enumerate(objects):
      if obj["id"] == deleted_object["id"]:
        del objects[i]
        return JSONResponse(
          request, {"message": "Object deleted", "object": deleted_object}
          )

    # If not found, return error
    return JSONResponse(
      request, {"message": "Object not found", "object": deleted_object}
      )

  # If we get here, something went wrong
  return JSONResponse(request, {"message": "Something went wrong"})

server.serve_forever(str(wifi.radio.ipv4_address))

# curl -X POST http://ip/api -H "Content-Type: application/json" -d '{"id": 2, "name":"Object 2"}'

# curl -X PUT http://ip/api -H "Content-Type: application/json" -d '{"id": 3, "name":"Object 3"}'

# curl -X DELETE http://ip/api -H "Content-Type: application/json" -d '{"id": 3}'
