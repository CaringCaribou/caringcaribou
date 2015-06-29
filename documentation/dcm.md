# DCM
```
>./cc.py dmc -h

-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'dcm'

usage: cc.py dcm [-h] {discovery,services,subfunc,dtc} ...

Diagnostics module for CaringCaribou

positional arguments:
 {discovery,services,subfunc}

optional arguments:
 -h, --help            show this help message and exit

Example usage:
 cc.py dcm discovery
 cc.py dcm services 0x733 0x633
 cc.py dcm subfunc 0x733 0x633 0x22 2 3
 cc.py dcm dtc 0x7df 0x7e8
 ```

## Discovery
```
>./cc.py dmc discovery -h

-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'dcm'

usage: cc.py dcm discovery [-h] [-min MIN] [-max MAX]

optional arguments:
 -h, --help            show this help message and exit
 -min MIN
 -max MAX
```
## Services
````
>./cc.py dmc services -h

-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'dcm'

usage: cc.py dcm services [-h] src dst

positional arguments:
  src                  arbitration ID to transmit from
  dst                  arbitration ID to listen to

optional arguments:
 -h, --help            show this help message and exit
```
## Subfunc
```
>./cc.py dmc subfunc -h
-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'dcm'

usage: cc.py dcm subfunc [-h] [-show] src dst service i [i ...]

positional arguments:
  src                  arbitration ID to transmit from
  dst                  arbitration ID to listen to
  service              service ID (e.g. 0x22 for Read DID)
  i                    sub-function indicies

optional arguments:
 -h, --help            show this help message and exit
 -show                 show data in terminal
```
## Dtc
```
-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'dcm'

usage: cc.py dcm dtc [-h] [-clear] src dst

positional arguments:
  src         arbitration ID to transmit from
  dst         arbitration ID to listen to

optional arguments:
  -h, --help  show this help message and exit
  -clear      Clear DTC / MIL
```
