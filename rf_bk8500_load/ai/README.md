# AI-facing driver information

Read these files in order:

1. `bk8500_load_ai_contract.lock` — verify integrity and keyword count.
2. `bk8500_load_ai_contract.yaml` — machine-readable driver semantics.
3. `system_ai_contract.example.yaml` — example bench composition.
4. RFDS-017, RFDS-018, RFDS-019, and lifecycle specifications.

## Current release

- Package: `rf_bk8500_load_v26.16.zip`
- Distribution: `bk8500-load==26.16.0`
- Contract revision: 12
- Public keyword count: 55

## Physical verification recorded in the contract

The latest preserved physical run tested driver `26.14.0` and passed 56/56:
all 55 public keywords plus the list persistence workflow. Device identity:
model 8500, serial `1687710135`, firmware `1.84`; link COM12 at 9600 baud.

Release 26.16 keeps the verified v26.14 protocol path and adds optional read-only baud detection. The evidence path is
`evidence/hardware_conformance/v26.14_com12_2026-07-28/`.

## Planning rules

- Default to simulation for test construction.
- Require RFDS-018 bench approval before enabling the load input.
- Treat persistent register/list writes as explicit opt-in operations.
- Preserve safe teardown: input OFF, safe state, close connections.
- Do not interpret local echo as instrument acknowledgement.
- Do not claim full RFDS-019 Levels 2–4 from the 56/56 run alone; raw
  per-keyword protocol traces and injected fault vectors are not included.

## Programmatic discovery

```python
import bk8500_load

print(bk8500_load.contract_path())
print(bk8500_load.lock_path())
```

## Release v26.16 connection planning

`Open Load Connection` supports `baudrate=AUTO` and
`auto_detect_baudrate=${TRUE}`. The AI contract defines the probe order,
read-only `0x6A` oracle, identity confirmation, cleanup, timing, and returned
connection evidence. Do not infer success from receipt of 26 bytes alone.
