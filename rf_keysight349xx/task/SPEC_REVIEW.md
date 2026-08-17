# Specification Review — RF Keysight 349xx Driver Implementation Plan

**Reviewed document:** `RF_Keysight349xx_Driver_Implementation_Plan_v1.0.md` (v1.0, 2026-08-17)
**Planned driver:** `rf_keysight349xx`
**Target instruments:** Keysight / Agilent 34970A, 34972A
**Review date:** 2026-08-17
**Reviewer scope:** specification only — no implementation exists yet, and none was written for this review.

---

## 1. Verdict

**APPROVED FOR IMPLEMENTATION, conditional on the four blocking items in section 3.**

The plan is unusually disciplined. Its central strength is that it refuses to invent device
behavior: every capability must trace to an RFDS requirement, a documented device command, a
keyword, a protocol vector, and evidence, and anything not established is forced into an explicit
`UNKNOWN` / `NOT_APPLICABLE` / `EXCLUDED` disposition rather than a plausible guess. The vendor
command coverage audit (§20) and the ownership-aware safety model (§21) are the two artifacts that
most distinguish this from a typical driver plan.

The blocking items are not conceptual defects. Three are conflicts with conventions already
established by the twelve drivers in this repository, and one is a device-capability gate the plan
omits. All four are cheap to fix now and expensive to retrofit after Phase 1.

---

## 2. What the plan gets right

These are worth naming explicitly, because they are the parts that should survive review pressure
unchanged.

| Area | Assessment |
|---|---|
| Acquisition semantics (§12, §42) | Correctly refuses to treat `INITiate` / `FETCh?` / `READ?` / `R?` / `DATA:REMove?` as interchangeable. These differ in buffering and reading-memory side effects and are routinely conflated; calling it out twice is appropriate. |
| Retry policy (§22) | The split between bounded retry for idempotent queries and *no* blind retry for state-changing writes is correct. The query/compare/reconcile recovery strategy is the right answer for uncertain delivery. |
| Ownership-aware safety (§21) | Correct for a switch/DAQ mainframe on a shared bench. "Never blindly open every relay" and "never blindly zero every DAC" are the right defaults; a driver that safe-shutdowns the whole frame is a hazard, not a feature. |
| Safety config realism (§21) | The example uses 201/202 for switching, 301 for a digital port, and 304/305 for DAC. Those match real 34907A channel assignments, which indicates the author worked from the actual hardware model rather than a template. |
| Unknown dispositions (§11.2) | Marking continuity and diode `UNKNOWN` and explicitly forbidding a substitute mapping onto resistance or voltage is exactly right. |
| Vendor command audit (§20) | Forces systematic review of the command reference and makes exclusions visible rather than silent. This is the artifact that proves coverage was considered. |
| Trace-before-connect (§28) | Requiring capture to start before connection and identity traffic closes a real evidence gap — connection-time protocol operations are the ones most often missing from conformance evidence. |
| Simulator honesty (§27) | Requiring simulator evidence to be labeled as such, and barring it from claiming physical accuracy or hardware safety validation, is the correct boundary. |
| Model gating (§18) | 34972A-only functionality raising `DriverUnsupportedOperationError` on a 34970A is the right normalization. |

---

## 3. Blocking findings

### B1 — `src/` layout contradicts every existing driver in this repository

**Where:** §37 specifies `src/rf_keysight349xx/`.

**Problem:** All twelve drivers in this repository use a flat package root
(`rf_<driver>/rf_<driver>/`). None uses a `src/` layout. Verified across
`rf_votsch_climate_chamber`, `rf_ngi_n83624`, `rf_hp34401a`, `rf_tbs1000c`, and
`rf_ea_ps9000t` — `src/` absent in all, flat package present in all.

This is not cosmetic. Per-driver structural validators assert a fixed package root
(`rf_votsch_climate_chamber/scripts/validate_structure.py` reports "fixed root
rf_votsch_climate_chamber"), and the NGI task document explicitly required a flat repository
layout. A `src/` driver would be the only one of its kind and would need bespoke tooling.

**Recommendation:** Change §37 to `rf_keysight349xx/rf_keysight349xx/`. If `src/` is genuinely
wanted, it must be raised as a repository-wide decision with an approved deviation, not introduced
silently by one driver.

### B2 — RFDS-008 (evidence) is missing from the authoritative source set and the package structure

**Where:** §2.1 source list; §37 package structure.

**Problem:** The source set lists RFDS-001–007, 009, 010, 012, 014, 015, 017, 018, 019 and the
lifecycle document. RFDS-008 is absent. Yet **all twelve drivers in this repository implement an
RFDS-008 live evidence engine** (`evidence.py` present in every one), producing `run_summary.json`,
`events/`, `protocol/`, `evidence_manifest.json`, and `integrity/checksums.sha256`.

§5 asks the driver to "produce observable protocol evidence" and §28 depends heavily on evidence
artifacts, but no evidence engine is specified, `evidence.py` does not appear in §37, and the
governing standard is not in the baseline. The plan therefore requires evidence outputs without
specifying the subsystem that produces them.

**Recommendation:** Add RFDS-008 to §2.1, add `evidence.py` to §37, and add an evidence-engine
deliverable to Phase 1 Gate 3 (which already covers "logging/evidence infrastructure" but has no
standard behind it).

Also confirm intent for the other absent standards — **RFDS-011, RFDS-013, RFDS-016** are likewise
not listed. RFDS-013 (capability authority) is referenced by recent `rf_hp34401a` work, so its
omission looks unintentional. If any are genuinely out of scope, say so explicitly rather than
leaving them unmentioned; the plan's own principle is that absence must be a recorded disposition.

### B3 — Measurement capability is not gated on the internal DMM

**Where:** §11 measurement engine; §4.3 module discovery; §6 connection workflow.

**Problem:** On the 34970A/34972A the internal DMM is an **option**. A mainframe without it (or
with it disabled) can still switch and route, but cannot measure. The plan models this nowhere in
the capability path: §4.3 discovers *modules* in slots 100/200/300 but says nothing about DMM
presence, §6 builds the "effective capability model" without consulting it, and §11's validation
list covers channels, card compatibility, model restrictions, and argument ranges — but not DMM
availability.

The concept is not entirely absent: "internal DMM installed/enabled" appears in the AI contract
state model (§25) and the simulator state list (§27). It simply never reaches the capability gate
or the measurement preconditions, so the two sections disagree with §11.

**Consequence:** every measurement, scan, statistics, and temperature keyword would attempt
transmission on a switch-only frame and fail with a device error instead of a clean
`DriverUnsupportedOperationError`.

**Recommendation:** Add DMM presence/enabled discovery to §6, make it part of the effective
capability model, and add it to §11.1 validation. Treat it as a first-class gate alongside model
gating (§18). Note this also affects Phases 3, 4, and 5.

### B4 — `Get Digital Direction` may not correspond to a real device command

**Where:** §16.2 digital output.

**Problem:** The plan lists `Get Digital Direction` as a planned keyword and states that direction
changes "shall be represented as explicit state transitions and side effects." On the 34907A,
digital I/O channels 301/302 are bidirectional and direction is generally implicit in whether the
channel is read or written; a queryable direction register is not part of the standard command
set. If no such command exists, this keyword cannot be implemented without inventing behavior —
precisely what §1 and §11.2 forbid.

**Recommendation:** Give `Get Digital Direction` (and the §16.2 direction-transition requirement)
an explicit disposition in the vendor command coverage audit before Phase 7. If the command
reference establishes no queryable direction, mark it `UNKNOWN` or `NOT_APPLICABLE` and drop the
keyword rather than synthesizing direction state in the driver. Flagged here because it is the one
place in the plan where a keyword appears to have been listed ahead of source verification.

---

## 4. Non-blocking findings

### N1 — Robot library identity is under-specified

§3.1 gives `Robot library: rf_keysight349xx.library` (a module path). Repository convention is to
also export a `<Device>Library` class alias from the package root — `rf_ngi_n83624` exposes
`NGI_N83624Library`, `rf_votsch_climate_chamber` exposes `VotschClimateChamberLibrary`. Decide the
exported class name in the public API contract (§9 already defers keyword naming there) so suites
can use the conventional `Library    rf_keysight349xx.Keysight349xxLibrary` form.

### N2 — Version scheme differs from existing drivers

§3.2 uses three-part `v26.01.00`; existing drivers use two-part (`26.01`, `26.02`). Harmless in
isolation, but release tooling and any cross-driver version checks should be confirmed to accept
it. Note also that `rf_ngi_n83624` carries `RELEASE_VERSION = "26.02"` with distribution version
`26.2` — a source/distribution split that is easy to get wrong; define both explicitly here.

### N3 — Statistics return schema is incomplete relative to its own keyword list

§13 lists `Get Minimum Timestamp` and `Get Maximum Timestamp`, but the recommended structured
return (`channel`, `minimum`, `maximum`, `average`, `peak_to_peak`, `count`) omits them. Either add
timestamp fields to the schema or state that timestamps are separate scalar keywords.

### N4 — Continuity/diode will likely resolve to NOT_APPLICABLE

Open questions 3 and 4 ask whether continuity and diode measurement are supported. The 34970A/34972A
internal DMM function set is DCV, ACV, DCI, ACI, 2-wire and 4-wire resistance, frequency, period,
and temperature; continuity and diode test are 34401A-class DMM functions. The expected resolution
is therefore `NOT_APPLICABLE`, not `UNKNOWN`. **Confirm against the command reference before
recording it** — this note is a prediction of the outcome, not a substitute for the source check the
plan rightly demands.

### N5 — Relay cycle count read disposition is unstated

§19 excludes relay-cycle counter *reset*, but does not say whether *reading* the count is an
acceptable read-only public diagnostic. This is relay-maintenance data with real operational value.
It falls under open question 5; make it an explicit line in the vendor coverage audit.

### N6 — HIL matrix combinatorics should be scoped early

§30 crosses 2 mainframes, 4 transports, and 8 modules. Because transports are already model-bound,
the practical matrix is 4 transport combinations × 8 modules = 32 entries, each needing an explicit
status. That is achievable, but open question 8 ("which real hardware combinations are available")
should be answered before Phase 11 so the D2 promotion criteria are known rather than discovered.

### N7 — Example count

§31 says "at least ten runnable examples are required" and then lists fifteen. Not a defect;
confirm fifteen is the target so the acceptance check is unambiguous.

### N8 — Editorial

Line 1929: "iacceptance" → "acceptance". Line 1930: stray trailing list marker `1.`. The document is
stored here verbatim and unmodified; correct these in v1.1 upstream.

---

## 5. Scoring

| Area | Weight | Score | Weighted |
|---|---:|---:|---:|
| Scope and objective | 10% | 9.5 | 0.95 |
| Architecture and layering | 10% | 8.0 | 0.80 |
| Safety model | 20% | 9.8 | 1.96 |
| API completeness and capability gating | 15% | 8.0 | 1.20 |
| Test and conformance strategy | 15% | 9.7 | 1.46 |
| Hardware qualification boundary | 10% | 9.6 | 0.96 |
| Packaging and repository fit | 5% | 6.0 | 0.30 |
| Documentation and examples | 5% | 9.5 | 0.48 |
| Evidence and traceability | 10% | 8.5 | 0.85 |

**Overall: 8.96 / 10.**

Deductions concentrate in three places: packaging (B1, `src/` conflicts with the whole repository),
API/capability gating (B3, the missing internal-DMM gate), and evidence (B2, RFDS-008 absent from
the baseline). Safety, testing, and acquisition semantics score high and need no rework.

---

## 6. Recommended actions before Phase 1 Gate 1 closes

1. **B1** — change §37 to the flat `rf_keysight349xx/rf_keysight349xx/` layout.
2. **B2** — add RFDS-008 to §2.1 and `evidence.py` to §37; state the disposition of RFDS-011, 013, 016.
3. **B3** — add internal-DMM discovery to §6, the capability model, and §11.1 validation.
4. **B4** — give `Get Digital Direction` an explicit source-verified disposition.
5. Resolve N1 (exported class name) and N2 (version scheme) while the public API contract is still open.
6. Carry N4, N5, N6 into `release/open_questions.yaml` as tracked items rather than review comments.

None of these require implementation work to resolve; all are document changes plus one command
reference check. The plan's phase structure and gate model are sound and need no revision.

---

## 7. Status

```text
Specification stored:   task/RF_Keysight349xx_Driver_Implementation_Plan_v1.0.md (verbatim, unmodified)
Implementation:         NOT STARTED — no code written
Blocking findings:      4 (B1-B4), all document-level
Non-blocking findings:  8 (N1-N8)
Next gate:              Phase 1 Gate 1 (Architecture & Skeleton)
```
