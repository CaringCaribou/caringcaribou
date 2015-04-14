# caringcaribou
A friendly car security exploration tool

## Rationale
We are lacking a security testing tool for automotive. A zero-knowledge tool that can be dropped onto any automotive network and collect information regarding what services exist and what vulnerabilities exist. This is a start.

The start of this work is done as part of the HeavenS research project.

## Features
Currently this is just a bunch of python files, typically one per area-of-interest. In time, the idea is to build a master application that takes arguments and then imports and executes modules as required.

### CAN.Action
This is the daddy of all classes. Imported by all other modules. Abstraction for all access to the CAN bus

### Diagnostics
ArbID Discovery - try to connect (02 10 01) to all possible ArbId (000-7FF) and collect valid responses (xx 7F or xx 50)
Service Discovery - Brute force all SIDs and report any responses (anything that is not xx F7 11)
Sub-function Discovery - Brute force engine that takes SID and an index indicating which positions to brute force as input

### XCP
ArbId Discovery - try to connect (FF) to all possible ArbId (000-7FF) and collect all valid responses (FF or FE)
Get Basic Information - connect and get information about XCP abilities in the target environment
Upload - dump ECU memory (SRAM, flash and bootloader) to file 

### Listener
TBD - ArbId listener - register all ArbIds heard on the CAN bus

## Hardware requirements


## Software requirements

## How to install
### Ubuntu
### Windows 7
### Raspberry Pi

# Contributors
The HeavenS project - 
Christian Sandberg
