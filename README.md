# caringcaribou
A friendly car security exploration tool

## Rationale
We are lacking a security testing tool for automotive. A zero-knowledge tool that can be dropped onto any automotive network and collect information regarding what services exist and what vulnerabilities exist. This is a start.

This work was done as part of the HeavenS research project.

## Features
Currently this is just a bunch of python files, typically one per area-of-interest. In time, the idea is to build a master application that takes arguments and then imports and executes modules as required.

### CAN.Action
This is the daddy of all classes. Imported by all other modules. Abstraction for all access to the CAN bus

### Diagnostics ISO 14229
- ArbID Discovery - try to connect (02 10 01) to all possible ArbId (000-7FF) and collect valid responses (xx 7F or xx 50)
- Service Discovery - Brute force all SIDs and report any responses (anything that is not xx F7 11)
- Sub-function Discovery - Brute force engine that takes SID and an index indicating which positions to brute force as input

### XCP
- ArbId Discovery - try to connect (FF) to all possible ArbId (000-7FF) and collect all valid responses (FF or FE)
- Get Basic Information - connect and get information about XCP abilities in the target environment
- Upload - dump ECU memory (SRAM, flash and bootloader) to file 

### Listener
- ArbId listener - register all ArbIds heard on the CAN bus

## Hardware requirements
Some sort of interface towards an automotive bus that is compatible with socketCAN (http://elinux.org/CAN_Bus#CAN_Support_in_Linux).
We used a PEAK hardware called PCAN-USB

## Software requirements
python2.7
python-can
a pretty modern linux kernel
## How to install

### Linux
The setup consists of two steps. First we need to get the USB-to-Can device working and secondly configure Python-Can for the device.
#### USB-to-Can Setup
1. Install a Linux dist with a kernel >= 3.4 e.g. latest Ubuntu (we used Ubuntu 14.04 LTS)
2. Plug in the USB-to-Can device (we used [PEAK PCAN-USB](http://www.peak-system.com/PCAN-USB.199.0.html))
3. Load the CAN module:

   ```
   sudo modprobe can
   ```
4. Set up the can device:

   ```
   sudo ip link set can0 up type can bitrate <bitrate_of_CAN-Bus> 
   ```
5. ```can0``` will now display as a normal network interface


#### Python-Can
Clone/download Python-Can from [bitbucket.org/hardbyte/python-can](https://bitbucket.org/hardbyte/python-can)
##### Install
1. Install [pip](https://pypi.python.org/pypi/pip)
2. Install python-can:

   ```sudo python setup.py install```

3. Verify that the installation worked by running python from the terminal and  load the can module. 

   ```
   Python 2.7.6 (default, Mar 22 2014, 22:59:56) 
   [GCC 4.8.2] on linux2
   Type "help", "copyright", "credits" or "license" for more information.
   >>> import can
   >>> 
   ```


##### Configure
Python-Can uses a configuration file ```~/.canrc``` to specify a CAN interface.
The contents of this file should be:

    [default]
    interface = socketcan_ctypes
    channel = can0

##### Test it
Connect the USB-to-CAN device to an actual CAN-bus and run the following: 

``` python bin/canlogger.py ```

If packets are received everything is good to go!

### Windows 7 
The simplest solution is to download [VMPlayer](https://my.vmware.com/web/vmware/free#desktop_end_user_computing/vmware_player/7_0), install a Linux distribution and to follow the Linux guide above.
### Raspberry Pi
- http://www.cowfishstudios.com/blog/canned-pi-part1
- http://skpang.co.uk/catalog/pican-canbus-board-for-raspberry-pi-p-1196.html
Wireshark is up and running but python-can is currently defunct

# The target
We used an open source implementation of Autosar from ArcCore available here: http://www.arccore.com/hg **FIXME**
We used a devboard from ArcCore, called Arctic EVK-M3 - an STM32F107 based device

# Contributors
* The HeavenS project, funded by VINNOVA - http://www.vinnova.se/sv/Resultat/Projekt/Effekta/HEAVENS-HEAling-Vulnerabilities-to-ENhance-Software-Security-and-Safety/
* Christian Sandberg
* Kasper Karlsson
* Tobias Lans
* Mattias Jidhage
* Johannes Weschke
* Filip Hesslund
