# DoIP - Diagnostic communication over Internet Protocol
This module can be used to enumerate and perform security testing on DoIP upon the ISO 13400-2. It is mainly build targeting the UDSonIP (ISO 14229-5) protocol implementation in Caring Caribou, but it is supposed to be extended for further DoIP testing even outside of the UDS implementation.

The UDS protocol uses a server-client model, where the client (e.g. a diagnostics tool or Caring Caribou) sends requests on a specific arbitration ID, which a server (ECU) listens to. The server sends responses on another specific arbitration ID.

Supported modes:
* discovery - Scan for arbitration IDs where ECUs listen and respond to incoming diagnostics requests
* services - Scan for diagnostics services supported by an ECU
* ecu_reset - Reset an ECU
* security_seed - Request security seeds from an ECU
* dump_dids - Dump data identifiers with the read_data_by_identifier UDS service
* testerpresent - Force an elevated diagnostics session against an ECU to stay active

As always, module help can be shown by adding the `-h` flag (as shown below). You can also show help for a specific mode by specifying the mode followed by `-h`, e.g. `./cc.py doip discovery -h` or `./cc.py doip testerpresent -h`

```
$ ./cc.py doip -h

-------------------
CARING CARIBOU v0.3
-------------------

Loaded module 'doip'

usage: cc.py doip [-h] {discovery,services,ecu_reset,testerpresent,security_seed,dump_dids} ...

DoIP module for CaringCaribou

positional arguments:
  {discovery,services,ecu_reset,testerpresent,security_seed,dump_dids}

optional arguments:
  -h, --help            show this help message and exit

Example usage:
  cc.py doip discovery
  cc.py doip discovery -blacklist 0x123 0x456
  cc.py doip discovery -autoblacklist 10
  cc.py doip services 0x733 0x633
  cc.py doip ecu_reset 1 0x733 0x633
  cc.py doip testerpresent 0x733
  cc.py doip security_seed 0x3 0x1 0x733 0x633 -r 1 -d 0.5
  cc.py doip dump_dids 0x733 0x633
  cc.py doip dump_dids 0x733 0x633 --min_did 0x6300 --max_did 0x6fff -t 0.1
```

## Discovery
Scans for arbitration IDs where an ECU responds to UDS requests.

The ID of both the request and the matching response are printed. These are typically used as inputs for other UDS modes.

```
$ ./cc.py doip discovery -h

-------------------
CARING CARIBOU v0.3
-------------------

Loaded module 'doip'

usage: cc.py doip discovery [-h] [-min MIN] [-max MAX] [-b B [B ...]] [-ab N] [-d D]

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
$ ./cc.py doip services -h

-------------------
CARING CARIBOU v0.3
-------------------

Loaded module 'doip'

usage: cc.py doip services [-h] [-t T] src dst

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
$ ./cc.py doip ecu_reset -h

-------------------
CARING CARIBOU v0.3
-------------------

Loaded module 'doip'

usage: cc.py doip ecu_reset [-h] type src dst

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
$ ./cc.py doip testerpresent -h

-------------------
CARING CARIBOU v0.3
-------------------

Loaded module 'doip'

usage: cc.py doip testerpresent [-h] [-d D] [-dur S] src dst

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
$ ./cc.py doip dump_dids -h

-------------------
CARING CARIBOU v0.3
-------------------

Loaded module 'doip'

usage: cc.py doip dump_dids [-h] [-t T] [--min_did MIN_DID] [--max_did MAX_DID] src dst

positional arguments:
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

optional arguments:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout
  --min_did MIN_DID  minimum device identifier (DID) to read (default: 0x0000)
  --max_did MAX_DID  maximum device identifier (DID) to read (default: 0xFFFF)
```