# caringcaribou
A friendly car security exploration tool

## Rationale
We are lacking a security testing tool for automotive. A zero-knowledge tool that can be dropped onto any automotive network and collect information regarding what services exist and what vulnerabilities exist. This is a start.

This work was done as part of the HeavenS research project.

## Features and Architecture
CaringCaribou is module based with a master command (cc.py) that runs the show. The reason for this is to enable an easy drop-in architecture for new modules.

## List of Modules

### dcm.py - Diagnostics ISO 14229
- discovery - ArbID Discovery. Tries to connect (02 10 01) to all possible ArbId (000-7FF) and collect valid responses (xx 7F or xx 50)
- services - Service Discovery.Brute force all Service Id's (SID) and report any responses (anything that is not xx F7 11)
- subfunc - Sub-function Discovery. Brute force engine that takes SID and an index indicating which positions to brute force as input.

Detailed information on the [dcm-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/dcm.md).

### xcp.py - Universal Measurement and Calibration Protocol (XCP)
- discovery - ArbId Discovery. Tries to connect (FF) to all possible ArbId (000-7FF) and collect all valid responses (FF or FE)
- info - XCP Get Basic Information. Connects and gets information about XCP abilities in the target environment
- dump - XCP Upload. Used to dump ECU memory (SRAM, flash and bootloader) to file 


Detailed information on the [xcp-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/xcp.md).

### listener.py - Listener
- ArbId listener - register all ArbIds heard on the CAN bus

Detailed information on the [listener-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/listener.md).

### send.py - Send CAN packets
- Raw message transmission module, used to drive manual test cases

Detailed information on the [send-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/send.md).

### CAN.Action.py
This is the daddy of all classes. Imported by all other modules. Abstraction for all access to the CAN bus

## Hardware requirements
Some sort of interface towards an automotive bus that is compatible with socketCAN (http://elinux.org/CAN_Bus#CAN_Support_in_Linux).

## Software requirements
- python2.7
- python-can
- a pretty modern linux kernel

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
4. Set up the can device (bitrate may differ between different CAN buses):

   ```
   sudo ip link set can0 up type can bitrate 500000 
   ```
5. ```can0``` will now display as a normal network interface


#### Python-Can
Download Python-Can from [bitbucket.org/hardbyte/python-can commit 77eea796362b](https://bitbucket.org/hardbyte/python-can/get/77eea796362b.zip). 

Use other commits at your own peril.

##### Install
1. Install [pip](https://pypi.python.org/pypi/pip)
2. Install python-can by running:

        sudo python setup.py install

3. Verify that the installation worked by running python from the terminal and load the can module. 

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
#### Parts list
- Raspberry Pi model B 
- SD-card 8 GB
- piCAN-shield
- DBUS 9 male
- 2 wires

#### Helpful sites
- http://skpang.co.uk/blog/archives/1141 (piCAN shield)
- http://www.cowfishstudios.com/blog/canned-pi-part1 (Kernel modules and howto)
- http://lnxpps.de/rpie/ (Kernel modules & config)
- http://ifinterface.com/page/page3.php?langid=1 (Kernel modules)
- http://www.raspberrypi.org/forums/viewtopic.php?p=675658#p675658 (Device Tree)


#### USB-to-CAN
##### Raspian
1. Download and flash latest raspian image to SD card.
We used ```http://downloads.raspberrypi.org/raspbian/images/raspbian-2015-02-17/```
1. Update, upgrade & reboot

```
sudo apt-get update
sudo apt-get upgrade
sudo reboot
```

##### Kernel modules
1. Download kernel modules for mcp2501x that fits your kernel version. We used ifinterface and ```rpi-can-3.18.7+ (not for Raspberry 2)``` 
1. ```cd /```
1. Unpack into ```/lib``` and ```/usr``` using ```sudo tar -jxvf /path-to/<archivename>```
1. Register the new modules

```
sudo depmod -a
sudo reboot
```
###### Add modules in /etc/modules to enable them at boot

```
# /etc/modules: kernel modules to load at boot time.
#
# This file contains the names of kernel modules that should be loaded
# at boot time, one per line. Lines beginning with "#" are ignored.
# Parameters can be specified after the module name.

snd-bcm2835
spi_bcm2708

# MCP2515 configuration for PICAN module
spi-config devices=\
bus=0:cs=0:modalias=mcp2515:speed=10000000:gpioirq=25:pd=20:pds32-0=16000000:pdu32-4=0x2002:force_release

# load the module
mcp251x
```


Make sure they are not in a blacklist in ```/etc/modprobe.d/<blacklist>``` If they are - comment this entries:


```
#blacklist spi-bcm2708
#blacklist mcp251x
```
##### Enable spi in Device Tree
In /boot/config.txt, add

```
# add SPI-support for piCAN
dtparam=spi=on
```
Note: Enabling spi in the device tree was required when we performed install due to changes in how Raspberry handles devices. It will change and/or be removed with new releases.

##### Bring up the interface
11. Configure CAN interface
```sudo ip link set can0 type can bitrate 500000```

12. Bring the interface up
```sudo ip link set can0 up ```

##### Python-Can
See instructions above in the Linux guide


## How to use
The best way to understand how to use Caring Caribou is by envoking cc.py's help menu:
    
    python cc.py -h

 
## Extending the project
Create a python file with a ```module_main(args)``` function. Put it in the ```modules``` folder. CaringCaribou (cc.py) will automagically recognize it as a module and list it in the output of ```./cc.py -h```

## The target
We used an open source implementation of Autosar from ArcCore available here: http://www.arccore.com/hg **FIXME**
We used a devboard from ArcCore, called Arctic EVK-M3 - an STM32F107 based device

## Contributors
* The HeavenS project, funded by VINNOVA - http://www.vinnova.se/sv/Resultat/Projekt/Effekta/HEAVENS-HEAling-Vulnerabilities-to-ENhance-Software-Security-and-Safety/
* Christian Sandberg
* Kasper Karlsson
* Tobias Lans
* Mattias Jidhage
* Johannes Weschke
* Filip Hesslund
