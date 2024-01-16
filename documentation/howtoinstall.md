## How to install

### Work in progress: python package, setup.py

Currently refactoring to implement proper Python packaging.

Install the tool along with dependencies (python-can) with: `python setup.py install`.

You still need to configure your CAN interface per the instructions below.

Package installation tested on:

- [X] Python 3.10
- [ ] Python 3.6 - 3.9
- [X] Python 2.7

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
The contents of this file might e.g. be:

    [default]
    interface = socketcan
    channel = can0

##### Test it
Run the following command:

    cc.py dump

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

> NOTE! The installation procedure was more complex earlier - if you are using an older Raspbian, try looking into older versions of this howto.
> Regarding HW, [this](https://harrisonsand.com/can-on-the-raspberry-pi/) blogpost details a couple of interesting alternatives

#### USB-to-CAN
##### Raspbian
1. Download and flash latest raspbian image to SD card.
We used ```http://downloads.raspberrypi.org/raspbian/images/raspbian-2017-07-05/```
2. Update, upgrade & reboot

```
sudo apt-get update
sudo apt-get upgrade
sudo reboot
```

##### Kernel modules
1. Enable kernel module for spi by;  
    1. either using the Raspberry Pi Configuration tool, available from the Raspbian desktop
    2. or editing ```/boot/config.txt``` and adding ```dtparam=spi=on```
2. Enable kernel module for the mcp2515 chipset (CAN controller) on piCAN by adding ```dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25``` to ```/boot/config.txt```
3. Add ```dtoverlay=spi-bcm2835-overlay``` to ```/boot/config.txt```, because everyone says it's the right thing to do

```
sudo reboot
```

##### Bring up the interface
Configure CAN interface and bring it up
```sudo ip link set can0 up type can bitrate 500000```

#### Python-Can
See instructions [above](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/howtoinstall.md#python-can) in the Linux guide
