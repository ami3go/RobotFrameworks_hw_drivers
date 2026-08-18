# Artifact Review — Spec v1.6 and the generated protocol artifacts

**Reviewed:** `RF_Keysight349xx_Driver_Implementation_Plan_v1.6.md`,
`protocol/vendor_command_coverage.yaml`, `reference/SOURCE_VERIFICATION.md`
**Review date:** 2026-08-18
**Predecessors:** `SPEC_REVIEW.md` (v1.0), `DEEP_REVIEW_v1.1.md` (v1.1),
`GUIDE_CONFORMANCE_REVIEW_v1.2.md` (v1.2), `CYCLING_REVIEW_v1.3.md` (v1.3)
**Scope:** specification and generated artifacts only — no implementation exists.

---

## 1. Why this pass exists

The four earlier reviews examined v1.0–v1.3. **v1.4, v1.5, and v1.6 have never been reviewed** —
they were written as fixes and shipped unexamined. `vendor_command_coverage.yaml` has likewise never
been checked by anything other than the script that produced it.

That is the un-reviewed surface, and it is where this pass looked.

**Verdict: two critical defects, both in artifacts I generated. One of them silently removed a
required capability from the public API.**

---

## 2. Critical findings

### R1 — §9.2 deleted two required statistics keywords

**Severity: CRITICAL** (RFDS-010 §9.1 — "materially incorrect … reporting"; a declared capability
silently removed)

Spec §13 has listed these keywords since v1.0:

```text
Get Channel Minimum
Get Channel Maximum
Get Channel Average
Get Minimum Timestamp
Get Maximum Timestamp
```

`vendor_command_coverage.yaml` binds only `CALCulate:AVERage:MAXimum?`,
`:MAXimum:TIME?`, `:PTPeak?`, `:COUNt?`, and `:CLEar`. It has **no entry** for
`CALCulate:AVERage:MINimum?`, `:MINimum:TIME?`, or `:AVERage?`.

Verified against the reference — all three exist:

```text
CALCulate:AVERage:AVERage?          line 604
CALCulate:AVERage:MINimum?          line 609
CALCulate:AVERage:MINimum:TIME?     line 610
```

Because §9.2's table is *generated from the map*, it omits `Get Channel Minimum`,
`Get Channel Average`, and `Get Minimum Timestamp`. And v1.6 declares:

> "Where a narrative list and this table disagree, **this table governs**."

So v1.6 did not merely fail to list three keywords — **it formally deleted two required statistics
capabilities from the public API by declaration.** Minimum and average are not optional extras on a
DAQ unit; §13's own structured return schema still contains `minimum` and `average` fields that
nothing now produces.

Current state check:

| Keyword | In §13 narrative | In coverage map | In §9.2 (authoritative) |
|---|---|---|---|
| `Get Channel Maximum` | yes | yes | yes |
| `Get Channel Minimum` | yes | **no** | **no** |
| `Get Channel Average` | yes | **no** | **no** |
| `Get Minimum Timestamp` | yes | **no** | **no** |
| `Get Maximum Timestamp` | yes | yes | yes |

**Fix:** add the three commands and rebind the three keywords, then regenerate §9.2.

### R2 — The "100% coverage" claim is false

**Severity: CRITICAL** (the audit's entire purpose is to prove systematic review; a false
completeness claim defeats it)

`vendor_command_coverage.yaml` states:

```text
# Commands in reference : 193
# Commands dispositioned: 193  (100% coverage — no command is unlisted)
```

The extractor counted **command blocks**, not commands. The reference documents multiple distinct
commands inside a single block — the block titled `CALCulate:AVERage:MAXimum?` also documents
`MINimum?`, `AVERage?`, and `MINimum:TIME?`. The generator's assertion checked map ↔ extracted-list
consistency, which is circular: it proved the map matched the list the same script produced, not
that the list matched the reference.

Roughly **30 distinct long-form commands** are unlisted, clustered in families where the map used a
"same family" note in place of an entry:

| Family | Unlisted commands include |
|---|---|
| 2-wire resistance | `[SENSe:]RESistance:RANGe`, `:RANGe:AUTO`, `:RESolution`, `:APERture`, `:NPLC`, `:OCOMpensated` |
| Frequency | `[SENSe:]FREQuency:APERture`, `:VOLTage:RANGe`, `:VOLTage:RANGe:AUTO` |
| 2-wire RTD | `[SENSe:]TEMPerature:TRANsducer:RTD:TYPE`, `:RESistance[:REFerence]`, `:OCOMpensated` |
| Statistics | `CALCulate:AVERage:MINimum?`, `:AVERage?`, `:MINimum:TIME?` (see R1) |
| Alarm limits | `CALCulate:LIMit:LOWer`, `:LOWer:STATe` |
| Digital | `[SENSe:]DIGital:DATA:WORD?`, `SOURce:DIGital:DATA:WORD` |
| 4-wire RTD | `[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated` |

**The claim should be withdrawn, not softened.** The correct statement is that 193 command *blocks*
were extracted and dispositioned, and that per-command coverage requires expanding families.

### R2a — 2-wire RTD has no command binding

Spec §14 lists both "2-wire RTD" and "4-wire RTD" as planned sensor support. The map binds only the
`FRTD` (four-wire) transducer commands. `[SENSe:]TEMPerature:TRANsducer:RTD:TYPE` and its siblings —
the two-wire forms — are unlisted, so a declared sensor type has no device binding at all.

This is the same class as R1: a capability the plan claims, with nothing behind it.

---

## 3. Major findings

### R3 — "Family member" notes were used as a coverage substitute

Eighteen map entries carry notes of the form "AC form in same family" or "RESistance form in same
family". That shorthand is reasonable *documentation*, but it was allowed to stand in for an entry,
which is what produced R2. A note is not a disposition — §20 requires every command to "receive an
explicit disposition", and a command mentioned only in another command's note has not received one.

**Fix:** expand every family to explicit rows. If that inflates the file, that is the true size of
the audit.

### R4 — The drift guard added in v1.6 guards the wrong edge

v1.6 §9.2 added:

> `validate_structure.py` shall fail when a keyword appears in `vendor_command_coverage.yaml` but
> not in `api/public_api.yaml`, or the reverse.

That guards **map ↔ public_api**. It does not guard **reference ↔ map**, which is precisely the edge
R1 and R2 fell through. The guard as written would have reported the v1.6 state as clean while two
required keywords were missing.

**Fix:** add a reference-completeness check — re-extract commands from the reference and fail when
any is absent from the map. It must not reuse the extractor's own output as the expected set, or it
reproduces the circularity in R2.

### R5 — `SOURCE_VERIFICATION.md` inherits the same overstatement

It states "No device-behaviour question remains unresolved." That is true for the *questions asked*,
but the questions were drawn from the same incomplete command inventory. Two-wire RTD reference
resistance and offset compensation, for example, were never asked about because the commands were
never listed.

**Fix:** re-verify after the family expansion, and scope the claim to the enumerated command set.

---

## 4. What verified clean

Checked and correct — recorded so the negative findings are not read as a blanket judgement:

- **All 112 mapped keywords are present in v1.6** — the v1.6 reconciliation itself worked; zero
  keywords absent, verified programmatically.
- **`SYSTem:LOCK` binding is sound.** The four locking commands exist as described, and §5.2's
  device-lock / driver-lock composition is a correct reading.
- **DAC range, four-wire pairing offsets, current-channel restriction, monitor mode,
  `INSTrument:DMM`, and the reset/preset state tables** — all re-checked against the reference and
  correctly transcribed.
- **The EXCLUDED set holds up.** Each of the 23 exclusions was re-checked; the LAN writes,
  `SYSTem:LANGuage`, `SYSTem:INTerface`, and `SYSTem:SECurity:IMMediate` classifications are right.

---

## 5. Pattern worth naming

This is the third consecutive review in which the defects were in artifacts **I** produced, and the
third in which they were found by changing *verification method* rather than by looking harder:

| Pass | Defect location | Found by |
|---|---|---|
| Guide conformance | v1.1/v1.2 edits (G7–G9) | Reading the standards instead of inferring from precedent |
| v1.6 self-check | v1.5 keyword inventory | Programmatic diff instead of eyeballing (11 sampled → 40 actual) |
| This pass | Coverage map | Checking the map against the reference instead of against itself |

Each generated artifact has been wrong in a way its own generator could not detect, because the
generator's check was internally circular. The recurring lesson is not "be more careful" — it is
that **a generated artifact must be validated against its source, by a method that does not share
the generator's assumptions.**

R4 is the concrete instance: the guard I added checks the edge I was already thinking about, not the
edge that actually failed.

---

## 6. Required actions

1. **R1** — add `CALCulate:AVERage:MINimum?`, `:AVERage?`, `:MINimum:TIME?`; rebind
   `Get Channel Minimum`, `Get Channel Average`, `Get Minimum Timestamp`; regenerate §9.2.
2. **R2 / R2a / R3** — expand every command family to explicit rows, including the 2-wire
   `RESistance`, `FREQuency`, and `RTD` families; withdraw the "100% coverage" claim until the
   expanded set is verified.
3. **R4** — replace the drift guard with a reference-completeness check that does not reuse the
   extractor's output as its expected set.
4. **R5** — re-run source verification against the expanded inventory.

None requires new information. All are corrections to artifacts produced in the last three
revisions.

---

## 7. Status

```text
Reviewed:              v1.6 + vendor_command_coverage.yaml + SOURCE_VERIFICATION.md
Implementation:        NOT STARTED — no code written
Critical findings:     2  (R1, R2 — plus R2a)
Major findings:        3  (R3, R4, R5)
Verified clean:        keyword reconciliation, SYSTem:LOCK, device facts, EXCLUDED set
Defect origin:         all findings are in artifacts generated in v1.4-v1.6
Recommended next step: v1.7 applying items 1-4 before Phase 1 Gate 1
```
