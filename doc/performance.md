Notes
-----

For "normal" use-cases, the performance of the AT-interface is comparable
to the native interface. The sections below show some examples for
comparing a Pico+ESP32C3 with a Pico-W.

The first example queries the OpenMeteo weather service every minute.
The last three columns show the time necessary to send the request,
to process the response and the amount of free memory (without any
manual garbage collection). The "send-time" also includes the time
necessary to connect to the service and this is the dominant figure.

The second example is a server use-case. The requested page links to
a number of js script-files and css-files. Since browsers open many
parallel connections to the server, this example only works well with
a firmware version that supports more than five parallel connections.

Even in this scenario the performance of the AT-interface is on par
with the native performance.

One example where the native interface is much faster is when sending
UDP packets. The use-case is a high-frequency data-sampling application
that sends the data via UDP to a server (or second device). The Pico-W
can send about 1000 packets per second, whereas the AT-interface reaches
only about 100 packets per second.


Raspberry Pi Pico with ESP32C3-SuperMini
----------------------------------------

Using `examples/query_openmeteo.py` and CircuitPython 9.1.3.
(version 0.9.x)

    initializing co-processor with default uart-baudrate
    AT version:3.3.0.0(3b13d04 - ESP32C3 - May  8 2024 08:21:54)
    TX power: 15.0
    changing TX power to 15
    TX power: 15.0
    connecting to AP wlan-xxxx ...
      connected: False
      connected: True
    
    ts,T/met °C,H/met %rH,P/met hPa,WMO,Wspd km/s,Wdir °,R mm,send s,recv s,memfree
    2024-10-23T10:30,10.4,95,1034,61,7.6,360,1.4,1.384,0.646,80896
    2024-10-23T10:30,10.4,95,1034,61,7.6,360,1.4,2.716,0.642,88544
    2024-10-23T10:45,10.4,95,1034,61,7.6,357,1.4,0.487,0.648,95600
    2024-10-23T10:45,10.4,95,1034,61,7.6,357,1.4,0.466,0.638,48864
    2024-10-23T10:45,10.4,95,1034,61,7.6,357,1.4,0.491,0.642,59872
    2024-10-23T10:45,10.4,95,1034,61,7.6,357,1.4,0.485,0.644,70816
    2024-10-23T10:45,10.4,95,1034,61,7.6,357,1.4,0.471,0.644,87168
    2024-10-23T10:45,10.4,95,1034,61,7.6,357,1.4,0.519,0.639,86288
    2024-10-23T10:45,10.4,95,1034,61,7.6,357,1.4,0.480,0.644,96144
    2024-10-23T10:45,10.4,95,1034,61,7.6,357,1.4,0.490,0.632,101648


Raspberry Pi Pico W
-------------------

Using `examples/query_openmeteo.py` and CircuitPython 9.1.3.

    TX power: 15.0
    changing TX power to 15
    TX power: 15.0
    connecting to AP wlan-xxxx ...
      connected: False
      connected: True
    
    ts,T/met °C,H/met %rH,P/met hPa,WMO,Wspd km/s,Wdir °,R mm,send s,recv s,memfree
    2024-10-23T10:15,10.4,95,1034,61,7.2,0,1.4,4.089,0.015,83152
    2024-10-23T10:15,10.4,95,1034,61,7.2,0,1.4,3.989,0.015,72128
    2024-10-23T10:15,10.4,95,1034,61,7.2,0,1.4,3.987,0.014,61232
    2024-10-23T10:15,10.4,95,1034,61,7.2,0,1.4,5.000,0.015,50336
    2024-10-23T10:15,10.4,95,1034,61,7.2,0,1.4,3.486,0.016,39440
    2024-10-23T10:30,10.4,95,1034,61,7.6,360,1.4,3.492,0.015,28544
    2024-10-23T10:30,10.4,95,1034,61,7.6,360,1.4,3.994,0.014,79040
    2024-10-23T10:30,10.4,95,1034,61,7.6,360,1.4,0.234,0.014,70848
    2024-10-23T10:30,10.4,95,1034,61,7.6,360,1.4,0.491,0.015,62656
    2024-10-23T10:30,10.4,95,1034,61,7.6,360,1.4,0.491,0.015,54464


Raspberry Pi Pico with ESP32C3-SuperMini
----------------------------------------

Example with complex web-site (9 requests, 137.76kB) served by ehttpserver:

  - load-time: 19.57s (Debug-mode, no optimizations, e.g. higher baudrate)
  - load-time: 7.08s (Debug unset, baudrate=1_500_000)


Raspberry Pi Pico W
-------------------

Example with complex web-site (9 requests, 137.76kB) served by ehttpserver:

  - load-time: 10.97s

