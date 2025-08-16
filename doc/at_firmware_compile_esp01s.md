Compile AT Firmware for ESP-01S
===============================

Introduction
------------

Espressif does not support the ESP8266 anymore in the master-branch of
the project repo, but it *does* update the v2.3.0.0_esp8266 branch
once in while. Therefore it can be useful to compile an up to date
firmware even for old devices. Note that the branch-name might change
in case Espressif decides to change the supported version number.

This document contains simple to use instructions for compiling your
own firmware. You need nothing except a Github-account and about a
quarter of an hour.

The simplest way is to use Github codespaces, since this does not
change anything on your PC. Github provides 60 hours of free codespace
runtime each month. Once created, you can either keep the codespace or
just delete it. After a certain time, unused codespaces are stopped
automatically so they don't eat up the runtime-budget. They are also
deleted if unsused too long (but you are prompted).  All in all
codespaces are perfect for small development tasks that nevertheless
require the installation of a lot of software.


Steps
-----

  1. Fork the repo <https://github.com/espressif/esp-at>
  2. Open your fork. Create a branch from release/v2.3.0.0_esp8266:
     push "Branches" right to "master" and then the green button
     top right "New branch". Be sure to select the correct source (repo
     and branch).
  3. Checkout the branch into a codespace. From the main page of your
     fork, use the navigation
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
  5. `sudo apt-get -y install flex gperf`
  6. `./build.py build`<br>
     Choose platform (PLATFORM_ESP8266), module (ESP8266_1MB) and
     silence mode (0).<br>
     Note that this command will fail ("idf.py build failed"), but it
     will install ESP-IDF which we need for the following steps.
  7. `python -m pip install --user -r esp-idf/requirements.txt`<br>
  8. Manually edit (navigate using the tree on the left):
     `components/customized_partitions/raw_data/factory_param/factory_param_data.csv`
     to change UART-pins to 1,3 and to change the default country-code.
     The relevant module is labeled "PLATFORM_ESP8266,ESP8266_1MB".
     The last six numbers should be `1,3,-1,-1,-1,-1` instead of `15,13,3,1,5,-1`.
     I also change the description field (third field) to reflect the changes.<br>
  9. Optional: Add, commit and push this file to reuse it for later builds.
 10. Run `esp-idf/install.sh` to install the toolchain.
 11. Run `. esp-idf/export.sh` to configure the environment. You have to repeat
     this step (only this step) every time you open a new terminal.
 12. Install some additional packages. Needs to run once after the
     environment has been configured:<br>
     `python -m pip install pyyaml xlrd`
 13. `./build.py build`
 14. The newly generated firmware is in `build/factory/factory_ESP8266_1MB.bin`.
     To download, navigate on the left to the file, right click and
     choose 'Download...'
 15. Install as documented for the standard firmware.
 16. Stop codespace (use <https://github.com/codespaces>) and/or
 17. Delete codespace (also available with <https://github.com/codespaces>)


Flashing the Firmware
---------------------

It is important to set the flash-mode correctly for your device. Not every
ESP-01S on the market will support all modes. I had to use the slowest
option "dout" to make the device work:

    esptool.py --chip auto -p /dev/ttyUSB0 --baud 115200 \
       --before default_reset --after hard_reset \
          write_flash -z --flash_mode dout --flash_freq 80m 0x0 \
             /path/to/factory_ESP8266_1MB.bin

Maybe you also need to set the flash-frequency to to 40m.


Testing
-------

Start your favorite serial terminal with baudrate of 115200 and test
the version:

    miniterm --eol CRLF /dev/ttyUSB0 115200
    --- Miniterm on /dev/ttyUSB0  115200,8,N,1 ---
    --- Quit: Ctrl+] | Menu: Ctrl+T | Help: Ctrl+T followed by Ctrl+H ---
    AT
    
    OK
    AT+GMR
    AT version:2.2.2.0-dev(b65f53f - ESP8266 - Jul  5 2024 06:59:26)
    SDK version:v3.4-84-ge19ff9af
    compile time(eee9fcc2):Oct 22 2024 11:30:08
    Bin version:2.2.1(ESP8266_1MB)
    
    OK
