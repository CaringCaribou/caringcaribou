# Caring Caribou
A friendly automotive security exploration tool.

## Rationale
This work was initiated as part of the research project HEAVENS (HEAling Vulnerabilities to ENhance Software Security and Safety), but lives on as a stand-alone project.
We were lacking a security testing tool for automotive; a zero-knowledge tool that can be dropped onto any CAN network and collect information regarding what services and vulnerabilities exist. This project is a start.

## Documentation
- [How to install](documentation/howtoinstall.md)
- [How to use](documentation/howtouse.md)
- [Troubleshooting](documentation/troubleshooting.md), common errors and solutions

## Get started
Install the tool:

    python setup.py install

The best way to understand how to use Caring Caribou is to look at the help screen:

    caringcaribou --help

This will list all available modules at the bottom of the output. Help for specific modules works the same way. For example, the help screen for the `send` module is shown by running

    caringcaribou send --help

The module help always includes some usage examples. If the module has multiple sub functions, these have similar help screens as well:

    caringcaribou send message -h
    caringcaribou send file -h

More detailed usage information is available [in the documentation on usage](documentation/howtouse.md).

## Features and Architecture
Caring Caribou is based on a main entry point in `caringcaribou.py` which runs the show. This enables an easy drop-in architecture for new modules, which are located in the `caringcaribou/modules` folder.

The `caringcaribou/utils` folder contains various higher level CAN protocol implementations and shared functions, meant to be used by modules.

The `caringcaribou/tests` folder contains automated test suites and `/documentation` stores documentation files (modules are also documented here).

## List of Modules
A clean installation of Caring Caribou includes the following modules:

### uds - Universal Diagnostic Services
Discovers and utilizes various ISO 14229-1 services.
- discovery - Scans for ECUs supporting diagnostics services
- services - Scans for diagnostics services supported by an ECU
- subservices - Subservice enumeration of supported diagnostics services by an ECU
- ecu_reset - Reset an ECU
- testerpresent - Force an elevated session against an ECU to stay active
- dump_dids - Dumps values of Dynamic Data Identifiers (DIDs)
- read_mem - Read memory from an ECU
- auto - Fully automated diagnostics scan, by using the already existing UDS submodules

Details here: [uds module](documentation/uds.md)

### xcp - Universal Measurement and Calibration Protocol (XCP)
- discovery - Scans for ECUs supporting XCP
- info - XCP Get Basic Information. Retrieves information about XCP abilities of an ECU
- dump - XCP Upload. Used to dump ECU memory (such as SRAM, flash and bootloader) to file 

Details here: [xcp module](documentation/xcp.md)

### fuzzer - CAN fuzzer
- random - sends random CAN messages
- brute - brute forces all possible messages matching a given bit mask
- mutate - mutate selected nibbles of a given message
- replay - replay a log file from a previous fuzzing session
- identify - replay a log file and identify message causing a specific event

Details here: [fuzzer module](documentation/fuzzer.md)

### dump - Dump CAN traffic
Dumps incoming traffic to stdout (terminal output) or file

Details here: [dump module](documentation/dump.md)

### send - Send CAN packets
Raw message transmission module, used to send messages manually from command line or replay dump files

Details here:  [send module](documentation/send.md)

### listener - Listener
Lists all distinct arbitration IDs being used on the CAN bus

Details here: [listener module](documentation/listener.md)

### test - Run test suite
Runs automated Caring Caribou test suites

### dcm - [deprecated] Diagnostics Control Module
**Note**: This module has been replaced by the [UDS](documentation/uds.md) module. It is still supported by CC due to legacy reasons.

Details here: [dcm module](documentation/dcm.md)

### uds_fuzz - Universal Diagnostic Services Fuzzer
Fuzzing module for UDS security seed randomness evaluation and testing.
- seed_randomness_fuzzer - ECUReset method fuzzing for seed randomness evaluation
- delay_fuzzer - delay fuzzing for targets with weak randomness implemented, to match acquired seed/key pair to the delay in which the seed can be requested

Details here: [uds_fuzz module](documentation/uds_fuzz.md)

### doip - Diagnostic communication over Internet Protocol
Discovers and utilizes various ISO 13400-2 services.
- discovery - Scans for ECUs supporting diagnostics services
- services - Scans for diagnostics services supported by an ECU
- ecu_reset - Reset an ECU
- security_seed - Request security seeds from an ECU
- testerpresent - Force an elevated session against an ECU to stay active
- dump_dids - Dumps values of Dynamic Data Identifiers (DIDs)
- seed_randomness_fuzzer - ECUReset method fuzzing for seed randomness evaluation

Details here: [doip module](documentation/doip.md)

## List of libraries/utilities
The `caringcaribou/utils` folder contains the following:

### can_actions.py
Provides abstraction for access to the CAN bus, bruteforce engines etc.

### common.py
Contains various common functions, type converters etc.

### constants.py
Constant definitions

### iso14229_1.py
Implementation of the ISO-14229-1 standard for Unified Diagnostic Services (UDS).

### iso15765_2.py
Implementation of the ISO-15765-2 standard (ISO-TP). This is a transport protocol which enables sending of messages longer than 8 bytes over CAN by splitting them into multiple data frames.

## Hardware requirements
Some sort of CAN bus interface (http://elinux.org/CAN_Bus#CAN_Support_in_Linux)

## Software requirements
- Python 3.7 or higher
- python-can
- a pretty modern linux kernel

## Extending the project with new modules
- A template for new modules is available in `caringcaribou/modules/module_template.py`
- Create a python file with a function `module_main(args)` (or copy the template) in the `caringcaribou/modules` directory.
- In `setup.py`, add an entry under `caringcaribou.modules`, referencing your new module like: `my_module = caringcaribou.modules.my_module`
- Run `python setup.py install`
- Verify that the module is available, it should be listed in the output of `caringcaribou -h`

If your new module is located in `caringcaribou/modules/foo.py` you will run it with the command `caringcaribou foo`.
Additional arguments (if any) are passed as arguments to the `module_main` function.


## The target
The target ECU used for the development setup is an STM32F107 based dev-board from ArcCore called Arctic EVK-M3, but the tool can be used against any ECU communicating over a CAN bus.

## Contributors
* The [HEAVENS](https://www.vinnova.se/en/p/heavens-healing-vulnerabilities-to-enhance-software-security-and-safety/) project, funded by VINNOVA
* Christian Sandberg
* Kasper Karlsson
* Tobias Lans
* Mattias Jidhage
* Johannes Weschke
* Filip Hesslund
* Craig Smith (OpenGarages.org)
* internot
* Mathijs Hubrechtsen
* Lear Corporation
* sigttou
* FearfulSpoon
* Alex DeTrano
* Thomas Sermpinis
* Alexander Alasjö
* Vincent de Chefdebien
