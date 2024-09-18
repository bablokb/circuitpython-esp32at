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

import wifi
import socketpool

import helpers
DEBUG  = False

# --- run server   -----------------------------------------------------------

helpers.init(DEBUG)
helpers.set_tx_power()
helpers.connect()

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
