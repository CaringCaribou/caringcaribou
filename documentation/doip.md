# DoIP - Diagnostic communication over Internet Protocol
This module can be used to enumerate and perform security testing on DoIP upon the ISO 13400-2. It is mainly build targeting the UDSonIP (ISO 14229-5) protocol implementation in Caring Caribou, but it is supposed to be extended for further DoIP testing even outside the UDS implementation.

*Note: This module requires the packages `doipclient` and `udsoncan`, which only support Python 3.6+. These can be installed through `$ pip install doipclient udsoncan`.  If your system uses Python 2 as default python interpreter, you may have to use `$ pip3 install doipclient udsoncan` or `$ python3 -m pip install doipclient udsoncan` (and make sure to run Caring Caribou through `python3`) instead.*

The UDS protocol uses a server-client model, where the client (e.g. a diagnostics tool or Caring Caribou) sends requests on a specific arbitration ID, which a server (ECU) listens to. The server sends responses on another specific arbitration ID.

Supported modes:
* discovery - Scan for arbitration IDs where ECUs listen and respond to incoming diagnostics requests
* services - Scan for diagnostics services supported by an ECU
* ecu_reset - Reset an ECU
* security_seed - Request security seeds from an ECU
* dump_dids - Dump data identifiers with the read_data_by_identifier UDS service
* testerpresent - Force an elevated diagnostics session against an ECU to stay active
* seed_randomness_fuzzer - ECUReset method fuzzing for seed randomness evaluation

As always, module help can be shown by adding the `-h` flag (as shown below). You can also show help for a specific mode by specifying the mode followed by `-h`, e.g. `caringcaribou doip discovery -h` or `caringcaribou doip testerpresent -h`

```
$ caringcaribou doip -h


-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'doip'

usage: caringcaribou doip [-h] {discovery,services,ecu_reset,testerpresent,security_seed,dump_dids,seed_randomness_fuzzer} ...

DoIP module for CaringCaribou

positional arguments:
  {discovery,services,ecu_reset,testerpresent,security_seed,dump_dids,seed_randomness_fuzzer}

optional arguments:
  -h, --help            show this help message and exit

Example usage:
  caringcaribou doip discovery
  caringcaribou doip discovery -blacklist 0x123 0x456
  caringcaribou doip discovery -autoblacklist 10
  caringcaribou doip services 0x733 0x633
  caringcaribou doip ecu_reset 1 0x733 0x633
  caringcaribou doip testerpresent 0x733
  caringcaribou doip security_seed 0x3 0x1 0x733 0x633 -r 1 -d 0.5
  caringcaribou doip dump_dids 0x733 0x633
  caringcaribou doip dump_dids 0x733 0x633 --min_did 0x6300 --max_did 0x6fff -t 0.1
  caringcaribou doip seed_randomness_fuzzer 2 2 0x733 0x633 -m 1 -t 10 -d 50 -id 4
```

## Discovery
Scans for arbitration IDs where an ECU responds to UDS requests.

The ID of both the request and the matching response are printed. These are typically used as inputs for other UDS modes.

```
$ caringcaribou doip discovery -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'doip'

usage: caringcaribou doip discovery [-h] [-min MIN] [-max MAX] [-b B [B ...]] [-ab N] [-d D]

optional arguments:
  -h, --help            show this help message and exit
  -min MIN              min arbitration ID to send request for
  -max MAX              max arbitration ID to send request for
  -b B [B ...], --blacklist B [B ...]
                        arbitration IDs to blacklist responses from
  -ab N, --autoblacklist N
                        listen for false positives for N seconds and blacklist matching arbitration IDs before running discovery
  -d D, --delay D       D seconds delay between messages (default: 0.2)
```

## Services
Scans an ECU (or rather, a given pair of request/response arbitration IDs) for supported diagnostics services.

```
$ caringcaribou doip services -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'doip'

usage: caringcaribou doip services [-h] [-t T] src dst

positional arguments:
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

optional arguments:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout (default: 0.2)
```

## ECU Reset
Requests a restart of an ECU.

It is common for an ECU to support multiple reset types.

```
$ caringcaribou doip ecu_reset -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'doip'

usage: caringcaribou doip ecu_reset [-h] type src dst

positional arguments:
  type        Reset type: 1=hard, 2=key off/on, 3=soft, 4=enable rapid power shutdown, 5=disable rapid power shutdown
  src         arbitration ID to transmit to
  dst         arbitration ID to listen to

optional arguments:
  -h, --help  show this help message and exit
```

## Tester Present
Sends Tester Present messages to keep an elevated diagnostics session alive.

Elevated sessions (often referred to as "unlocked servers") automatically fall back to default session ("re-lock") once no Tester Present message has been seen for a certain amount of time.

By continuing to send Tester Present messages after a server (ECU) has been unlocked (e.g. by an official diagnostics tool), it can be kept in an unlocked state for an arbitrary amount of time in order to allow continued access to protected services.

```
$ caringcaribou doip testerpresent -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'doip'

usage: caringcaribou doip testerpresent [-h] [-d D] [-dur S] src dst

positional arguments:
  src                   arbitration ID to transmit to
  dst                   arbitration ID to listen to

optional arguments:
  -h, --help            show this help message and exit
  -d D, --delay D       send TesterPresent every D seconds (default: 0.5)
  -dur S, --duration S  automatically stop after S seconds
```

## Dump DIDs
Scans a range of Dynamic Data Identifiers (DIDs) and dumps their values.

```
$ caringcaribou doip dump_dids -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'doip'

usage: caringcaribou doip dump_dids [-h] [-t T] [--min_did MIN_DID] [--max_did MAX_DID] src dst

positional arguments:
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

optional arguments:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout
  --min_did MIN_DID  minimum device identifier (DID) to read (default: 0x0000)
  --max_did MAX_DID  maximum device identifier (DID) to read (default: 0xFFFF)
```

## Seed Randomness Fuzzer
Requests a security seed after a Hard ECUReset, using the supplied request sequence, to check for duplicate seeds. 

In case that duplicate seeds are found by the tool, it means that the ECU is potentially  vulnerable and uses weak random number generation seeded by the system timer.

```
$ caringcaribou doip seed_randomness_fuzzer -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'doip'

usage: caringcaribou doip seed_randomness_fuzzer [-h] [-t ITERATIONS] [-r RTYPE] [-id RTYPE] [-m RMETHOD] [-d D] stype level src dst

positional arguments:
  stype                 Session Type: 1=defaultSession 2=programmingSession 3=extendedSession 4=safetySession
  level                 Security level: [0x1-0x41 (odd only)]=OEM 0x5F=EOLPyrotechnics [0x61-0x7E]=Supplier [0x0, 0x43-0x5E, 0x7F]=ISOSAEReserved
  src                   arbitration ID to transmit to
  dst                   arbitration ID to listen to

optional arguments:
  -h, --help            show this help message and exit
  -t ITERATIONS, --iter ITERATIONS
                        Number of iterations of seed requests. It is highly suggested to perform >=1000 for accurate results. (default: 1000)
  -r RTYPE, --reset RTYPE
                        Enable reset between security seed requests. Valid RTYPE integers are: 1=hardReset, 2=key off/on, 3=softReset, 4=enable rapid power shutdown, 5=disable rapid power shutdown. This attack is based on hard
                        ECUReset (1) as it targets seed randomness based on the system clock. (default: hardReset)
  -id RTYPE, --inter_delay RTYPE
                        Intermediate delay between messages:(default: 0.1)
  -m RMETHOD, --reset_method RMETHOD
                        The method that the ECUReset will happen: 1=before each seed request 0=once before the seed requests start (default: 1) *This method works better with option 1.*
  -d D, --delay D       Wait D seconds between reset and security seed request. You'll likely need to increase this when using RTYPE: 1=hardReset. Does nothing if RTYPE is None. (default: 3.901)
```
