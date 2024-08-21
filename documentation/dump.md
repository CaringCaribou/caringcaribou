# Dump
```
$ caringcaribou dump -h

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'dump'

usage: caringcaribou dump [-h] [-f F] [-c] [-s SEC] [W ...]

CAN traffic dump module for CaringCaribou

positional arguments:
  W               Arbitration ID to whitelist

options:
  -h, --help      show this help message and exit
  -f F, --file F  Write output to file F (default: stdout)
  -c              Output on candump format
  -s SEC          Print separating line after SEC silent seconds

Example usage:
  caringcaribou dump
  caringcaribou dump -s 1.0
  caringcaribou dump -f output.txt
  caringcaribou dump -c -f output.txt 0x733 0x734

```
 
Example of __dumping to file all messages available on CAN bus:__
```
$ caringcaribou dump -f output_all.txt      

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'dump'

Dumping CAN traffic (press Ctrl+C to exit)
Messages printed to file: 588
```
_After ending the work with Ctrl+C we can see content saved to the file:_
```
$ cat output_all.txt

# Caring Caribou dump file
# 2024-08-18 21:56:29.230679
# /usr/local/bin/caringcaribou dump -f output_all.txt
Timestamp: 1724010989.242758        ID: 00a7    S Rx                DL:  8    b7 fc dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010989.242766        ID: 0107    S Rx                DL:  8    00 00 fe 00 60 00 00 00     Channel: can0
Timestamp: 1724010989.242768        ID: 0209    S Rx                DL:  8    4b 06 00 00 00 00 e8 7f     Channel: can0
Timestamp: 1724010989.247718        ID: 00a8    S Rx                DL:  8    27 fd 1c 40 77 64 00 00     Channel: can0
Timestamp: 1724010989.247728        ID: 0121    S Rx                DL:  8    8c f7 ff df 2d 78 7e fe     Channel: can0
Timestamp: 1724010989.248652        ID: 0391    S Rx                DL:  8    00 00 00 00 00 00 00 07     Channel: can0
Timestamp: 1724010989.248657        ID: 0120    S Rx                DL:  8    fd 07 00 07 00 00 ff 01     Channel: can0
Timestamp: 1724010989.252734        ID: 03c7    S Rx                DL:  8    fd 40 04 00 00 40 03 00     Channel: can0
...
Timestamp: 1724010990.102891        ID: 00a7    S Rx                DL:  8    27 f2 dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010990.102916        ID: 0107    S Rx                DL:  8    00 00 fe 00 60 00 00 00     Channel: can0
Timestamp: 1724010990.102926        ID: 0209    S Rx                DL:  8    62 01 00 00 00 00 e8 7f     Channel: can0
Timestamp: 1724010990.107688        ID: 00a8    S Rx                DL:  8    0b f3 1c 40 77 64 00 00     Channel: can0
Timestamp: 1724010990.107733        ID: 0121    S Rx                DL:  8    a0 f2 ff df 2d 78 7e fe     Channel: can0
Timestamp: 1724010990.108550        ID: 0120    S Rx                DL:  8    96 02 00 07 00 00 ff 01     Channel: can0
```

Example of __dumping only messages with filtered arbitration ID 0x0a7:__
```
$ caringcaribou dump -f output_filtered.txt 0x0a7      

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'dump'

Dumping CAN traffic (press Ctrl+C to exit)
Messages printed to file: 60
```
_After ending the work with Ctrl+C we can see content saved to the file:_
```
$ cat output_filtered.txt

# Caring Caribou dump file
# 2024-08-18 21:55:38.495095
# /usr/local/bin/caringcaribou dump -f output_filtered.txt 0x0a7
Timestamp: 1724010938.508579        ID: 00a7    S Rx                DL:  8    08 fb dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010938.518590        ID: 00a7    S Rx                DL:  8    b7 fc dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010938.528363        ID: 00a7    S Rx                DL:  8    47 fd dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010938.538406        ID: 00a7    S Rx                DL:  8    cc fe dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010938.548592        ID: 00a7    S Rx                DL:  8    12 ff dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010938.558383        ID: 00a7    S Rx                DL:  8    db f0 dc 73 fd 3d f7 1c     Channel: can0
...
Timestamp: 1724010939.078372        ID: 00a7    S Rx                DL:  8    9c f4 dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010939.088447        ID: 00a7    S Rx                DL:  8    e7 f5 dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010939.098445        ID: 00a7    S Rx                DL:  8    74 f6 dc 73 fd 3d f7 1c     Channel: can0
Timestamp: 1724010939.108472        ID: 00a7    S Rx                DL:  8    fd f7 dc 73 fd 3d f7 1c     Channel: can0
```

Example of __dumping only messages with filtered arbitration ID 0x0a7 with printing separating line after 1 second of silence on the bus:__
```
$ caringcaribou dump -s 1 -f output_filtered1.txt 0x0a7      

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'dump'

Dumping CAN traffic (press Ctrl+C to exit)
Messages printed to file: 2462
```
_After ending the work with Ctrl+C we can see content saved to the file (one separating line can be spotted in the log file):_
```
$ cat output_filtered1.txt

# Caring Caribou dump file
# 2024-08-21 21:04:28.420797
# /usr/local/bin/caringcaribou dump -s 1 -f output_filtered1.txt 0x0a7
Timestamp: 1724267068.441365        ID: 00a7    S Rx                DL:  8    15 9b 5d 76 fd 65 97 1d     Channel: can0
Timestamp: 1724267068.451315        ID: 00a7    S Rx                DL:  8    aa 9c 5d 76 fd 65 97 1d     Channel: can0
Timestamp: 1724267068.461301        ID: 00a7    S Rx                DL:  8    5a 9d 5d 76 fd 65 97 1d     Channel: can0
Timestamp: 1724267068.471251        ID: 00a7    S Rx                DL:  8    d1 9e 5d 76 fd 65 97 1d     Channel: can0
...
Timestamp: 1724267079.101264        ID: 00a7    S Rx                DL:  8    57 d5 5f 76 fd a1 97 1d     Channel: can0
Timestamp: 1724267079.111264        ID: 00a7    S Rx                DL:  8    c4 d6 5f 76 fd a1 97 1d     Channel: can0
Timestamp: 1724267079.121225        ID: 00a7    S Rx                DL:  8    4d d7 5f 76 fd a1 97 1d     Channel: can0
--- Count: 1069
Timestamp: 1724267084.789399        ID: 00a7    S Rx                DL:  8    c6 d0 5f 7f fd f5 d7 1f     Channel: can0
Timestamp: 1724267084.799355        ID: 00a7    S Rx                DL:  8    4e d1 5f 7f fd f5 d7 1f     Channel: can0
Timestamp: 1724267084.809358        ID: 00a7    S Rx                DL:  8    3a d2 5f 7f fd f5 d7 1f     Channel: can0
...
Timestamp: 1724267097.789275        ID: 00a7    S Rx                DL:  8    2c d4 5f 76 fd a1 97 1d     Channel: can0
Timestamp: 1724267097.799324        ID: 00a7    S Rx                DL:  8    57 d5 5f 76 fd a1 97 1d     Channel: can0
Timestamp: 1724267097.809346        ID: 00a7    S Rx                DL:  8    c4 d6 5f 76 fd a1 97 1d     Channel: can0
Timestamp: 1724267097.819252        ID: 00a7    S Rx                DL:  8    4d d7 5f 76 fd a1 97 1d     Channel: can0
```

Example of __dumping only messages with filtered arbitration ID 0x0a7 in candump format:__
```
$ caringcaribou dump -c -f output_filtered2.txt 0x0a7

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'dump'

Dumping CAN traffic (press Ctrl+C to exit)
Messages printed to file: 98
```
_After ending the work with Ctrl+C we can see content saved to the file:_
```
$ cat output_filtered2.txt

# Caring Caribou dump file
# 2024-08-18 21:53:36.221341
# /usr/local/bin/caringcaribou dump -c -f output_filtered2.txt 0x0a7
(1724010816.236653) can0 0A7#a7185d74fd45171d
(1724010816.246754) can0 0A7#77195d74fd45171d
(1724010816.256651) can0 0A7#711a5d74fd45171d
(1724010816.266762) can0 0A7#1f1b5d74fd45171d
(1724010816.276668) can0 0A7#a01c5d74fd45171d
(1724010816.286684) can0 0A7#501d5d74fd45171d
...
(1724010817.186603) can0 0A7#ea175d74fd45171d
(1724010817.196558) can0 0A7#a7185d74fd45171d
(1724010817.206666) can0 0A7#77195d74fd45171d
(1724010817.216543) can0 0A7#711a5d74fd45171d
```

