## How to install

### Installing Caring Caribou python package
Install the tool along with dependencies (python-can) by running `python setup.py install`

You still need to configure your CAN interface per the instructions below.

### Linux
The setup consists of two steps. First we need to get the USB-to-Can device working and secondly configure Python-Can
for the device.

#### USB-to-Can Setup
1. Install a reasonably modern Linux dist (with a kernel >= 3.4), for example Ubuntu.
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
1. Install [pip](https://pypi.python.org/pypi/pip) (package management system for python - often installed by default)
2. Install python-can by running:

        pip install python-can

3. Verify that the installation worked by running python from the terminal and load the can module. 

    ```
    $ python
    Python 3.10.12 (main, Mar 22 2024, 16:50:05) [GCC 11.4.0] on linux
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

    caringcaribou dump

If packets are received, everything is good to go!

### Windows
The simplest solution is to use a VM hypervisor (like VMware Player or VirtualBox), install a Linux VM and then follow the Linux guide above.
