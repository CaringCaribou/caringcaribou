## How to use
The best way to understand how to use Caring Caribou is by envoking cc.py's help menu:
    
    python cc.py -h

More information on the different modules are available here:
+ [dcm-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/dcm.md)
+ [xcp-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/xcp.md)
+ [send-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/send.md)
+ [listener-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/listener.md)

### Example use
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
#### Xcp discovery
Enough with diagnostics, let's investigate xcp in more or less the same way

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








