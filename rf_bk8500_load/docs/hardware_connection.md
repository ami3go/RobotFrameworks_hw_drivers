# Hardware connection and first communication


## Verified connection

A complete physical run passed 56/56 tests on COM12 at 9600 baud,
address 0, with model 8500 serial `1687710135` firmware `1.84`.
`Get Load Connection Info` reported DTR and RTS asserted and the
echo-aware response path completed successfully.

## Electrical interface warning

The load's rear DB9 uses TTL signalling, not standard RS-232 voltage levels.
Use the B&K/ITECH USB-to-TTL adapter or an electrically equivalent level
shifter. A direct PC RS-232 connection may damage the load.

## Preparation

1. Keep the load input OFF and disconnect the DUT power source.
2. Connect the approved USB-to-TTL adapter.
3. Set the instrument and driver to the same baud rate: 4800, 9600, 19200, or
   38400.
4. Confirm that the serial port is not open in another application.
5. Confirm wiring, polarity, current rating, airflow, and protection limits.

## Identity-only check

Windows:

```powershell
.\scripts
un_example.ps1 01_identity_and_limits -Simulated:$false -Port COM4
```

Linux:

```bash
SIMULATED=False PORT=/dev/ttyUSB0 ./scripts/run_example.sh 01_identity_and_limits
```

The driver asserts DTR and RTS during open. This sequence passed the preserved COM12 physical run. If either line cannot be asserted,
connection fails with a targeted diagnostic instead of waiting for repeated
protocol timeouts.

## First powered test

Use a current-limited source and conservative values. Review and edit the
protection limits in `examples/resources/bk8500_example.resource` before
running a load-regulation example on hardware.

## Baud-rate discovery

The supported front-panel rates are 4800, 9600, 19200, and 38400. Fixed baud
is preferred for deterministic production benches. For portable benches or
unknown instrument configuration, enable automatic detection:

```robotframework
Open Load Connection    port=${LOAD_PORT}    baudrate=${PREFERRED_BAUD}
...    auto_detect_baudrate=${TRUE}
```

Each failed rate fully closes and reopens the COM port, including the verified
DTR/RTS sequence and startup delay. Detection never enables the load input.
