# Executable Review — Spec v1.8

> **STATUS: CLOSED — all findings resolved.** E1–E4 applied in **v1.9**. The four RTD/FRTD
> `OCOMpensated` commands are added (map now 351), guard 1 requires reconciling two independent
> extractions, §29.1 steps declare their required deliverables and report `NOT_RUN` rather than
> `PASS` when an input is missing, and the map header states its known limits.
> Guard 1 is now implemented at `scripts/validate_command_coverage.py` and **passes with 0
> unresolved discrepancies**.
> **The current specification is `RF_Keysight349xx_Driver_Implementation_Plan_v1.9.md`.**
> Retained as the historical record — do not read the findings below as open.

**Reviewed:** `RF_Keysight349xx_Driver_Implementation_Plan_v1.8.md`, `protocol/vendor_command_coverage.yaml`
**Review date:** 2026-08-18
**Predecessors:** `SPEC_REVIEW.md`, `DEEP_REVIEW_v1.1.md`, `GUIDE_CONFORMANCE_REVIEW_v1.2.md`,
`CYCLING_REVIEW_v1.3.md`, `ARTIFACT_REVIEW_v1.6.md`, `DEEP_REVIEW_v1.7.md`
**Method — new for this pass:** the previous seven passes *read* the artifacts. This pass **runs the
checks §9.2 requires**, and validates the command inventory against a source no previous extractor
used.
**Scope:** specification only — no implementation exists.

---

## 1. Verdict

**The method change paid off immediately, in both directions.**

- **2 of the 3 drift guards §9.2 mandates cannot execute at all** — the artifacts they compare do
  not exist. §29.1 step 24 is unrunnable as written.
- Running the one guard that *can* execute, against an independent source, found **4 genuinely
  missing commands**. The 347-command inventory — itself a correction of a 193-command inventory —
  is still incomplete.

Seven reading passes did not surface either. This is the first pass to attempt execution, and it is
the third distinct extraction method to find commands the previous methods missed.

---

## 2. Critical finding

### E1 — Two of the three mandated drift guards cannot run

**Severity: CRITICAL** (a verification step that cannot execute provides no assurance while
appearing in the acceptance sequence)

§9.2 mandates three checks, and §29.1 step 24 makes them release-blocking. Their operands:

| Guard | Compares | Status |
|---|---|---|
| 1. reference → map | reference ↔ `vendor_command_coverage.yaml` | **runnable** |
| 2. map → public API | map ↔ `api/public_api.yaml` | **cannot run** — `api/public_api.yaml` does not exist |
| 3. guides → public API | RFDS mandatory sets ↔ `api/public_api.yaml` | **cannot run** — same |

Also absent: `capability/capability_model.yaml` and `ai/ai_contract.yaml`, both mandated by §37 and
both operands of §25/§32.1 synchronization requirements.

This is defensible *today* — those artifacts are Phase 1 Gate 1 deliverables and the project has not
entered Gate 1. But the plan does not say so. §29.1 lists the checks as an unconditional sequence,
which means the sequence cannot be run to completion at any point before Gate 1 closes, and nothing
records that.

**Fix:** state which verification steps are gated on which deliverables, so an unrunnable check is
visibly deferred rather than silently skipped. A check that "passes" because its input is missing is
the failure mode RFDS-008 §6.1 exists to prevent.

---

## 3. Major findings

### E2 — The inventory is still incomplete: 4 commands missing

Guard 1 was implemented and run for the first time. As §9.2 requires, the expected set came from an
**independent extraction** — the reference's own `Commands A-Z` index (line 14158), which no
previous extractor used.

Result: **342 commands in the index, 347 in the map, and neither is a superset of the other.**

Genuinely missing from the map, verified present in the reference at lines 7364–7372:

```text
[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated
[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated?
[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated
[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated?
```

The remaining index-only entries are notation artifacts, not misses: `SYST:LFRequency?` is an
abbreviated alias, and `SYSTem:SECurity[:IMMediate]` / `[SENSe:]TOTalize:STARt[:IMMediate]` differ
from the mapped forms only in optional-node brackets.

**This is functionally significant, not clerical.** Offset compensation is a measurement-accuracy
feature for RTD sensors — it cancels thermal EMF in the lead resistance. §14 declares both 2-wire
and 4-wire RTD support, and `Configure RTD` would have shipped unable to control it. The
`FRESistance` and `RESistance` families *do* carry `OCOMpensated` in the map; only the RTD forms
were dropped, so the omission is invisible by inspection.

**Root cause:** the v1.7 Syntax-section extractor missed these four. The family-prefix rule that was
supposed to catch `TRANsducer:RTD:*` only classified commands the extractor had already found — it
could not add ones absent from its input.

### E3 — "An independent extraction" is insufficient; reconciliation is required

§9.2 requires guard 1's expected set to come from "an independent extraction", singular. This pass
demonstrates that one independent extraction is not enough: the Syntax-section method found 12
commands the A-Z index method missed (`ABORt`, `FETCh?`, `INITiate`, `CONFigure?`, `DISPlay`,
`CALibration?`, `[SENSe:]FUNCtion`, …), and the A-Z index found 4 the Syntax method missed.

Neither method is complete. The correct requirement is **reconciliation of at least two independent
extractions**, with every discrepancy resolved to either a real command or a documented notation
artifact.

Three extraction methods have now been used across three revisions, and each found commands the
previous ones missed:

| Revision | Method | Commands | Missed |
|---|---|---:|---|
| v1.6 | block titles | 193 | 154 |
| v1.7 | per-block Syntax sections | 347 | 4 |
| this pass | `Commands A-Z` index | 342 | 12 (different 12) |

### E4 — The coverage claim should state its method's known limits

The map header states the extraction method, which was the v1.7 improvement over a bare "100%
coverage" claim. It should go one step further and record that the method is known to be incomplete
and against what it was reconciled — otherwise a future reader sees "347 commands, extracted from
Syntax sections" and reasonably infers completeness.

---

## 4. What executing confirmed as sound

- **Guard 1's design is correct.** The non-circularity requirement — "shall not reuse the map
  generator's extractor output as its expected set" — is exactly what made this finding possible.
  Had I implemented it lazily against `/tmp/cmds2.txt`, it would have passed and found nothing.
- **The v1.8 union model holds.** All 34 mandatory driver-level keywords and all 121 device-facing
  keywords are present in v1.8; re-verified.
- **`capability_group` is populated** on 321 of 347 commands; the 26 without are the `EXCLUDED` and
  policy-`UNKNOWN` entries, which correctly have no group.

---

## 5. Pattern

Fifth consecutive pass finding a defect in a generated artifact, and the fifth found by changing
method:

| Pass | Method |
|---|---|
| Guide conformance | Read the standards rather than infer from precedent |
| v1.6 self-check | Programmatic diff rather than sampling |
| Artifact review | Map vs reference, rather than map vs itself |
| Deep review v1.7 | Inventory vs the guides, rather than vs the reference |
| **This pass** | **Execute the checks, and validate against a source the extractors never used** |

The consistent shape: every artifact was complete with respect to what its generator consulted. The
defence is not more careful generation — it is **reconciling independent derivations**, which is now
E3's recommendation and is the only technique in this list that does not depend on guessing the next
blind spot in advance.

---

## 6. Required actions

1. **E2** — add the four RTD/FRTD `OCOMpensated` commands and bind them to `Configure RTD`.
2. **E3** — change §9.2 guard 1 to require reconciliation of at least two independent extractions,
   with discrepancies resolved and notation artifacts documented.
3. **E1** — mark §29.1 steps as gated on their deliverables, so an unrunnable check is visibly
   deferred rather than passing vacuously.
4. **E4** — state the extraction method's known limits in the map header.

---

## 7. Status

```text
Reviewed:              v1.8 + vendor_command_coverage.yaml
Method:                executed the mandated guards; independent A-Z index extraction
Implementation:        NOT STARTED — no code written
Critical findings:     1  (E1 — 2 of 3 guards unrunnable)
Major findings:        3  (E2 4 commands missing, E3, E4)
Prior findings:        D1-D4 re-verified as resolved
Recommended next step: v1.9 applying items 1-4, then Phase 1 Gate 1
```
