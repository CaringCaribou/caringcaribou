## Troubleshooting

This page aims to present solutions to some common errors.

### Missing default configuration file for python-can
#### Symptoms
Running `cc.py` and specifying an interface via `-i` gives the following error:
`NotImplementedError: Invalid CAN Bus Type - None`

#### Solution
Python-can requires an interface/channel configuration file.

Create a `.canrc` file in your home directory with the following content:
```
[default]
interface = socketcan
channel = can0
```

This step is also described in https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/howtoinstall.md#configure

Documentation for python-can: https://python-can.readthedocs.io/en/master/configuration.html

### Inactive CAN interface
#### Symptoms
Running a module with a channel specified through `-c` gives the following error:
`IOError: [Errno 19] No such device. This might be caused by an invalid or inactive CAN interface.`

#### Solution
Activate your CAN interface - this needs to be done after each reboot of your system.

For physical interfaces (note: bitrates may vary depending on the CAN bus you are connected to):
```
echo "Setting up CAN interface can0"
sudo modprobe can
sudo ip link set can0 up type can bitrate 500000
```

For virtual interfaces:
```
echo "Setting up virtual CAN interface vcan0"
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up
```

### Missing python-can
#### Symptoms
Running `cc.py` gives the following error message:
```
Traceback (most recent call last):
  File "cc.py", line 5, in <module>
    import can
ImportError: No module named can
```

#### Solution
Install python-can. This can be done by running `pip install python-can`

### Deprecated command line arguments
#### Symptoms
Running a module specifying a channel as an interface using `-i` (e.g. `cc.py -i can0`) gives the following error:
`can.exceptions.CanInterfaceNotImplementedError: Unknown interface type "can0"`

### Solutions
Use the updated command line flags to specify the `interface` using `-i`, the `channel` using `-c` and the bitrate `-b` (e.g. `cc.py -i socketcan -c can0 -b 500000`).
