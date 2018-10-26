# Fuzzer
````
>./cc.py fuzzer -h

-------------------
CARING CARIBOU v0.2
-------------------

Loaded module 'fuzzer'

usage: cc.py fuzzer [-h] {random,brute,mutate,replay,identify} ...

Fuzzing module for CaringCaribou

positional arguments:
  {random,brute,mutate,replay,identify}
    random              Random fuzzer for messages and arbitration IDs
    brute               Brute force selected nibbles in a message
    mutate              Mutate selected nibbles in arbitration ID and message
    replay              Replay a previously recorded directive file
    identify            Replay and identify message causing a specific event

optional arguments:
  -h, --help            show this help message and exit

Example usage:

./cc.py fuzzer random
./cc.py fuzzer random -min 4 -seed 0xabc123 -f log.txt
./cc.py fuzzer brute -d 12345678 -db 00001100 0x123
./cc.py fuzzer mutate -d 1234abcd -db 00001100 -i 7fff -ib 0111
./cc.py fuzzer replay log.txt
./cc.py fuzzer identify log.txt
````
