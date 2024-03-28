# Send
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

## Message
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

## File

```
$ caringcaribou send file -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'send'

usage: caringcaribou send file [-h] [--delay D] [--loop] filename

positional arguments:
  filename         path to file

optional arguments:
  -h, --help       show this help message and exit
  --delay D, -d D  delay between messages in seconds (overrides timestamps in
                   file)
  --loop, -l       loop message sequence (re-send over and over)
```
