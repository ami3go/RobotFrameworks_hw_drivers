# Real Chamber Setup

## Preconditions

- Confirm the chamber model and controller support the expected SimServ-compatible TCP protocol.
- Confirm the chamber IP address and TCP port, normally 2049.
- Configure independent high/low temperature alarms on the chamber controller.
- Confirm the DUT, fixtures, cables, airflow, and auxiliary services are rated for the planned profile.
- Confirm the digital-output mapping before operating dryer or compressed air.

## Connectivity check

From the test computer, confirm basic IP reachability and that local firewall policy permits the chamber connection. A successful ping does not prove the chamber protocol is available.

Use the read-only hardware smoke path first. Do not set `ALLOW_CHAMBER_CONTROL=True` until identification, current temperature, setpoint, and status reads have succeeded.

## Evidence to retain

Store the following with the Robot output:

- release version;
- Python and Robot Framework versions;
- chamber model and serial number;
- chamber/controller firmware or status information when available;
- configured local safety limits;
- test start/end time;
- output XML, log HTML, report HTML, and relevant chamber event logs.

## Emergency behavior

Host automation is not a safety controller. Network loss, host crash, or process termination can prevent cleanup commands. Independent chamber protection and an operator-accessible stop method remain mandatory.
