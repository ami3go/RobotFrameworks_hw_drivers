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
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.2.md` | v1.1 + all deep-review fixes | **Current draft — NOT conformant** |
| `GUIDE_CONFORMANCE_REVIEW_v1.2.md` | v1.2 checked against all 19 RFDS guides in `AI_Guides/` | **OPEN — 4 critical, 11 major** |

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

## Conformance status

**v1.2 is not conformant with the RFDS guide set.** `GUIDE_CONFORMANCE_REVIEW_v1.2.md` checked it
against all 19 specifications in `AI_Guides/` and found 15 defects, 4 critical:

- **G1** — §2.1 cites four RFDS versions that do not exist (RFDS-001 v1.2, 002 v1.1, 003 v2.0,
  004 v2.0; the guide set holds v1.1, v1.0, v1.0, v1.0). The traceability matrix §52 requires is
  unbuildable against them.
- **G2** — release identity violates RFDS-011 §6 in every artifact name. Gate ZIPs use an invented
  `-gN` suffix where the standard encodes the gate in `vYY.PP.GG`.
- **G3** — RFDS-013 Capability Model is mandatory and omitted. Six required discovery keywords are
  missing from the public API inventory, and the `capability/` artifact tree is absent.
- **G4** — RFDS-011 Release Process is omitted although RFDS-020, which the plan does cite, lists
  it as a normative reference.

Three further findings (G7–G9) are defects in the v1.2 edits themselves: raw-I/O keyword names,
a reset confirmation gate, and an error-queue bound that each diverge from mechanisms RFDS-002
already specifies.

**Do not enter Phase 1 Gate 1 until v1.3 resolves these.**

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
