# Troubleshooting

## Port does not open

- Confirm no terminal, VISA tool, or second process owns the port.
- On Linux, verify the user has access through the distribution's serial-device group or udev policy.
- Do not let the library modify operating-system permissions automatically.

## No response

- Confirm 9600 baud, address 0, parity none, DTR/RTS asserted, and the instrument's `separate` communication mode.
- Confirm SCPI line termination for the actual firmware.
- For TTL DB9 models, use a supported TTL adapter; a conventional RS-232 interface can be electrically incompatible.

## `IndeterminateCommandOutcome`

Do not repeat the command. Query input, short, mode, setpoint, status, and protection where communication is available. Otherwise isolate power/DUT externally and require manual verification.

## Legacy protocol

A valid checksum and 26-byte response do not prove command success. Stable legacy write support remains blocked until return-code position and per-command response layout are captured.
