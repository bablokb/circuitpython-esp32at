Compile AT Firmware
===================

Introduction
------------

Compiling your own AT firmware is useful to

  - change the default country and wifi-channels
  - change the number of parallel connections
  - tweak firmware size and functionality
  - add certificates

There are many ways to build an individual firmware, see e.g.
<https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/Compile_and_Develop/index.html>
for details.

The simplest way is to use Github codespaces, since this does not
change anything on your PC and only takes about a quarter of an
hour. The following example assumes you want to create a firmware with
10 instead of 5 parallel connections for an ESP32C3.

Note that Github provides 60 hours of free codespace runtime each
month. Once created, you can either keep the codespace or just delete
it. After a certain time, unused codespaces are stopped automatically
so they don't eat up the runtime-budget. They are also deleted if
unsused too long (but you are prompted).  All in all codespaces are
perfect for small development tasks that nevertheless require the
installation of a lot of software.


Steps
-----

  1. Fork the repo <https://github.com/espressif/esp-at>
  2. Create a branch from release/4.1.0.0 (or what ever you need)
  3. Checkout the branch into a codespace. Use the navigation
     - "<> Code" (green button)
     - select the right tab 'Codespaces'
     - choose '...' to the right of the '+'
     - choose '+ New with options...'
     - select your branch
     - push green "create codespace" button
     - wait until your codespace is created and the browser shows the
       Visual Studio Code environment. A terminal is created automatically
       (this might take a few moments). Once the terminal is ready, execute
       the following commands.
  4. `sudo apt-get -y update`
  5. `./build.py install`<br>
     Choose the platform (`ESP32C3`) and the module (`MINI-1`).
  6. `./build.py menuconfig`
  7. Component Config --> AT --> AT socket maximum connection number --> 10
  8. Q (Quit) Y (yes to save?)
  9. Check the difference to the default:<br>
     `diff -ubB sdkconfig.old sdkconfig | grep MAX_CONN`<br>
     `-CONFIG_AT_SOCKET_MAX_CONN_NUM=5`<br>
     `+CONFIG_AT_SOCKET_MAX_CONN_NUM=10`
 10. Manually edit (navigate using the tree on the left):
     `components/customized_partitions/raw_data/factory_param/factory_param_data.csv`
     e.g. to change UART-pins or the default country-code.
 11. Optional: Add, commit and push this file to reuse it for later builds.
 12. `./build.py build`
 13. The newly generated firmware is in `build/factory/factory_MINI-1.bin`.
     To download, navigate using the tree on the left to the file,
     right click and choose 'Download...'
 14. Install as documented for the standard firmware:
     <https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/Get_Started/Downloading_guide.html#flash-at-firmware-into-your-device>
 15. Stop the codespace (use <https://github.com/codespaces>) and/or
 16. Delete the codespace (also available at <https://github.com/codespaces>)
