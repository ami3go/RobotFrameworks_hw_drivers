# Physical hardware conformance suite

`01_all_library_keywords.robot` contains one independently reported test for
each of the 55 public Robot Framework keywords plus one save/reconfigure/
recall persistence workflow.

## Verified result

The preserved v26.14 execution passed **56/56** on:

- B&K Precision 8500;
- serial `1687710135`;
- firmware `1.84`;
- COM12, 9600 baud, address 0;
- Robot Framework 7.4.2;
- Python 3.13.5;
- Windows 11.

Suite duration was 87.159538 seconds and safe teardown passed. Evidence is
stored under
`evidence/hardware_conformance/v26.14_com12_2026-07-28/`.

Release 26.16 expects installed/source version `26.16.0` and optionally exercises read-only automatic baud detection before the same 55-keyword conformance sequence.

## Run safe profile

```powershell
.\scripts\run_hardware_conformance.ps1 -Port COM12
```

## Run complete profile

```powershell
.\scripts\run_hardware_conformance.ps1 -Port COM12 `
    -AllowInputOn:$true `
    -AllowPersistentWrites:$true
```

Persistent mode writes settings register 25 and list slot 8 by default.
Review the bench before enabling these flags.

## Result interpretation

Expected complete result: **56 passed, 0 failed**.

Two failure-level messages may appear while the suite deliberately verifies
error handling for an unknown alias and for calls after all connections are
closed. They are expected only when the enclosing tests pass.

## Serial diagnostic

```powershell
.\scripts\run_serial_diagnostic.ps1 -Port COM12
```

The diagnostic rejects an exact local echo as command acknowledgement,
waits for the real status/data response, and requires a non-empty identity.

## RFDS-019 boundary

This suite proves Robot Framework callability and representative device
readback. Full RFDS-019 Levels 2–4 require per-keyword raw outbound/inbound
traces, protocol vectors, and injected failure/recovery evidence.

## Automatic baud detection profile

PowerShell:

```powershell
.\scripts\run_hardware_conformance.ps1 -Port COM12 -Baudrate 9600 -AutoDetectBaudrate:$true
```

The suite records the actual selected baud in Robot metadata. `BAUDRATE` is the
preferred first attempt; `BAUDRATE_CANDIDATES` defines the fallback order.
