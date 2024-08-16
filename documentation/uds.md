# UDS - Unified Diagnostics Services
This module can be used to discover and utilize various diagnostics services. It is built upon the ISO 14229-1 protocol implementation in Caring Caribou and
replaces the old [DCM](./dcm.md) module.

The UDS protocol uses a server-client model, where the client (e.g. a diagnostics tool or Caring Caribou) sends requests on a specific arbitration ID, which a server (ECU) listens to. The server sends responses on another specific arbitration ID.

Supported modes:
* discovery - Scan for arbitration IDs where ECUs listen and respond to incoming diagnostics requests
* services - Scan for diagnostics services supported by an ECU
* subservices - Subservice enumeration of supported diagnostics services by an ECU
* ecu_reset - Reset an ECU
* testerpresent - Force an elevated diagnostics session against an ECU to stay active
* security_seed - An automated way to collect seeds for a specific security access level in a specific diagnostic session
* dump_dids - Dumps values of Dynamic Data Identifiers (DIDs)
* read_mem - Read memory from an ECU
* auto - Fully automated diagnostics scan, by using the already existing UDS submodules

As always, module help can be shown by adding the `-h` flag (as shown below). You can also show help for a specific mode by specifying the mode followed by `-h`, e.g. `caringcaribou uds discovery -h` or `caringcaribou uds testerpresent -h`

```
$ caringcaribou uds -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'uds'

usage: caringcaribou uds [-h]
                 {discovery,services,ecu_reset,testerpresent,security_seed,dump_dids,read_mem}
                 ...

Universal Diagnostic Services module for CaringCaribou

positional arguments:
  {discovery,services,ecu_reset,testerpresent,security_seed,dump_dids,read_mem}

optional arguments:
  -h, --help            show this help message and exit

Example usage:
  caringcaribou uds discovery
  caringcaribou uds discovery -blacklist 0x123 0x456
  caringcaribou uds discovery -autoblacklist 10
  caringcaribou uds services 0x733 0x633
  caringcaribou uds ecu_reset 1 0x733 0x633
  caringcaribou uds testerpresent 0x733
  caringcaribou uds security_seed 0x3 0x1 0x733 0x633 -r 1 -d 0.5
  caringcaribou uds dump_dids 0x733 0x633
  caringcaribou uds dump_dids 0x733 0x633 --min_did 0x6300 --max_did 0x6fff -t 0.1
  caringcaribou uds read_mem 0x733 0x633 --start_addr 0x0 --mem_length 0x1000 --mem_size 0x100 --outfile memory_0_1000_100
```

## Discovery
Scans for arbitration IDs where an ECU responds to UDS requests.

The ID of both the request and the matching response are printed. These are typically used as inputs for other UDS modes.

```
$ caringcaribou uds discovery -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'uds'

usage: caringcaribou uds discovery [-h] [-min MIN] [-max MAX] [-b B [B ...]] [-ab N]
                           [-sv] [-d D]

optional arguments:
  -h, --help            show this help message and exit
  -min MIN              min arbitration ID to send request for
  -max MAX              max arbitration ID to send request for
  -b B [B ...], --blacklist B [B ...]
                        arbitration IDs to blacklist responses from
  -ab N, --autoblacklist N
                        listen for false positives for N seconds and blacklist
                        matching arbitration IDs before running discovery
  -sv, --skipverify     skip verification step (reduces result accuracy)
  -d D, --delay D       D seconds delay between messages (default: 0.01)
```

Example use:
```
$ caringcaribou uds discovery

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

Sending Diagnostic Session Control to 0x07e0
  Verifying potential response from 0x07e0
    Resending 0x7e0...  Success
Found diagnostics server listening at 0x07e0, response at 0x07e8

Identified diagnostics:

+------------+------------+
| CLIENT ID  | SERVER ID  |
+------------+------------+
| 0x000007e0 | 0x000007e8 |
+------------+------------+
```

## Services
Scans an ECU (or rather, a given pair of request/response arbitration IDs) for supported diagnostics services.

```
$ caringcaribou uds services -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'uds'

usage: caringcaribou uds services [-h] [-t T] src dst

positional arguments:
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

optional arguments:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout (default: 0.2)
```

Example use:
```
$ caringcaribou uds services 0x7E0 0x7E8

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

Probing service 0xff (255/255): found 19
Done!

Supported service 0x01: Unknown service
Supported service 0x02: Unknown service
Supported service 0x03: Unknown service
Supported service 0x04: Unknown service
Supported service 0x04: Unknown service
Supported service 0x38: Unknown service
Supported service 0x09: Unknown service
Supported service 0x10: DIAGNOSTIC_SESSION_CONTROL
Supported service 0x11: ECU_RESET
Supported service 0x19: READ_DTC_INFORMATION
Supported service 0x22: READ_DATA_BY_IDENTIFIER
Supported service 0x23: READ_MEMORY_BY_ADDRESS
Supported service 0x27: SECURITY_ACCESS
Supported service 0x28: COMMUNICATION_CONTROL
Supported service 0x2e: WRITE_DATA_BY_IDENTIFIER
Supported service 0x2f: INPUT_OUTPUT_CONTROL_BY_IDENTIFIER
Supported service 0x31: ROUTINE_CONTROL
Supported service 0x3e: TESTER_PRESENT
Supported service 0x85: CONTROL_DTC_SETTING
```


## Sub-services
Scans a diagnostics service ID for supported sub-service IDs.

```
$ caringcaribou uds subservices -h

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

usage: caringcaribou uds subservices [-h] [-t T] dtype stype src dst

positional arguments:
  dtype              Diagnostic Session Control Subsession Byte
  stype              Service ID
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

options:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout (default: 0.02)
```


## ECU Reset
Requests a restart of an ECU.

It is common for an ECU to support multiple reset types.

```
$ caringcaribou uds ecu_reset -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'uds'

usage: caringcaribou uds ecu_reset [-h] [-t T] type src dst

positional arguments:
  type               Reset type: 1=hard, 2=key off/on, 3=soft, 4=enable rapid
                     power shutdown, 5=disable rapid power shutdown
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

optional arguments:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout
```

## Tester Present
Sends Tester Present messages to keep an elevated diagnostics session alive.

Elevated sessions (often referred to as "unlocked servers") automatically fall back to default session ("re-lock") once no Tester Present message has been seen for a certain amount of time.

By continuing to send Tester Present messages after a server (ECU) has been unlocked (e.g. by an official diagnostics tool), it can be kept in an unlocked state for an arbitrary amount of time in order to allow continued access to protected services.

```
$ caringcaribou uds testerpresent -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'uds'

usage: caringcaribou uds testerpresent [-h] [-d D] [-dur S] [-spr] src

positional arguments:
  src                   arbitration ID to transmit to

optional arguments:
  -h, --help            show this help message and exit
  -d D, --delay D       send TesterPresent every D seconds (default: 0.5)
  -dur S, --duration S  automatically stop after S seconds
  -spr                  suppress positive response
```

## Dump DIDs
Scans a range of Dynamic Data Identifiers (DIDs) and dumps their values.

```
$ caringcaribou uds dump_dids -h

-------------------
CARING CARIBOU v0.x
-------------------

Loaded module 'uds'

usage: caringcaribou uds dump_dids [-h] [-t T] [--min_did MIN_DID] [--max_did MAX_DID]
                           src dst

positional arguments:
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

optional arguments:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout
  --min_did MIN_DID  minimum device identifier (DID) to read (default: 0x0000)
  --max_did MAX_DID  maximum device identifier (DID) to read (default: 0xFFFF)
```

Example use:
```
$ caringcaribou uds dump_dids 0x7E0 0x7E8

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

Dumping DIDs in range 0x0000-0xffff

Identified DIDs:
DID    Value (hex)
0x0100 00
0x0102 00
0x0104 0000
0x0105 0000
0x0106 00
0x0108 00
0x011b 00000009000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
0x0121 00000019
0x0153 005eeec64500020000005ed8b8fb00020000005ec2957500020000005eb48d2a00020000005e84a2e800020000005e72aac700020000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
0x0154 005ef6a90e40000000005ef6a34040000000005ef6a2af40000000005ef6a25140000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
0x0155 005e84950204000000005e84950104000000005e84950104000000005e84950004000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
0x0261 00
0x028d 0c19
0x029e 0019
0x02a0 00120000000000210000001e00000001000000340000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
0x02a1 00030000000000000000000000390000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
0x02cd 00
0x02ed 02010300000000000400
0x02ee 04c00000000000000000
...
0x14d2 00
0x14d4 0000
0x14d8 61a7
0x14f9 5a00
0x1510 06
0x1514 04
0x1538 0000
0x1558 01
0x1588 08
^C

Terminated by user
```


## Security Seed
An automated way to collect seeds for a specific security access level in a specific diagnostic session. You can also define the number of seeds to collect, as well as configure automatic resets and set the wait time between requests.

```
$ caringcaribou uds security_seed -h

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

usage: caringcaribou uds security_seed [-h] [-r RTYPE] [-d D] [-n NUM] stype level src dst

positional arguments:
  stype                 Session Type: 1=defaultSession 2=programmingSession 3=extendedSession 4=safetySession [0x40-0x5F]=OEM
                        [0x60-0x7E]=Supplier [0x0, 0x5-0x3F, 0x7F]=ISOSAEReserved
  level                 Security level: [0x1-0x41 (odd only)]=OEM 0x5F=EOLPyrotechnics [0x61-0x7E]=Supplier [0x0, 0x43-0x5E,
                        0x7F]=ISOSAEReserved
  src                   arbitration ID to transmit to
  dst                   arbitration ID to listen to

options:
  -h, --help            show this help message and exit
  -r RTYPE, --reset RTYPE
                        Enable reset between security seed requests. Valid RTYPE integers are: 1=hardReset, 2=key off/on, 3=softReset,
                        4=enable rapid power shutdown, 5=disable rapid power shutdown. (default: None)
  -d D, --delay D       Wait D seconds between reset and security seed request. You'll likely need to increase this when using RTYPE:
                        1=hardReset. Does nothing if RTYPE is None. (default: 0.01)
  -n NUM, --num NUM     Specify a positive number of security seeds to capture before terminating. A '0' is interpreted as infinity.
                        (default: 0)
```

Example use for collecting 10 seeds in the Diagnostic Session 0x3 (Extended), and Security Access level 0x3:
```
$ caringcaribou uds security_seed -n 10 0x3 0x3 0x7E0 0x7E8

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

Security seed dump started. Press Ctrl+C to stop.

Seed received: 2190c8e4	(Total captured: 10)

Security Access Seeds captured:
8ac56231
178bc5e2
773b1d8e
b2592c96
a251a8d4
2b95ca65
eb753a9d
1b8dc663
b5daed76
2190c8e4
```


## Auto
Performs a fully automated diagnostics scan from start to finish, by using the already existing CC modules.

```
$ caringcaribou uds auto -h

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

usage: caringcaribou uds auto [-h] [-min MIN] [-max MAX] [-b B [B ...]] [-ab N] [-sv] [-d D] [-t T] [--min_did MIN_DID] [--max_did MAX_DID]

options:
  -h, --help            show this help message and exit
  -min MIN              min arbitration ID to send request for
  -max MAX              max arbitration ID to send request for
  -b B [B ...], --blacklist B [B ...]
                        arbitration IDs to blacklist responses from
  -ab N, --autoblacklist N
                        listen for false positives for N seconds and blacklist matching arbitration IDs before running discovery
  -sv, --skipverify     skip verification step (reduces result accuracy)
  -d D, --delay D       D seconds delay between messages (default: 0.01)
  -t T, --timeout T     wait T seconds for response before timeout (default: 0.2)
  --min_did MIN_DID     minimum device identifier (DID) to read (default: 0x0000)
  --max_did MAX_DID     maximum device identifier (DID) to read (default: 0xFFFF)
```
