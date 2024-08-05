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

## Write DIDs
Write data to one/multiple Data Identifiers (DIDs). By default, this command will verify the data was written successfully.
This is accomplished by first reading the DID, writing the DID, reading the DID and comparing the two values. If they are different,
the write was successful.

On the other hand, the user can skip this verification step by passing the `-sv` flag. In this case, only a write will be performed.

```
$ caringcaribou uds write_dids -h

-------------------
CARING CARIBOU v0.x
-------------------

Loading module 'uds'

usage: caringcaribou uds write_dids [-h] [-t T] [-sv] src dst min_did max_did data

positional arguments:
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to
  min_did            minimum device identifier (DID) to write
  max_did            maximum device identifier (DID) to write
  data               data to write (no spaces) in hex format e.g. deadbeef

options:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout
  -sv, --skipverify  skip write verification step i.e. do not check if write succeeded by reading back data identifier
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
