## How to use
The best way to understand how to use Caring Caribou is to look at cc.py's help menu:
    
    python cc.py -h

or simply

    ./cc.py -h

This will list all available modules at the bottom of the output:

```
$ ./cc.py -h
usage: cc.py [-h] [-i INTERFACE] module ...

-------------------
CARING CARIBOU v0.2
\_\_    _/_/
    \__/
    (oo)\_______
    (__)\       )\/
        ||-----||
        ||     ||
-------------------

A friendly car security exploration tool

positional arguments:
  module        Name of the module to run
  ...           Arguments to module

optional arguments:
  -h, --help    show this help message and exit
  -i INTERFACE  force interface, e.g. 'can1' or 'vcan0'

available modules:
  dcm, dump, fuzzer, listener, send, test, xcp
```

So in order to see usage information for e.g. the `send` module, run

    ./cc.py send -h

which will show both module specific arguments and some usage examples:

```
$ ./cc.py send -h

-------------------
CARING CARIBOU v0.2
-------------------

Loaded module 'send'

usage: cc.py send [-h] {message,file} ...

Raw message transmission module for CaringCaribou.
Messages can be passed as command line arguments or through a file.

positional arguments:
  {message,file}

optional arguments:
  -h, --help      show this help message and exit

Example usage:
  cc.py send message 0x7a0#c0.ff.ee.00.11.22.33.44
  cc.py send message -d 0.5 123#de.ad.be.ef 124#01.23.45
  cc.py send file can_dump.txt
  cc.py send file -d 0.2 can_dump.txt
```

Any sub-commands (in this case, `message` and `file`) have their own help screen as well. Let's have a look at the `message` option:

```
$ ./cc.py send message -h

-------------------
CARING CARIBOU v0.2
-------------------

Loaded module 'send'

usage: cc.py send message [-h] [--delay D] [--loop] msg [msg ...]

positional arguments:
  msg              message on format ARB_ID#DATA where ARB_ID is interpreted
                   as hex if it starts with 0x and decimal otherwise. DATA
                   consists of 1-8 bytes written in hex and separated by dots.

optional arguments:
  -h, --help       show this help message and exit
  --delay D, -d D  delay between messages in seconds
  --loop, -l       loop message sequence (re-send over and over)
```

### Non-default interface
In order to use a non-default CAN interface for any module, you can always provide the `-i INTERFACE` flag before the module name.

For instance, in oder to send the message `c0 ff ee` with arbitration ID `0xf00` on virtual CAN bus `vcan0`, you would run

    ./cc.py -i vcan0 send message 0xf00#c0.ff.ee

More information on the different modules is available here:
+ [dcm-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/dcm.md)
+ [xcp-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/xcp.md)
+ [send-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/send.md)
+ [listener-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/listener.md)

### Virtual CAN bus
In order to communicate over CAN without access to a physical CAN bus, it is possible to use a virtual CAN bus instead. Doing this in Linux is generally as easy as running the following commands:

    sudo modprobe vcan
    sudo ip link add dev vcan0 type vcan
    sudo ip link set vcan0 up

## Example use
In this example we have connected a compatible [hardware](https://github.com/CaringCaribou/caringcaribou/blob/master/README.md#hardware-requirements) (PiCAN) to our client computer (a Raspberry Pi) and installed the software according to the [instructions](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/howtoinstall.md#raspberry-pi).

The PiCAN is then connected to a CAN bus that features one or more ECUs. Since we know very little about the target ECUs, a great start is to do some discovery. Currently three types of discovery is available; dcm discovery, xcp discovery and the listener.
#### The listener
Lets start with the listener:

```cd /<path-to-caringcaribou>/tool```

```./cc.py -h```

```./cc.py listener -h```

``` ./cc.py listener ```
(end the listener with ctrl-C)

```
Last ID: 0x002 (total found: 30)

Detected arbitration IDs:
Arb id 0x001 114 hits
Arb id 0x002 13 hits
```
On our system we found two active arbitration IDs - probably sending some important signal/measurement repeatedly. Let's investigate if diagnostics are present on some ECUs.
#### Diagnostic discovery

```./cc.py dcm -h```

```./cc.py dcm discovery -h```

```./cc.py dcm discovery -min 0x003``` (no need to do discovery on 0x001 and 0x002)

```
Loaded module 'dcm'

Starting diagnostics service discovery
Sending diagnostics Tester Present to 0x0733
Found diagnostics at arbitration ID 0x0733, reply at 0x0633

```
Great! Now we now what arbitration ID to use when we look for services and subfunctions:

```./cc.py dcm services 0x733 0x633```

This gives us that the service READ_DATA_BY_IDENTIFIER (0x22) is available. 0x22 is typically followed by a two byte parameter ID (PID). The two bytes are in positions 2 and 3 and since we want to try them all we enter both 2 and 3 into the subfunction discovery indices list

```./cc.py dcm subfunc 0x733 0x633 0x22 2 3```

```
Loading module 'dcm'

Starting DCM sub-function discovery
Probing sub-function 0x22 data ['0c', 'ab'] (found: 4)

Found sub-functions for services 0x22 (READ_DATA_BY_IDENTIFIER)

Sub-function 01 00
Sub-function 01 01
Sub-function 01 02
Sub-function 02 00

Terminated by user
```
#### XCP discovery
Enough with diagnostics, let's investigate XCP in more or less the same way

```./cc.py xcp -h```

```./cc.py xcp discovery -h```

```./cc.py xcp discovery -min 0x003``` ((no need to do discovery on 0x001 and 0x002)
```
Loaded module 'xcp'

Starting XCP discovery
Sending XCP Connect to 0x03e8 > DECODE CONNECT RESPONSE

Resource protection status
(...skipping)

COMM_MODE_BASIC
(...skipping)

Found XCP at arb ID 0x03e8, reply at 0x03e9
```
For XCP you can get more information by running

```./cc.py xcp info 0x3e8 0x3e9```

and you can try to dump parts of the memory by using

```./cc.py xcp dump 0x3e8 0x3e9 0x1f0000000 0x4800 -f bootloader.hex```








