## How to use
The best way to understand how to use Caring Caribou is to look at its help menu:
    
    caringcaribou -h

This will list all available modules at the bottom of the output:

```
$ caringcaribou -h
usage: caringcaribou [-h] [-i INTERFACE] module ...

-------------------
CARING CARIBOU v0.x
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
  dcm, doip, dump, fuzzer, listener, module_template, send, test, uds, uds_fuzz, xcp
```

So in order to see usage information for e.g. the `send` module, run

    $ caringcaribou send -h

which will show both module specific arguments and some usage examples:

```
$ caringcaribou send -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'send'

usage: caringcaribou send [-h] {message,file} ...

Raw message transmission module for CaringCaribou.
Messages can be passed as command line arguments or through a file.

positional arguments:
  {message,file}

optional arguments:
  -h, --help      show this help message and exit

Example usage:
  caringcaribou send message 0x7a0#c0.ff.ee.00.11.22.33.44
  caringcaribou send message -d 0.5 123#de.ad.be.ef 124#01.23.45
  caringcaribou send file can_dump.txt
  caringcaribou send file -d 0.2 can_dump.txt
```

Any sub-commands (in this case, `message` and `file`) have their own help screen as well. Let's have a look at the `message` option:

```
$ caringcaribou send message -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'send'

usage: caringcaribou send message [-h] [--delay D] [--loop] msg [msg ...]

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

    $ caringcaribou -i vcan0 send message 0xf00#c0.ff.ee

### Virtual CAN bus
In order to communicate over CAN without access to a physical CAN bus, it is possible to use a virtual CAN bus instead. Doing this in Linux is generally as easy as running the following commands:

    sudo modprobe vcan
    sudo ip link add dev vcan0 type vcan
    sudo ip link set vcan0 up


### Available modules

You can find more information and usage examples for each module in their respective documentation:

+ [Dump](dump.md)
+ [Send](send.md)
+ [Listener](listener.md)
+ [Fuzzer](fuzzer.md)
+ [UDS](dcm.md)
+ [UDS_fuzz](uds_fuzz.md)
+ [DoIP](doip.md)
+ [XCP](xcp.md)

## Example use
In this example we have connected a compatible [hardware](https://github.com/CaringCaribou/caringcaribou/blob/master/README.md#hardware-requirements) (PiCAN) to our client computer (a Raspberry Pi) and installed the software according to the [instructions](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/howtoinstall.md#raspberry-pi).
The PiCAN is then connected to a CAN bus that features one or more ECUs. 

Since we initially know nothing about the target ECUs, it's crucial to start with some reconnaissance. For this purpose, four main discovery types are available:

- [listener](listener.md/#Listener)
- [uds discovery](uds.md#Discovery)
- [uds services](uds.md#Services)
- [xcp discovery](xcp.md#Discovery)

Let's use all of them to see what information we can get.

We're starting with the listener.
```
$ caringcaribou listener

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'listener'

Running listener (press Ctrl+C to exit)
Last ID: 0x002 (2 unique arbitration IDs found)
```
(stop the listener with Ctrl+C)
```
Detected arbitration IDs:
Arb id 0x001 114 hits
Arb id 0x002 13 hits
```

On our system we found two active arbitration IDs: 0x001 and 0x002 - probably sending some important signal/measurement repeatedly.

Now let's investigate if diagnostics are present on some ECUs. Thanks to 'listener' results, we know that there is no need to do discovery on 0x001 and 0x002, so lets start from ID 0x003.

Start uds discovery from arbitration ID 0x003:
```
$ caringcaribou uds discovery -min 0x003

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

Sending Diagnostic Session Control to 0x07e0
  Verifying potential response from 0x07e0
    Resending 0x7e0...  Success
Found diagnostics server listening at 0x07e0, response at 0x07e8

Identified diagnostics:

+------------+------------+
| CLIENT ID  | SERVER ID  |
+------------+------------+
| 0x000007e0 | 0x000007e8 |
+------------+------------+
```

Great! Now we know the ID that the ECU uses to send responses (0x07e8) and the ID we can use to send requests (0x07e0). Let's use this knowledge to scan for available services.

```
$ caringcaribou uds services 0x7e0 0x7e8

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

Probing service 0xff (255/255): found 19
Done!

Supported service 0x01: Unknown service
Supported service 0x02: Unknown service
Supported service 0x03: Unknown service
Supported service 0x04: Unknown service
Supported service 0x04: Unknown service
Supported service 0x38: Unknown service
Supported service 0x09: Unknown service
Supported service 0x10: DIAGNOSTIC_SESSION_CONTROL
Supported service 0x11: ECU_RESET
Supported service 0x19: READ_DTC_INFORMATION
Supported service 0x22: READ_DATA_BY_IDENTIFIER
Supported service 0x23: READ_MEMORY_BY_ADDRESS
Supported service 0x27: SECURITY_ACCESS
Supported service 0x28: COMMUNICATION_CONTROL
Supported service 0x2e: WRITE_DATA_BY_IDENTIFIER
Supported service 0x2f: INPUT_OUTPUT_CONTROL_BY_IDENTIFIER
Supported service 0x31: ROUTINE_CONTROL
Supported service 0x3e: TESTER_PRESENT
Supported service 0x85: CONTROL_DTC_SETTING
```

That was a good one! Look at how many services we discovered in this ECU. That's a great start for further UDS exploration.

Enough with UDS, now let's look at another supported protocol - [XCP](xcp.md).

Just like with UDS, we can start the discovery from ID 0x003:

```
$ caringcaribou xcp discovery -min 0x003

-------------------
CARING CARIBOU v0.x
-------------------

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

    caringcaribou xcp info 0x3e8 0x3e9

and you can try to dump parts of the memory by using

    caringcaribou xcp dump 0x3e8 0x3e9 0x1f0000000 0x4800 -f bootloader.hex
