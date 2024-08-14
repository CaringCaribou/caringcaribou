# Listener
It's a mode dedicated to listening on the CAN bus and logging all detected arbitration IDs.

Opening the help menu:
```
$ caringcaribou listener -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'listener'

usage: caringcaribou listener [-h] [-r]

Passive listener module for CaringCaribou

optional arguments:
 -h, --help     show this help message and exit
 -r, --reverse  Reversed sorting of results
```

Example use:
```
$ caringcaribou listener

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'listener'

Running listener (press Ctrl+C to exit)
Last ID: 0x002 (2 unique arbitration IDs found)
```
(stop the listener with ctrl-C)
```
Detected arbitration IDs:
Arb id 0x001 114 hits
Arb id 0x002 13 hits

```
In the above example, two arbitration IDs were detected. The message with ID 0x001 was seen on the CAN bus 114 times, while the one with ID 0x002 appeared 13 times.
