# Fuzzer
The fuzzer module supports multiple fuzzing methods.
* random - generates random payloads within a given length interval
* brute - brute forces all possible values for selected nibbles of a given message
* mutate - mutates a given message by randomizing selected nibbles in arbitration ID and/or payload
* replay - replays a previous fuzzing session log file
* identify - like replay, but takes manual input to identify a single message causing an observed effect

The `random` and `mutate` modes both show which random seed is being used. The seed can be passed in an optional argument to these modes, in order to repeat the sequence of generated messages.

As always, module help can be shown by adding the `-h` flag (as shown below). You can also show help for a specific fuzzing mode by specifying the mode followed by `-h`, e.g. `cc.py fuzzer random -h` or `cc.py fuzzer mutate -h`

````
$ cc.py fuzzer -h

-------------------
CARING CARIBOU v0.x
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

cc.py fuzzer random
cc.py fuzzer random -min 4 -seed 0xabc123 -f log.txt
cc.py fuzzer brute 0x123 12ab..78
cc.py fuzzer mutate 7f.. 12ab....
cc.py fuzzer replay log.txt
cc.py fuzzer identify log.txt
````
