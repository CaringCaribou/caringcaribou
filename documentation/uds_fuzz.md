# UDS_Fuzz - Unified Diagnostics Services Fuzzer
The Security Access Service implemented in UDS, is used to modify the ECU data stored in memory. To grand access to this service, there is a seed/key mechanism which is customized (mainly for obscurity) by each automotive manufacturer.

Research showed that many manufacturers do not seed with enough entropy the seed/key algorithm of modern ECUs. In more detail ([source](https://www.reddit.com/r/CarHacking/comments/m044jp/simos18_supplier_bootloader_sboot_exploit_reading/)):

>  the random number generator is seeded with the system timer, which is not a source of entropy because it behaves predictably

The uds_fuzz module implements the appropriate fuzzing methodology to enumerate (seed_randomness_fuzzer) and exploit (delay_fuzzer) vulnerable ECUs.

Supported modes:
* seed_randomness_fuzzer - ECUReset method fuzzing for seed randomness evaluation
* delay_fuzzer - delay fuzzing for targets with weak randomness implemented, to match acquired seed/key pair to the delay in which the seed can be requested

As always, module help can be shown by adding the `-h` flag (as shown below). You can also show help for a specific mode by specifying the mode followed by `-h`, e.g. `cc.py uds_fuzz seed_randomness_fuzzer -h` or `cc.py uds_fuzz delay_fuzzer -h`

```
$ cc.py uds_fuzz -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'uds_fuzz'

usage: cc.py uds_fuzz [-h] {delay_fuzzer,seed_randomness_fuzzer} ...

UDS seed randomness fuzzer and tester module for CaringCaribou

positional arguments:
  {delay_fuzzer,seed_randomness_fuzzer}

optional arguments:
  -h, --help            show this help message and exit

Example usage:
  cc.py uds_fuzz seed_randomness_fuzzer 100311022701 0x733 0x633 -d 4 -r 1 -id 2 -m 0
  cc.py uds_fuzz delay_fuzzer 100311022701 0x03 0x733 0x633
```

## Seed Randomness Fuzzer
Requests a security seed after a Hard ECUReset, using the supplied request sequence, to check for duplicate seeds. 

In case that duplicate seeds are found by the tool, it means that the ECU is potentially  vulnerable and uses weak random number generation seeded by the system timer.

```
$ cc.py uds_fuzz seed_randomness_fuzzer -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'uds_fuzz'

usage: cc.py uds_fuzz seed_randomness_fuzzer [-h] [-t ITERATIONS] [-r RTYPE] [-id RTYPE] [-m RMETHOD] [-d D]
                                             stype src dst

positional arguments:
  stype                 Describe the session sequence followed by the target ECU.e.g. if the following sequence is
                        needed in order to request a seed: Request 1 - 1003 (Diagnostic Session Control), Request 2 -
                        1102 (ECUReset), Request 3 - 1005 (Diagnostic Session Control), Request 4 - 2705 (Security
                        Access Seed Request). The option should be: 1003110210052705
  src                   arbitration ID to transmit to
  dst                   arbitration ID to listen to

optional arguments:
  -h, --help            show this help message and exit
  -t ITERATIONS, --iter ITERATIONS
                        Number of iterations of seed requests. It is highly suggested to perform >=1000 for accurate
                        results. (default: 1000)
  -r RTYPE, --reset RTYPE
                        Enable reset between security seed requests. Valid RTYPE integers are: 1=hardReset, 2=key
                        off/on, 3=softReset, 4=enable rapid power shutdown, 5=disable rapid power shutdown. This
                        attack is based on hard ECUReset (1) as it targets seed randomness based on the system clock.
                        (default: hardReset)
  -id RTYPE, --inter_delay RTYPE
                        Intermediate delay between messages:(default: 0.1)
  -m RMETHOD, --reset_method RMETHOD
                        The method that the ECUReset will happen: 1=before each seed request 0=once before the seed
                        requests start (default: 1) *This method works better with option 1.*
  -d D, --delay D       Wait D seconds between reset and security seed request. You'll likely need to increase this
                        when using RTYPE: 1=hardReset. Does nothing if RTYPE is None. (default: 3.901)
```

## Delay Fuzzer
Requests a security seed after a Hard ECUReset, using the supplied request sequence, with increasing delays between the ECUReset and the seed request.

That way the exact delay needed to request the user specified seed can be matched. 

In that case, the user can access the security access service of vulnerable ECUs, with just one seed/key pair (it can be obtained in several ways) and no access to the secret key needed to generate the key from the seed.

```
$ cc.py uds_fuzz delay_fuzzer -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'uds_fuzz'

usage: cc.py uds_fuzz delay_fuzzer [-h] [-r RTYPE] [-d D] stype target src dst

positional arguments:
  stype                 Describe the session sequence followed by the target ECU.e.g. if the following sequence is
                        needed in order to request a seed: Request 1 - 1003 (Diagnostic Session Control), Request 2 -
                        1102 (ECUReset), Request 3 - 1005 (Diagnostic Session Control), Request 4 - 2705 (Security
                        Access Seed Request). The option should be: 1003110210052705
  target                Seed that is targeted for the delay attack. e.g. 41414141414141
  src                   arbitration ID to transmit to
  dst                   arbitration ID to listen to

optional arguments:
  -h, --help            show this help message and exit
  -r RTYPE, --reset RTYPE
                        Enable reset between security seed requests. Valid RTYPE integers are: 1=hardReset, 2=key
                        off/on, 3=softReset, 4=enable rapid power shutdown, 5=disable rapid power shutdown. This
                        attack is based on hard ECUReset (1) as it targets seed randomness based on the system clock.
                        (default: hardReset)
  -d D, --delay D       Wait D seconds between the different iterations of security seed request. You'll likely need
                        to increase this when using RTYPE: 1=hardReset. (default: 0.011)
```
