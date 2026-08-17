# Troubleshooting

## `Set Temperature` reports the previous setpoint

Some chamber controllers acknowledge the write before the public setpoint register updates. The driver therefore polls readback for a finite interval instead of checking only once.

1. Confirm that the chamber is in remote-control mode.
2. Check whether a running program, profile, or local operator lock owns the setpoint.
3. Review the failure details: requested value, last reported value, attempt count, and elapsed time.
4. Keep `setpoint_verify_tolerance_c` narrow enough to prove the write was accepted.
5. Increase `setpoint_verify_timeout_s` only when controller behavior justifies it; do not disable verification.

## Dryer, compressed-air or fan command is rejected

Auxiliary output channels are model- and wiring-dependent. The driver no longer assumes channels 7 and 8 for real TCP hardware, and makes no assumption at all about the fan.

- Leave `settings.auxiliary_outputs.dryer_output_channel`, `compressed_air_output_channel` and `fan_output_channel` as `null` until the exact mapping is qualified.
- `Set Fan`/`Get Fan` drive a digital output. A chamber that regulates ventilation as a percentage setpoint is not supported by these keywords; leave `fan_output_channel` as `null`.
- An unconfigured auxiliary keyword fails locally with `DriverUnsupportedOperationError`; no command is transmitted.
- Safe shutdown marks an unconfigured auxiliary action `SKIP` and still stops the chamber.
- Configure a channel only after verifying the chamber model, firmware, electrical function, and safe-state polarity.

## Disconnect unexpectedly changes chamber state

`Disconnect` follows `settings.safety.safe_shutdown_on_disconnect`. Set it to `false` only for a workflow that explicitly restores state before closing the transport. When importing a dictionary returned by `Get Driver Configuration`, the library removes its read-only runtime annotations and validates the remaining configuration before applying it. Always assert both `valid` and `applied` in a Robot suite.

## Common error families

- `RFDS-CON-001`: verify host, TCP port 2049, routing, and chamber service.
- `RFDS-TRN-*`: inspect TCP connectivity and reconnect explicitly.
- `RFDS-PRO-*`: capture trace and compare it with the protocol vectors.
- `RFDS-ARG-*`: correct the local argument type or range; no command was sent.
- Stabilization timeout: inspect target, chamber load, tolerance, polling interval, and finite timeout.
- Robot import failure: install the project into the active interpreter and verify with `python -c "import rf_votsch_climate_chamber"`.

## Evidence and diagnostics: which one do I want?

This driver has two separate diagnostic mechanisms — reach for the right one:

- **`Get Diagnostics` / `Export Diagnostics`** (pre-existing) — a point-in-time
  snapshot of current session state (connection, transport metrics, and the
  in-memory `protocol_trace` already captured for the active session). Good
  for "what is the state right now".
- **RFDS-008 live evidence** (`evidence.py`, new) — an always-on, append-only
  run under `results/session/rf_votsch_climate_chamber/<run>/`, covering the
  whole library instance's lifetime across every alias: every keyword call
  (`events/operations.jsonl`), every error with category/traceback
  (`events/errors.jsonl`), and every SimServ protocol frame
  (`protocol/exchanges.jsonl`, `protocol/outbound_trace.log` /
  `inbound_trace.log`), correlated by `correlation_id`/`operation_id`, plus a
  SHA-256-hashed `evidence_manifest.json` so the run can be proven unmodified.
  Written automatically; call `Export Diagnostic Bundle` at any point to zip
  the run so far, or let suite end finalize it. Disable with
  `Library rf_votsch_climate_chamber.VotschClimateChamberLibrary
  evidence_enabled=${FALSE}`.

To debug one specific keyword failure: find it in `events/errors.jsonl` (one
JSON object per exception, with `category` — `SAFETY`, `VALIDATION`, `STATE`,
`CONNECTION`, `TRANSPORT`, `PROTOCOL`, `DEVICE`, `RESOURCE`, `ENVIRONMENT`,
`INTERNAL`, `CANCELLED`, or `CLEANUP`, matching this driver's own
`exceptions.py` hierarchy), note its `operation_id`, then search
`events/operations.jsonl` for the exact arguments Robot passed and
`protocol/exchanges.jsonl` for the SimServ frames that operation sent/received
before failing. Validate a run hasn't been tampered with or truncated:

```console
python scripts/validate_evidence.py results/session/rf_votsch_climate_chamber/<run>/
```

`execution_mode` in `run_summary.json` reports `SIMULATOR`, `REAL_HARDWARE`,
or `MIXED` honestly based on which `Connect` resources were actually used
during the run (RFDS-008 §6.6) — never assume real-hardware evidence from a
simulator-only session.
