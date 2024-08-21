# Send
```
$ caringcaribou send -h

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'send'

usage: caringcaribou send [-h] {message,file} ...

Raw message transmission module for CaringCaribou.
Messages can be passed as command line arguments or through a file.

positional arguments:
  {message,file}

options:
  -h, --help      show this help message and exit

Example usage:
  caringcaribou send message 0x7a0#c0.ff.ee.00.11.22.33.44
  caringcaribou send message -d 0.5 123#de.ad.be.ef 124#01.23.45
  caringcaribou send message -p 0x100#11 0x100#22.33
  caringcaribou send file can_dump.txt
  caringcaribou send file -d 0.2 can_dump.txt
```

## Message
```
$ caringcaribou send message -h

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'send'

usage: caringcaribou send message [-h] [--delay D] [--loop] [--pad] msg [msg ...]

positional arguments:
  msg              message on format ARB_ID#DATA where ARB_ID is interpreted as hex if it starts with 0x and decimal otherwise. DATA consists of 1-8 bytes written in hex and separated by dots.

options:
  -h, --help       show this help message and exit
  --delay D, -d D  delay between messages in seconds
  --loop, -l       loop message sequence (re-send over and over)
  --pad, -p        automatically pad messages to 8 bytes length
```

Example of __sending a message with arbitration ID `0x07e0` and payload `c0 ff ee`, including padding, in a loop with a one second delay:__
```
$ caringcaribou send message --pad -d 1 -l 0x07e0#c0.ff.ee

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'send'

Parsing messages
  1 messages parsed
Sending messages
  Arb_id: 0x000007e0, data: c0.ff.ee.00.00.00.00.00
  Arb_id: 0x000007e0, data: c0.ff.ee.00.00.00.00.00
  Arb_id: 0x000007e0, data: c0.ff.ee.00.00.00.00.00
  Arb_id: 0x000007e0, data: c0.ff.ee.00.00.00.00.00
  Arb_id: 0x000007e0, data: c0.ff.ee.00.00.00.00.00
  Arb_id: 0x000007e0, data: c0.ff.ee.00.00.00.00.00
  Arb_id: 0x000007e0, data: c0.ff.ee.00.00.00.00.00
```


## File
```
$ caringcaribou send file -h

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'send'

usage: caringcaribou send file [-h] [--delay D] [--loop] filename

positional arguments:
  filename         path to file

options:
  -h, --help       show this help message and exit
  --delay D, -d D  delay between messages in seconds (overrides timestamps in file)
  --loop, -l       loop message sequence (re-send over and over)
```
The messages in the source file need to be saved in `candump` format (this can be done using the `dump` module with the `-c` option).

Example of __sending messages in a loop from the file `output_filtered2.txt` with a one second delay__
```
$ caringcaribou send file -d 1 -l output_filtered2.txt

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'send'

Parsing messages
  98 messages parsed
Sending messages
  Arb_id: 0x000000a7, data: a7.18.5d.74.fd.45.17.1d
  Arb_id: 0x000000a7, data: 77.19.5d.74.fd.45.17.1d
  Arb_id: 0x000000a7, data: 71.1a.5d.74.fd.45.17.1d
  Arb_id: 0x000000a7, data: 1f.1b.5d.74.fd.45.17.1d
  Arb_id: 0x000000a7, data: a0.1c.5d.74.fd.45.17.1d
  ...
```
