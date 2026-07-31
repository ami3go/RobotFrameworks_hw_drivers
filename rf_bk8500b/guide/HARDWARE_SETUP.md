# Hardware Connection and Safety

## Required equipment

- B&K Precision 8500B-series electronic load.
- Correct communications cable/adapter and driver.
- Current-limited DC source suitable for the load and DUT.
- Wiring rated for the maximum planned current and power.
- Emergency means to disable source output.

## Before running an active-load example

1. Verify polarity at the electronic-load input.
2. Set the source current limit conservatively.
3. Confirm the load model's voltage, current, and power ratings.
4. Confirm the DUT and cable safe operating areas.
5. Begin with the electronic-load input disabled.
6. Use a low current or power setpoint for the first active test.
7. Keep short-circuit mode disabled unless a reviewed test explicitly requires it.
8. Confirm that test teardown disables the load input.

## Communication-only qualification

Run `examples/01_identify.robot` first. It verifies connection, identity, and
capability data without intentionally enabling the load input.

## Hardware evidence

Store hardware execution reports outside the source tree or in a dedicated
release evidence folder. Record:

- Package version and Git revision.
- Python and Robot Framework versions.
- Instrument model, serial number, and firmware version.
- Communications interface and adapter.
- Source model and configured limits.
- Test wiring and measured conditions.
