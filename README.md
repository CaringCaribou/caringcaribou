# caringcaribou
A friendly car security exploration tool

## Rationale
We are lacking a security testing tool for automotive. A zero-knowledge tool that can be dropped onto any automotive network and collect information regarding what services exist and what vulnerabilities exist. This is a start.

This work was done as part of the HeavenS research project.

## Features
Currently this is just a bunch of python files, typically one per area-of-interest. In time, the idea is to build a master application that takes arguments and then imports and executes modules as required.

### CAN.Action
This is the daddy of all classes. Imported by all other modules. Abstraction for all access to the CAN bus

### Diagnostics ISO 14229
- ArbID Discovery - try to connect (02 10 01) to all possible ArbId (000-7FF) and collect valid responses (xx 7F or xx 50)
- Service Discovery - Brute force all SIDs and report any responses (anything that is not xx F7 11)
- Sub-function Discovery - Brute force engine that takes SID and an index indicating which positions to brute force as input

### XCP
- ArbId Discovery - try to connect (FF) to all possible ArbId (000-7FF) and collect all valid responses (FF or FE)
- Get Basic Information - connect and get information about XCP abilities in the target environment
- Upload - dump ECU memory (SRAM, flash and bootloader) to file 

### Listener
- ArbId listener - register all ArbIds heard on the CAN bus

## Hardware requirements
Some sort of interface towards an automotive bus that is compatible with socketCAN (http://elinux.org/CAN_Bus#CAN_Support_in_Linux).
We used a PEAK hardware called PCAN-USB

## Software requirements
python2.7
python-can
a pretty modern linux kernel
## How to install
### Ubuntu
Focus-area DO THIS
### Windows 7
Help needed
### Raspberry Pi
- http://www.cowfishstudios.com/blog/canned-pi-part1
- http://skpang.co.uk/catalog/pican-canbus-board-for-raspberry-pi-p-1196.html
Wireshark is up and running but python-can is currently defunct

# The target
We used an open source implementation of Autosar from ArcCore available here: http://www.arccore.com/hg **FIXME**
We used a devboard from ArcCore, called Arctic EVK-M3 - an STM32F107 based device

# Contributors
* The HeavenS project, funded by VINNOVA - http://www.vinnova.se/sv/Resultat/Projekt/Effekta/HEAVENS-HEAling-Vulnerabilities-to-ENhance-Software-Security-and-Safety/
* Christian Sandberg
* Kasper Karlsson
* Tobias Lans
* Mattias Jidhage
* Johannes Weschke
* Filip Hesslund
