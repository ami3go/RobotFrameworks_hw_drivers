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
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.2.md` | v1.1 + all deep-review fixes | Superseded |
| `GUIDE_CONFORMANCE_REVIEW_v1.2.md` | v1.2 checked against all 19 RFDS guides in `AI_Guides/` | Closed — G1–G15 all resolved in v1.3 |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.3.md` | v1.2 + all guide-conformance fixes | Superseded |
| `CYCLING_REVIEW_v1.3.md` | v1.3 checked guide-by-guide, one RFDS document at a time | Closed — all findings resolved in v1.4 |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.4.md` | v1.3 + both cycling-review cycles | **Current** |

All three review documents carry a status banner and are historical. Do not read their findings as open —
each has a disposition table showing where it was resolved.

## What the three review passes found

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

## Conformance status

**v1.3 resolves all 15 guide-conformance defects.** `GUIDE_CONFORMANCE_REVIEW_v1.2.md` checked v1.2
against all 19 specifications in `AI_Guides/` and found:

- **G1** — §2.1 cites four RFDS versions that do not exist (RFDS-001 v1.2, 002 v1.1, 003 v2.0,
  004 v2.0; the guide set holds v1.1, v1.0, v1.0, v1.0). The traceability matrix §52 requires is
  unbuildable against them.
- **G2** — release identity violates RFDS-011 §6 in every artifact name. Gate ZIPs use an invented
  `-gN` suffix where the standard encodes the gate in `vYY.PP.GG`.
- **G3** — RFDS-013 Capability Model is mandatory and omitted. Six required discovery keywords are
  missing from the public API inventory, and the `capability/` artifact tree is absent.
- **G4** — RFDS-011 Release Process is omitted although RFDS-020, which the plan does cite, lists
  it as a normative reference.

Three further findings (G7–G9) were defects in the v1.2 edits themselves: raw-I/O keyword names,
a reset confirmation gate, and an error-queue bound that each diverged from mechanisms RFDS-002
already specifies. All are corrected in v1.3, and §55 now records the underlying lesson — revisions
must cite a source, not reason from precedent.

**All 19 RFDS guides have now been reviewed and every finding applied.** Four review passes:

| Pass | Scope | Findings | Resolved in |
|---|---|---:|---|
| `SPEC_REVIEW.md` | v1.0, structural + repository convention | 4 blocking, 8 minor | v1.1 |
| `DEEP_REVIEW_v1.1.md` | v1.1, technical + safety coherence | 3 critical, 12 major, 5 consistency | v1.2 |
| `GUIDE_CONFORMANCE_REVIEW_v1.2.md` | v1.2, sampled across the guide set | 4 critical, 11 major | v1.3 |
| `CYCLING_REVIEW_v1.3.md` | v1.3, one guide at a time, all 19 | 3 critical, 12 major, 6 minor | v1.4 |

v1.4 adopts `rfds-core` as a pinned dependency, the RFDS-004 `transport/` tree, the RFDS-007
canonical exception hierarchy and error-code standard, RFDS-001's closed disposition set and release
classes, RFDS-012 GUI-L1, RFDS-018's ten bench sections, and RFDS-010's severity model.

**Phase 1 Gate 1 is unblocked on guide conformance.** The remaining prerequisite is the device
command reference, below.

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
