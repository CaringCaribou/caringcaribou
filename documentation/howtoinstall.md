## How to install

### Linux
The setup consists of two steps. First we need to get the USB-to-Can device working and secondly configure Python-Can
for the device.

#### USB-to-Can Setup
1. Install a reasonably modern Linux dist (with a kernel >= 3.4) e.g. latest Ubuntu.
Tested with Ubuntu 14.04 LTS, Ubuntu 16.04 LTS and Ubuntu 17.04.
2. Plug in the USB-to-Can device (we use [PEAK PCAN-USB](http://www.peak-system.com/PCAN-USB.199.0.html))
3. Load the CAN module (needs to be done after each reboot):

   ```
   sudo modprobe can
   ```
4. Set up the can device (needs to be done after each reboot). 

   ```
   sudo ip link set can0 up type can bitrate 500000 
   ```
   *Note:* The bit rate may differ between different CAN buses.
5. ```can0``` will now display as a normal network interface

#### Python-Can
Tested with python-can 1.5.2 and 2.0.0a2.

1. Install [pip](https://pypi.python.org/pypi/pip) (package management system for python - often installed by default)
2. Install python-can by running:

        pip install python-can

3. Verify that the installation worked by running python from the terminal and load the can module. 

    ```
    $ python
    Python 2.7.13 (default, Jan 19 2017, 14:48:08) 
    [GCC 6.3.0 20170118] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import can
    >>> 

    ```

##### Configure
Python-Can uses a configuration file ```~/.canrc``` to specify a CAN interface.
The contents of this file should be:

    [default]
    interface = socketcan
    channel = can0

*Note:* In case you are running an ancient version of python-can (from 2015-ish), you may need to set the interface to
`socketcan_ctypes` instead.

##### Test it
Go to the directory where Caring Caribou inun the following command:

``` python cc.py dump```

If packets are received, everything is good to go!

### Windows 7 
The simplest solution is to download
[VMware Player](https://my.vmware.com/en/web/vmware/free#desktop_end_user_computing/vmware_workstation_player/12_0)
, install a Linux distribution and to follow the Linux guide above.

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
