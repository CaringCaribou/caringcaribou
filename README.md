# caringcaribou
A friendly car security exploration tool

## Rationale
We are lacking a security testing tool for automotive. A zero-knowledge tool that can be dropped onto any automotive network and collect information regarding what services exist and what vulnerabilities exist. This is a start.

This work was done as part of the HeavenS research project.

## Features and Architecture
CaringCaribou is module based with a master command (cc.py) that runs the show. The reason for this is to enable an easy drop-in architecture for new modules.

## List of Modules

### dcm.py - Diagnostics ISO 14229
- discovery - ArbID Discovery. Tries to connect (02 10 01) to all possible ArbId (0x000-0x7FF) and collect valid responses (xx 7F or xx 50)
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

### can_actions.py
This is the daddy of all shared module functionality. Imported by all modules. Provides abstraction for access to the CAN bus, CAN bruteforce engines etc.

## Hardware requirements
Some sort of interface towards an automotive bus that is compatible with socketCAN (http://elinux.org/CAN_Bus#CAN_Support_in_Linux).

## Software requirements
- python2.7
- python-can
- a pretty modern linux kernel

## How to install
Instructions available [here](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/howtoinstall.md)

## How to use
The best way to understand how to use Caring Caribou is by envoking cc.py's help menu:
    
    python cc.py -h

Detailed information on the [usage](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/howtouse.md). 
## Extending the project
Create a python file with a ```module_main(args)``` function. Put it in the ```modules``` folder. CaringCaribou (cc.py) will automagically recognize it as a module and list it in the output of ```./cc.py -h```

## The target
We used an open source implementation of Autosar from ArcCore available here: http://www.arccore.com/hg **FIXME**
We used a devboard from ArcCore, called Arctic EVK-M3 - an STM32F107 based device

## Contributors
* The HeavenS project, funded by VINNOVA - http://www.vinnova.se/sv/Resultat/Projekt/Effekta/HEAVENS-HEAling-Vulnerabilities-to-ENhance-Software-Security-and-Safety/
* Christian Sandberg
* Kasper Karlsson
* Tobias Lans
* Mattias Jidhage
* Johannes Weschke
* Filip Hesslund
* Craig Smith (OpenGarages.org)
