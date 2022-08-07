# XCP
```
-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'xcp'

usage: cc.py xcp [-h] {discovery,info,dump} ...

XCP module for CaringCaribou

positional arguments:
 {discovery,info,dump}

optional arguments:
 -h, --help            show this help message and exit

Example usage:
 cc.py xcp discovery
 cc.py xcp info 1000 1001
 cc.py xcp dump 0x3e8 0x3e9 0x1fffb000 0x4800 -f bootloader.hex
 cc.py -p True -w True xcp unlock 0x7FC9600 0x7FC9601 Lenkung_MQB_A0_ZF_TRW CAL/PAG
 
 ```
 
## Discovery
 ```
-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'xcp'

usage: cc.py xcp discovery [-h] [-min MIN] [-max MAX]

optional arguments:
 -h, --help            show this help message and exit
 -min MIN
 -max MAX
 ```
 
## Info
 
 ```
-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'xcp'

usage: cc.py xcp info [-h] src dst

positional arguments:
  src         arbitration ID to transmit from
  dst         arbitration ID to listen to

optional arguments:
 -h, --help            show this help message and exit
 ```
 
## Dump
 
 ```
-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'xcp'

usage: cc.py xcp dump [-h] [-f F] src dst start length

positional arguments:
  src         arbitration ID to transmit from
  dst         arbitration ID to listen to
  start       start adress
  length      dump length

optional arguments:
 -h, --help            show this help message and exit
 -f F, -file F         output file
 ```

## Unlock
 
 ```
-------------------
CARING CARIBOU v0.3
-------------------

Loaded module 'xcp'

usage: cc.py xcp unlock [-h] src dst unlock_func resource

positional arguments:
  src          arbitration ID to transmit from
  dst          arbitration ID to listen to
  unlock_func  seed & key function to compute key from seed
  resource     resource to unlock: PGM, STIM, DAQ, CAL/PAG
 ```