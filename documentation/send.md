# Send
````
>./cc.py send -h

-------------------
CARING CARIBOU v0.1
-------------------

Loaded module 'send'

usage: cc.py send [-h] [--delay DELAY] msg [msg ...]

Raw message transmission module for CaringCaribou

positional arguments:
 msg                   Message on format ARB_ID#DATA where ARB_ID is
                       interpreted as hex if it starts with 0x and decimal
                       otherwise. DATA consists of 1-8 bytes, written in hex.

optional arguments:
 -h, --help            show this help message and exit
 --delay DELAY, -d DELAY
                       Delay between messages in seconds

Example usage:
 cc.py send 0x7a0#c0.ff.ee.00.11.22.33.44
 cc.py send -d 0.5 123#de.ad.be.ef 124#01.23.45
 ```
