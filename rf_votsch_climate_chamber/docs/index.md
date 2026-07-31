# Robot Framework Vötsch Climate Chamber Library

**Release:** v26.02  
**Archive:** `rf_votsch_climate_chamber_v26.02.zip`  
**Fixed project root:** `rf_votsch_climate_chamber/`

This project provides a production-oriented Robot Framework library and reusable Python driver for Vötsch/SimServ-compatible climate chambers using TCP port 2049.

## Architecture

```text
Robot Framework suite
        ↓
VotschClimateChamberLibrary
        ↓
ClimateChamber Python driver
        ↓
TCP protocol
        ↓
Climate chamber controller
```

The Robot adapter exposes explicit, readable keywords. The driver owns protocol framing, transport, reconnects, chamber validation, and typed errors.

## Core safety behavior

- Importing the library does not connect to hardware.
- Minimum and maximum temperatures are mandatory for a connection.
- Out-of-range setpoints fail before transmission.
- Stabilization waits have finite defaults.
- Raw protocol commands are not exposed as normal Robot keywords.
- Real-hardware control tests require explicit operator opt-in.

## Quick example

```robot
*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Stop And Disconnect Climate Chamber

*** Test Cases ***
Stabilize At 25 Degrees
    Set Temperature And Wait
    ...    target=25
    ...    tolerance=0.8
    ...    stable_samples=3
    ...    timeout=2 h
    Climate Chamber Temperature Should Be    25    tolerance=0.8
```

## Project documentation

Use the navigation menu for architecture, keyword details, setup guides, examples, safety, testing, troubleshooting, release history, and reviews.


## AI planning contracts

The release contains RFDS-017 and RFDS-018 machine-readable contracts. See **AI Driver Contract** and **Test-Bench Contract** in the navigation.
