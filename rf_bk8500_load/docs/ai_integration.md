# AI integration


**Current package:** `bk8500-load==26.16.0`, AI contract revision 12.

The contract records the passing v26.14 physical baseline: 55 public keyword
tests plus one list persistence workflow, all passed on model 8500 firmware
1.84 through COM12. AI planners must still treat RFDS-019 raw protocol-trace
coverage as separate from this callability evidence.

The canonical AI-facing files are delivered at the project root under `ai/`.
An AI test planner should use `ai/ai_contract.yaml` as its primary machine-readable
source of truth.

## Delivered AI files

- `ai/README.md` — agent consumption order and integrity-check instructions.
- `ai/ai_contract.yaml` — RFDS-017 v3.0 driver contract.
- `ai/ai_contract.lock` — contract and keyword-surface integrity lock.
- `ai/system_ai_contract.example.yaml` — RFDS-018 bench composition example.
- `ai/RFDS-017_AI_Driver_Contract_v3.0.md` — driver-contract specification.
- `ai/RFDS-018_AI_Test_Bench_Contract_v1.0.md` — system bench specification.
- `ai/RFDS_Driver_Implementation_Lifecycle_v1.1.md` — implementation lifecycle.

The contract describes all 55 Robot Framework keywords, their signatures,
state transitions, preconditions, postconditions, timing, side effects, risk
levels, errors, exclusive resources, safety rules, verification objectives, and
setup/teardown behavior.

## Programmatic discovery

```python
import bk8500_load

print(bk8500_load.contract_path())
print(bk8500_load.lock_path())
```

For an unpacked package, these functions resolve the root `ai/` directory. A
wheel installation resolves the copied data under `share/rf_bk8500_load/ai`.

## Planning automatic baud detection

An AI planner may enable `auto_detect_baudrate` only during connection setup.
It must treat probing as read-only, budget for up to four serial open/startup
cycles, and record `baudrate_probe_attempts` as evidence. For stable production
fixtures, prefer an explicit numeric baud to avoid unnecessary connection time.
