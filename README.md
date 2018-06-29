# Caring Caribou
A friendly car security exploration tool

## Rationale
We are lacking a security testing tool for automotive. A zero-knowledge tool that can be dropped onto any CAN network and collect information regarding what services and vulnerabilities exist. This is a start.

This work was initiated as part of the HeavenS research project, but lives on as a stand-alone project.

## Features and Architecture
Caring Caribou is based on a master script `cc.py`, which runs the show. This enables an easy drop-in architecture for new modules, which are located in the `/modules` folder.

The tool also has a `/libs` folder. This contains various higher level CAN protocol implementations and useful functions, which can be used by the modules.

## List of Modules
A clean installation of Caring Caribou includes the following modules:

### dcm.py - Diagnostics ISO 14229
- discovery - ArbID Discovery. Tries to connect (02 10 01) to all possible ArbId (0x000-0x7FF) and collect valid responses (xx 7F or xx 50). Supports both manual and automatic blacklisting of arbitration IDs, in order to remove false positives.
- services - Service Discovery. Brute force all Service Id's (SID) and report any responses (anything that is not xx F7 11)
- subfunc - Sub-function Discovery. Brute force engine that takes SID and an index indicating which positions to brute force as input.
- dtc - Diagnostic Trouble Codes.  Fetches DTCs.  Can clear DTCs and MIL (Engine Light) as well.

Detailed information on the [dcm-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/dcm.md).

### xcp.py - Universal Measurement and Calibration Protocol (XCP)
- discovery - ArbId Discovery. Tries to connect (FF) to all possible ArbId (0x000-0x7FF) and collect all valid responses (FF or FE)
- info - XCP Get Basic Information. Connects and gets information about XCP abilities in the target environment
- dump - XCP Upload. Used to dump ECU memory (SRAM, flash and bootloader) to file 

Detailed information on the [xcp-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/xcp.md).

### listener.py - Listener
- ArbId listener - register all ArbIds heard on the CAN bus

Detailed information on the [listener-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/listener.md).

### send.py - Send CAN packets
- Raw message transmission module, used to drive manual test cases

Detailed information on the [send-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/send.md).

### dump.py - Dump CAN traffic
- Dump incoming traffic to stdout or file.

Detailed information on the [dump-module](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/dump.md).

## List of libraries
The `/lib` folder contains the following libraries:

### can_actions.py
Contains various shared module functionality. Provides abstraction for access to the CAN bus, CAN bruteforce engines etc.

### iso14229_1.py
Implementation of the ISO-14229-1 standard for Unified Diagnostic Services (UDS).

### iso15765_2.py
Implementation of the ISO-15765-2 standard (ISO-TP). This is a transport protocol which enables sending of messages longer than 8 bytes over CAN by splitting them into multiple data frames.

## Hardware requirements
Some sort of CAN bus interface compatible with socketCAN (http://elinux.org/CAN_Bus#CAN_Support_in_Linux)

## Software requirements
- Python 2.7 or 3.x
- python-can
- a pretty modern linux kernel

## How to install
Instructions available [here](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/howtoinstall.md)

## How to use
The best way to understand how to use Caring Caribou is to look at cc.py's help menu:
    
    python cc.py -h

Detailed usage information is available [here](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/howtouse.md). 

## Extending the project
Create a python file with a function `module_main(args)` and put it in the ```tool/modules``` folder. Caring Caribou will automagically recognize it as a module and list it in the output of `./cc.py -h`

For example, if your new module is located in `modules/foo.py` you run it with the command `./cc.py foo`. Additional arguments (if any) are passed as arguments to the `module_main` function.

A template for new modules is available in `tool/template`

## The target
The target ECU used for the development setup is an STM32F107 based dev-board from ArcCore called Arctic EVK-M3, but the tool can be used against any ECU communicating over a CAN bus.

## Contributors
* The [HeavenS](http://www.vinnova.se/sv/Resultat/Projekt/Effekta/HEAVENS-HEAling-Vulnerabilities-to-ENhance-Software-Security-and-Safety/) project, funded by VINNOVA
* Christian Sandberg
* Kasper Karlsson
* Tobias Lans
* Mattias Jidhage
* Johannes Weschke
* Filip Hesslund
* Craig Smith (OpenGarages.org)
* internot
