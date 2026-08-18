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
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.4.md` | v1.3 + both cycling-review cycles | Superseded |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.5.md` | v1.4 + all device-source resolutions | Superseded |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.6.md` | v1.5 + keyword inventory reconciled with the vendor audit | Superseded |
| `ARTIFACT_REVIEW_v1.6.md` | v1.6 + the generated protocol artifacts | Closed — R1–R5 resolved in v1.7 |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.7.md` | v1.6 + corrected command extraction | Superseded |
| `DEEP_REVIEW_v1.7.md` | v1.7 — implementability axis | Closed — D1–D4 resolved in v1.8 |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.8.md` | v1.7 + authoritative inventory corrected | Superseded |
| `EXECUTABLE_REVIEW_v1.8.md` | v1.8 — ran the mandated checks instead of reading | Closed — E1–E4 resolved in v1.9 |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.9.md` | v1.8 + reconciled extraction, gated checks | Superseded |
| `../scripts/validate_command_coverage.py` | Guard 1, implemented and passing | **Runnable now** |
| `RFDS001_AUDIT_v1.9.md` | v1.9 audited per-requirement against RFDS-001's 132 IDs | Closed — A1–A6 resolved in v1.10 |
| `RF_Keysight349xx_Driver_Implementation_Plan_v1.10.md` | v1.9 + RFDS-001 audit findings | **Current** |
| `../release/requirements_traceability.csv` | All 132 RFDS-001 requirements, dispositioned | **Seeded** |
| `../protocol/vendor_command_coverage.yaml` | 347 vendor commands → dispositions and 121 keywords | **Authoritative binding** |
| `../reference/Keysight_34970A_34972A_Command_Reference.md` | Vendor command reference (§2.2 device source) | Held verbatim |
| `../reference/SOURCE_VERIFICATION.md` | Per-item verification record with line citations | Complete |

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

## Public surface

**~155 keywords**, from two disjoint sources — `api/public_api.yaml` is the union and the only
authoritative inventory:

| Source | Count | Binding |
|---|---:|---|
| `protocol/vendor_command_coverage.yaml` | ~121 | each backed by one or more of 347 SCPI commands |
| RFDS-002 §8/§9, RFDS-013 §7.1, RFDS-014 | ~34 | driver-level; emit no SCPI |

That is roughly two and a half times `rf_ngi_n83624` (62 keywords), and the twelve-phase estimate
predates the number. Scope is re-assessed at Phase 1 Gate 5.

Seven review passes have been run; all are closed. The recurring defect across v1.5–v1.7 was
treating a single-source derivation as a complete inventory — v1.6's extractor knew only block
titles, v1.7's generator knew only SCPI. §9.2 now states the rule: *an inventory assembled from one
source is authoritative only over that source's domain.*

## Verification status

**Guard 1 is implemented and passing.** `scripts/validate_command_coverage.py` reconciles the
coverage map against the reference's own `Commands A-Z` index — a source independent of the
Syntax-section extraction the map was built from — and reports **0 unresolved discrepancies** across
351 commands.

```console
$ python3 scripts/validate_command_coverage.py
  map commands            : 351
  A-Z index commands      : 342
  unresolved discrepancies: 0
  RESULT: PASS
```

Guards 2 and 3 (map → `api/public_api.yaml`, guides → `api/public_api.yaml`) **cannot run yet** —
that file is a Phase 1 Gate 1 deliverable. v1.9 §29.1 now records which steps are gated on which
deliverables and requires them to report `NOT_RUN` rather than `PASS` while their inputs are absent.

Eight review passes have been run; all are closed.

## Requirement traceability

`release/requirements_traceability.csv` is seeded with **all 132 RFDS-001 numbered requirements**,
each carrying a disposition: 129 `NOT_RUN` (specified, verification pending Gate 1) and 3
`NOT_APPLICABLE` with rationale. 51 carry an implementation-artifact reference.

This was audit finding **A6**, and it was the systemic one. Before v1.10 the plan cited 4 of 132
identifiers — all added reactively when a review happened to hit one — so a gap in an area the plan
had never visited had no mechanism that would surface it. That is how A1–A5 survived nine passes.
Seeding converts them from absences into visible rows.

The audit's other five findings are all resolved in v1.10: the deviation schema and its five
release-blocking constraints (§54.1), the device performance contract (§22.4), the resource
declaration with access modes and a default-disabled concurrency posture (§5.5), supply-chain and
security evidence (§50.1), and the Definition of Done now incorporating RFDS-001-ACC-001 (§53).

The other 18 guides carry ~3,195 unnumbered `shall` statements and cannot be seeded by identifier;
they are traced by document and section.

## Open before Phase 1 Gate 1

**The device source is now held** at `reference/Keysight_34970A_34972A_Command_Reference.md`, and
every device-behaviour question is resolved — see `reference/SOURCE_VERIFICATION.md`.

Notable resolutions: continuity and diode do **not** exist on this family (`NOT_APPLICABLE`);
monitor mode does (`ROUTe:MONitor`); current measurement is restricted to channels 21–22 of the
34901A; four-wire pairing is n+10 (34901A) / n+8 (34902A); the DAC range is −12 V to +12 V; there is
no queryable digital-direction command; and `SYSTem:PRESet` has the **identical** module hardware
effect to `*RST` — all relays open, both DACs zeroed, totalizer cleared.

What remains open is deployment facts and project policy, which the command reference cannot answer:
available HIL hardware, firmware exceptions, concurrent-scan policy, calibration-diagnostic
exposure, and relay-cycle-count exposure.

## Next step

Phase 1 Gate 1 — Architecture & Skeleton. First deliverables per §39: package skeleton,
`api/public_api.yaml`, `capabilities/capabilities.yaml`, `ai/ai_contract.yaml` skeleton,
`protocol/vendor_command_coverage.yaml`, and the requirement traceability matrix.
