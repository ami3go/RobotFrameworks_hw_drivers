# rf_keysight349xx — task folder

Planning artifacts for the Keysight / Agilent 34970A and 34972A driver.

**No implementation exists yet.** This folder contains specification and review documents only.

## Current specification

**`RF_Keysight349xx_Driver_Implementation_Plan_v1.2.md`** — the authoritative plan. Read this one.

## Document chain

| Document | Covers | Status |
|---|---|---|
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.0.md` | Original plan as supplied | Superseded — retained verbatim |
| `SPEC_REVIEW.md` | Review of v1.0 | Closed — B1–B4, N1–N3, N5, N7, N8 resolved in v1.1; N4, N6 deferred |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.1.md` | v1.0 + B1–B4 fixes | Superseded |
| `DEEP_REVIEW_v1.1.md` | Deep review of v1.1 | Closed — C1–C3, M1–M12, X1–X5 all resolved in v1.2 |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.2.md` | v1.1 + all deep-review fixes | **Current** |

Both review documents carry a status banner and are historical. Do not read their findings as open —
each has a disposition table showing where it was resolved.

## What the two review passes found

The **v1.0 review** was structural: a `src/` layout contradicting all twelve existing drivers,
RFDS-008 evidence missing from the source set, measurement not gated on the optional internal DMM,
and a keyword listed ahead of source verification.

The **v1.1 deep review** was technical and safety-focused. Its three critical findings shared one
shape — a safety principle stated in one section and contradicted in another:

- `SYST:ERR?` authorised for retry, though reading the SCPI error queue pops the entry and can
  therefore mask the failed relay or DAC write the queue exists to report;
- `Reset Device` offered unqualified, though a device reset opens all channel relays — precisely
  what the ownership safety model forbids;
- 34972A LAN configuration keywords that sever the transport delivering them, making the plan's own
  reconciliation strategy impossible to execute.

## Open before Phase 1 Gate 1

The **Keysight / Agilent 34970A / 34972A Command Reference** (§2.2) was not available to either
review. Several items are consequently recorded as `SOURCE_VERIFICATION_REQUIRED` rather than
answered, and carried as open questions 3, 4, and 11–15:

- per-card switching topology class (multiplexer, actuator, matrix, RF);
- current-capable channel set per card;
- four-wire pairing offset per card;
- monitor mode disposition;
- permitted DAC output range;
- whether continuity and diode measurement are supported;
- the exact side effect of `Preset Device`.

§1 of the plan forbids resolving device behaviour by assumption, so these are deliberately left
open rather than filled in from inference.

## Next step

Phase 1 Gate 1 — Architecture & Skeleton. First deliverables per §39: package skeleton,
`api/public_api.yaml`, `capabilities/capabilities.yaml`, `ai/ai_contract.yaml` skeleton,
`protocol/vendor_command_coverage.yaml`, and the requirement traceability matrix.
