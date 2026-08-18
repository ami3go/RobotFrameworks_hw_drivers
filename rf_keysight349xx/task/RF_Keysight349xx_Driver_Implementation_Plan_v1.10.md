# RF Keysight 349xx Robot Framework Driver — Implementation Plan

**Document version:** 1.10  
**Planned driver:** `rf_keysight349xx`  
**Target instruments:** Keysight / Agilent 34970A and 34972A  
**Target release family:** `rf_keysight349xx_v26.01` (RFDS-011 §5.2)  
**Status:** Implementation planning specification  
**Date:** 2026-08-17  
**Supersedes:** v1.9; v1.0–v1.9 retained alongside this document

---

## 0. Revision History

### v1.10 — 2026-08-18

Applies `RFDS001_AUDIT_v1.9.md` (A1–A6). That audit checked v1.9 against RFDS-001's **132 numbered
requirements** — the only guide carrying stable identifiers — and found six major gaps, all in areas
this plan had never visited.

| ID | Gap | Resolution |
|---|---|---|
| A6 | Only 4 of 132 RFDS-001 identifiers cited; nothing bound the requirement set into §52 | `release/requirements_traceability.csv` **seeded with all 132**, each carrying a disposition |
| A1 | No deviation schema, none of RFDS-001-DEV-002's five constraints | §54.1 adds both, and applies them to the two deviations the plan already contemplates |
| A2 | No device-specific performance contract — none of PERF-001's ten fields | §22.4 adds the contract |
| A3 | §53 not derived from RFDS-001-ACC-001's P1 criteria | §53 now cites and incorporates ACC-001 |
| A4 | No driver-level resource declaration or access modes | §5.5 adds both; default concurrency posture stated |
| A5 | Supply-chain evidence lacked licences, vulnerability status, binary provenance | §50.1 adds RFDS-001-SEC-002/003 |
| — | `VIS-001`/`VIS-002` had no disposition | Recorded `NOT_APPLICABLE` with rationale in the traceability CSV |

**A6 was the systemic finding and is fixed first.** The other five were invisible because nothing
enumerated the requirement set; with all 132 seeded they are now rows that read `NOT_RUN` rather than
gaps nobody was looking for.

### v1.9 — 2026-08-18

Applies `EXECUTABLE_REVIEW_v1.8.md` (E1–E4) — the first review to **run** the mandated checks rather
than read the specification.

| ID | Finding | Resolution |
|---|---|---|
| E1 | 2 of the 3 §9.2 drift guards cannot execute — `api/public_api.yaml`, `capability_model.yaml` and `ai_contract.yaml` do not exist, so §29.1 step 24 is unrunnable and would pass vacuously | §29.1 steps now declare their required deliverables; a check whose input is absent is `NOT_RUN`, never `PASS` |
| E2 | Four commands genuinely missing — the RTD and FRTD `OCOMpensated` set/query forms. Offset compensation is an RTD accuracy feature, so `Configure RTD` would have shipped unable to control it | Added and bound; map now 351 commands |
| E3 | §9.2 required "an independent extraction"; three methods have now produced 193 / 347 / 342 commands with none a superset of the others | Guard 1 now requires **reconciliation of at least two** independent extractions with every discrepancy resolved |
| E4 | The coverage claim did not state its method's known limits | Header records both extractions, the discrepancies resolved, and that a third method may still find more |

**Why E2 was invisible.** The `RESistance` and `FRESistance` families already carried
`OCOMpensated`; only the RTD forms were absent. Nothing in the map looked wrong by inspection — the
gap was findable only by comparing against a source the extractor had never used.

### v1.8 — 2026-08-18

**Corrective revision** applying `DEEP_REVIEW_v1.7.md` (D1–D4).

| ID | Finding | Resolution |
|---|---|---|
| D1 | §9.2 was authoritative for the keyword inventory but generated from the vendor command map, so **33 of 34 mandatory RFDS keywords were absent** — all RFDS-014 configuration, all RFDS-013 capability, 9 of 10 RFDS-002 universal, `Safe Shutdown`, `Recover Connection`, all raw I/O | `api/public_api.yaml` becomes the sole authoritative inventory, as the **union** of two disjoint sources. §9.2 now presents the device-facing table as one input |
| D1 | The drift guard would have **failed the build for correctly implementing the mandatory API** | Rewritten: driver-level keywords are exempt from the command-binding check |
| D2 | Granting a generated artifact precedence over normative specifications inverts RFDS-001 §7.1 | Precedence scoped to the command↔keyword binding only |
| D3 | Surface understated as 121 keywords | Restated as ~155 |
| D4 | No keyword-to-capability-group traceability, so §8's completeness rule was uncheckable | `capability_group` added to every mapped command; per-group completeness check added |

**Root cause, and the rule that prevents recurrence.** Four consecutive revisions produced an
artifact that was complete with respect to the source its generator knew about and incomplete with
respect to a source it never consulted. v1.6's extractor knew only block titles; v1.7's generator
knew only SCPI commands. §9.2 now states the general rule: **an inventory assembled from one source
is authoritative only over that source's domain.**

### v1.7 — 2026-08-18

**Corrective revision** applying `ARTIFACT_REVIEW_v1.6.md` (R1–R5). Both critical findings were
defects in artifacts generated in v1.4–v1.6.

| ID | Finding | Resolution |
|---|---|---|
| R1 | The map omitted `CALCulate:AVERage:MINimum?`, `:AVERage?`, `:MINimum:TIME?`, so §9.2 **deleted** `Get Channel Minimum`, `Get Channel Average`, `Get Minimum Timestamp` from the public API | All three commands added and keywords restored |
| R2 | "193 commands, 100% coverage" was false — the extractor read block *titles*, and the generator asserted the map against its own output (circular) | Re-extracted from each block's **Syntax** section: **347** commands. Claim restated with the method named |
| R2a | 2-wire RTD had no command binding although §14 claims the sensor type | `[SENSe:]TEMPerature:TRANsducer:RTD:*` bound to `Configure RTD` |
| R3 | "same family" notes stood in for entries | Every family expanded to explicit rows: 2-wire `RESistance`, `FREQuency`, AC `VOLTage`/`CURRent`, `LIMit:LOWer`, `DIGital…WORD` |
| R4 | The v1.6 drift guard checked map ↔ `public_api.yaml`, not reference ↔ map — the edge that failed | Guard replaced; see §9.2 |
| R5 | `SOURCE_VERIFICATION.md` scoped its claim to an incomplete inventory | Scope restated |

Also newly bound: `CALCulate:SCALe:GAIN` — §17 has listed `Set Scaling Gain` since v1.0 with no
command behind it — plus `DIAGnostic:PEEK:SLOT:DATA?` (`EXCLUDED`) and `SYSTem:LOCal`/`REMote`
(`INTERNAL`).

Counts move from 193 commands / 112 keywords to **347 commands / 121 keywords**.

### v1.6 — 2026-08-18

**Corrective revision.** Producing `protocol/vendor_command_coverage.yaml` mapped all 193 vendor
commands to 112 planned keywords — but **40 of those keywords appeared nowhere in v1.5**. The
narrative sections (§9–§18) had been written before the vendor audit and were never reconciled with
it, so the plan's own two descriptions of its public surface disagreed.

This revision makes the coverage map authoritative and derives the keyword inventory from it
mechanically, so the two cannot diverge again.

| Change | Detail | Sections |
|---|---|---|
| Keyword inventory reconciled | New §9.2 lists all 112 planned keywords with their vendor commands, generated from the coverage map | §9.2 |
| Coverage map made authoritative | The map, not the prose, is the source of truth for the command-to-keyword binding | §9.2, §20 |
| Locking bound to a real mechanism | §5.2 described a design problem the device already solves: `SYSTem:LOCK:REQuest?`, `:RELease`, `:OWNer?`, `:NAME?` exist | §5.2 |
| Drift guard added | `validate_structure.py` shall fail when a keyword exists in one artifact and not the other | §9.2, §29.1 |

The narrative sections are retained as rationale — they explain *why* a capability exists and what
constrains it. Where a narrative list and §9.2 disagree, §9.2 governs.

### v1.5 — 2026-08-18

The Keysight 34970A/34972A Command Reference is now held at
`reference/Keysight_34970A_34972A_Command_Reference.md` and is the §2.2 device source. Every
`SOURCE_VERIFICATION_REQUIRED` item is resolved against it; the full record with line citations is
`reference/SOURCE_VERIFICATION.md`.

| Item | Resolution from source | Sections |
|---|---|---|
| Continuity / diode (OQ-3, OQ-4) | `NOT_APPLICABLE` — zero occurrences in the reference; neither function exists | §11.2 |
| Monitor mode (OQ-11) | `PUBLIC` — `ROUTe:MONitor` group exists; contends with scan for the internal DMM | §12.1 |
| Card topologies (OQ-12) | Resolved — 34901A/02A/08A multiplexer, 34903A actuator, 34904A 4×8 matrix (row/column crosspoint), 34905A/06A RF | §15.2 |
| Current channels (OQ-12) | Resolved — channels 21 and 22 of the 34901A only | §11.3 |
| Four-wire pairing (OQ-12) | Resolved — n+10 (34901A), n+8 (34902A) | §14.1 |
| DAC range (OQ-13) | Resolved — −12 V to +12 V, 0.001 V resolution | §16.4 |
| `Preset Device` side effect (OQ-15) | Resolved — identical module hardware effect to `*RST`: all relays open, both DACs zeroed, totalizer cleared | §9.1 |
| `Get Digital Direction` (B4) | `NOT_APPLICABLE` — no queryable direction command exists | §16.2 |
| Internal DMM discovery (B3) | Confirmed — `INSTrument:DMM` is the mechanism; distinguishes disabled from not installed | §4.4, §6 |

**The reset finding is more serious than the deep review recorded.** C2 claimed `Reset Device` opens
all relays; the reference shows it also zeroes both DACs and clears the totalizer, and that
`SYSTem:PRESet` has the identical module hardware effect. Both keywords therefore violate §21's
"never blindly open or close every relay" **and** "never blindly zero every DAC" simultaneously.
§9.1 is updated accordingly.

Remaining open questions are deployment facts or project policy, which the command reference cannot
answer: available HIL hardware (OQ-8), firmware exceptions (OQ-9), concurrent-scan policy (OQ-14),
read-only calibration diagnostics (OQ-5), relay-cycle-count exposure.

### v1.4 — 2026-08-18

Applies `CYCLING_REVIEW_v1.3.md` (both cycles), the pass that took each RFDS guide in turn rather
than sampling across them. 21 findings from cycle 1 plus cycle 2's review of RFDS-006, 010, 012 and
018.

| ID | Finding | Resolution | Sections |
|---|---|---|---|
| C001-1 | §52 permitted eight traceability dispositions; RFDS-001-CLS-003 fixes four | Reduced to the closed set; `NOT_RUN` barred from acceptance | §52 |
| C001-2 | No release-class declaration though RFDS-001 §8.2 keys applicability off it | Declaration required per packaged revision | §51 |
| C001-3 | RFDS revision set not recorded per release | `release/rfds_revisions.yaml` added | §37, §52 |
| C003-1 | `rfds-core` never declared, though RFDS-003 §8.2 requires it | Named, pinned, and made a Gate 2 deliverable | §5.3, §37 |
| C003-2 | No prohibition on a private base-class copy | RFDS-003 §8.3 prohibition stated | §5.3 |
| C003-3 | `rfds-core` version not surfaced | Required in driver info, diagnostics, `software_inventory.json` | §5.3, §7.1 |
| C004-1 | `transports/` layout is not RFDS-004 §6's `transport/` tree | Replaced with the mandated tree and `backends/` layer | §37 |
| C004-2 | RFDS-004/RFDS-005 `src/` conflict resolved silently | Recorded as an interpretation note per RFDS-001-GOV-004 | §2.3, §37.1 |
| C004-3 | Retry preconditions weaker than RFDS-004 §14 | `NEVER` default stated; the five proven conditions adopted | §22.1 |
| C004-4 | Transport guide and connection examples missing | Added | §31, §34 |
| C007-1 | RFDS-007 §6 canonical exception hierarchy never adopted | Adopted in full; `DriverOperationUncertainError` bound to §22.2 | §2.4 |
| C007-2 | RFDS-007 §8 error code standard never referenced | `RFDS-<DOMAIN>-<NNN>` required on every exception | §2.4, §28.1 |
| C007-3 | Mandatory exception data and message format unstated | Bound to RFDS-007 §10–§12 | §2.4, §10.1 |
| C009-1 | `results/.gitkeep` absent, leaving evidence no declared home | Added | §37 |
| C014-1 | Packaged `resources/configuration/` missing | Added and kept in sync by `generate_metadata` | §37 |
| C014-2 | `config/migrations/README.md`, `tests/data/configuration/` missing | Added | §37 |
| C015-1 | Plugin manifest had no packaged location | Placed at `rf_keysight349xx/resources/plugin_manifest.json` | §37 |
| C015-2 | `tests/plugin/` layer absent | Four mandated tests added | §37, §29.1 |
| C015-3 | `docs/plugin_integration.md` missing | Added | §33 |
| C015-4 | `rfds.drivers` entry-point group not named | Named | §24 |
| C006-1 | Python baseline never declared | `requires-python` and the RFDS-006 §5 source rules stated | §5.4 |
| C010-1 | Review severities and statuses not bound to RFDS-010 | §36 bound to RFDS-010 §7–§10 | §36 |
| C012-1 | RFDS-012 in the source set but unaddressed | GUI compatibility level declared; eligibility criteria adopted | §2.5 |
| C018-1 | §26 bench sections did not match RFDS-018 §6 | Replaced with the ten mandated sections | §26 |
| C018-2 | Deployed bench contract location unstated | Stated as outside the driver package tree | §26 |

### v1.3 — 2026-08-18

Applies `GUIDE_CONFORMANCE_REVIEW_v1.2.md`, the first review performed against the 19 RFDS
specifications actually present in `AI_Guides/`. v1.0–v1.2 were assessed on internal coherence and
repository convention; none checked the normative documents. That check found the plan's declared
baseline itself to be wrong.

| ID | Finding | Resolution | Sections |
|---|---|---|---|
| G1 | §2.1 cited four RFDS versions absent from the guide set (001 v1.2, 002 v1.1, 003 v2.0, 004 v2.0) | All citations corrected to the versions held in `AI_Guides/`; document IDs added | §2.1 |
| G2 | Release identity violated RFDS-011 §6 in every artifact name | Replaced with `vYY.RR` public and `vYY.PP.GG` engineering-gate forms | §3.2, §3.3, §35 |
| G3 | RFDS-013 Capability Model mandatory, present, and omitted | Adopted: six mandatory discovery keywords, `capability/` tree, `tests/capability/` layer | §2.1, §7.2, §37 |
| G4 | RFDS-011 Release Process omitted though normatively referenced by RFDS-020 | Added to the source set and bound to release sections | §2.1, §50 |
| G5 | RFDS-016 given an `UNKNOWN` disposition; no such document exists | Corrected to "no such document in the guide set" | §2.1.2 |
| G6 | RFDS-008 cited under an invented title, and §2.1.1 derived from observation rather than the standard | Title corrected; artifact contract re-derived from RFDS-008 §11 and §6 | §2.1, §2.1.1 |
| G7 | Raw-I/O keyword names ignored RFDS-002 §9.11 permitted canonical names | Renamed to the canonical set; mandated tags added | §8.1 |
| G8 | `Reset Device` confirmation argument diverged from the RFDS-002 §9.8 canonical signature | Canonical signature restored; hazard handled through §9.8 documentation duties and a bench-contract gate | §9.1 |
| G9 | Error-queue bound placed in configuration; RFDS-002 §9.2 defines it as `max_count=100` | Moved to the canonical argument; mandated error dictionary schema added | §10.1, §10.2 |
| G10 | §37 layout diverged from RFDS-005 §6 in mandatory paths | Aligned: `ai/`, `config/`, `capability/`, `robot_resources/`, `generated/`, `tests/` corrected | §37 |
| G11 | §32 script set diverged from RFDS-005 §6 | Replaced with the mandated script set | §32 |
| G12 | §36 review artifacts diverged from RFDS-005 §6 | Replaced with the mandated review artifacts | §36 |
| G13 | §33 omitted five mandatory documentation pages | Added | §33 |
| G14 | §35 history naming non-conformant | Corrected; `history/README.md` added | §35 |
| G15 | AI contract identity binding to the plugin manifest unstated | Added; §25 now defers to RFDS-017 as sole normative source | §25 |

Three of these (G7, G8, G9) were defects introduced by the v1.2 edits themselves — mechanisms
invented in response to the deep review that the standards had already specified. The lesson is
recorded in §55: the source-first principle governs revision as much as authorship.

### v1.2 — 2026-08-18

Applies the critical, major, and consistency findings from `DEEP_REVIEW_v1.1.md`.

| ID | Finding | Resolution | Sections |
|---|---|---|---|
| C1 | `SYST:ERR?` authorised for bounded retry, but reading the SCPI error queue pops the entry, so a retry after a lost response silently discards an error | Destructive-read category added; retry prohibited for `SYST:ERR?`, `R?`, `DATA:REMove?` | §22.1, §22.3 |
| C2 | `Reset Device` offered unqualified although `*RST` opens all channel relays, contradicting §21 | Reclassified high-risk and confirmation-gated; relay side effect stated | §9.1 |
| C3 | 34972A LAN configuration severs the connection delivering it, making §22.2 reconciliation impossible | Split into LAN query (public) and LAN configuration (excluded by default) | §18.1, §18.2 |
| M1 | Raw protocol I/O declared as a capability group but never specified | Full specification added: enable gate, risk class, evidence capture, non-exemption from §19/§21 | §8.1 |
| M2 | Contract synchronization mandated with no generator or validator | Metadata generation and contract validation added to scripts and the verification sequence | §32, §29.1 |
| M3 | Switching semantics conflated multiplexer, actuator, and matrix topologies | Card-class-aware switching required; per-card topology made a sourced capability-model field | §15.2 |
| M4 | Write reconciliation unspecified as to timing | Bounded-poll reconciliation required with explicit timeout, interval, and error content | §22.2 |
| M5 | Simulator behaviour for unmodelled resources unstated | Acknowledging an unperformed write prohibited; must model or reject | §27.2 |
| M6 | Resource locking tested but never specified | Concurrency and locking model specified | §5.2 |
| M7 | Safe shutdown behaviour with no declared ownership ambiguous | Explicit fail-closed semantics with per-action SKIP reporting | §21.2 |
| M8 | Current-measurement channel restriction not stated | Made a sourced capability-model field with pre-transmission validation | §11.3 |
| M9 | Four-wire pairing rule required but not stated | Made a sourced per-card capability-model field affecting channel enumeration | §14.1 |
| M10 | Monitor mode absent entirely | Added as a required vendor-coverage disposition | §12.1, §54 |
| M11 | Error queue drain "bounded" with no bound | Bound specified; truncation reported rather than presented as an emptied queue | §10.2 |
| M12 | Recovery required but no recovery keyword defined | Recovery keyword defined with scan and ownership interaction | §8.2 |
| X1 | Definition of Done still said ten examples | Reconciled to fifteen | §53 |
| X2 | No evidence-completeness verification step | Added | §29.1 |
| X3 | HIL matrix lacked a DMM-present/absent dimension | Added | §30.4 |
| X4 | No configuration example for 34972A USB/VISA | Added | §23 |
| X5 | DAC output range validation not required | Added as a pre-transmission check | §16.4 |

Device-technical items (M3, M8, M9, M10, and open questions 3 and 4) are recorded here as **required
source verifications against the Keysight command reference**, not as asserted device behaviour. The
command reference was not available to the review that produced them, and §1 forbids resolving them
by assumption.

### v1.1 — 2026-08-17

Applies the blocking and resolvable non-blocking findings from `SPEC_REVIEW.md`. No requirement was
removed and the phase/gate structure is unchanged.

| ID | Finding | Resolution | Sections |
|---|---|---|---|
| B1 | `src/` layout contradicted all twelve existing repository drivers, which use a flat package root | Package structure changed to the flat `rf_keysight349xx/rf_keysight349xx/` root | §37 |
| B2 | RFDS-008 absent from the authoritative source set, and no evidence engine in the package structure, although §28 depends on evidence artifacts | RFDS-008 added, with explicit dispositions for RFDS-011/013/016; `evidence.py` added; evidence engine made a Phase 1 Gate 3 deliverable | §2.1, §37, §39 |
| B3 | Measurement capability never gated on the optional internal DMM, contradicting the DMM state already modelled in §25 and §27 | Internal-DMM discovery added to the connection workflow, the effective capability model, and measurement validation | §4.4, §6, §11.1 |
| B4 | `Get Digital Direction` listed as a planned keyword without source verification that a queryable direction register exists | Reclassified `UNKNOWN` pending command-reference verification; the direction-transition requirement made conditional | §16.2, §54 |
| N1 | Exported Robot library class name unspecified | Canonical exported class name defined | §3.1 |
| N2 | Version scheme differed from existing drivers, with no source/distribution split stated | Source and distribution version fields defined explicitly | §3.2 |
| N3 | Statistics return schema omitted the timestamps its own keyword list included | Timestamp fields added to the structured return | §13 |
| N5 | Relay-cycle-counter *read* disposition unstated | Added as an explicit vendor-coverage decision item | §19 |
| N7 | "At least ten examples" versus fifteen listed | Target fixed at fifteen | §31 |
| N8 | Typographical errors | Corrected | §55 |

Deferred to `release/open_questions.yaml` rather than resolved here: **N4** (continuity/diode
disposition — pending command-reference confirmation) and **N6** (which real hardware combinations
are available for HIL).

---

## 1. Purpose

This document defines the implementation plan for a production-grade Robot Framework driver for the Keysight / Agilent 34970A and 34972A data acquisition / switch units.

The driver shall be implemented against the uploaded project RFDS specifications and the supplied Keysight/Agilent 34970A/34972A Command Reference.

The implementation shall not silently invent device capabilities or protocol behavior. Every supported public capability shall be traceable to:

1. a project RFDS requirement;
2. a documented device command or behavior;
3. a public Robot Framework keyword;
4. a protocol vector;
5. verification evidence.

Any device behavior that cannot be established from the available authoritative sources shall be marked `UNKNOWN`, `NOT_APPLICABLE`, `EXCLUDED`, or an approved deviation.

---

## 2. Authoritative Source Set

The following uploaded documents are the implementation baseline.

### 2.1 RFDS project requirements

Versions below are those held in `AI_Guides/`. A citation shall match a document the project
actually holds; a plan may not cite a baseline that cannot be opened.

- RFDS-001 — Platform Requirements v1.1
- RFDS-002 — Mandatory Public API and Robot Framework Keyword Standard v1.0
- RFDS-003 — BaseInstrumentLibrary Common Base Class Design v1.0
- RFDS-004 — Transport Layer Specification v1.0
- RFDS-005 — Driver Package Specification v1.3
- RFDS-006 — Coding Standard v1.0
- RFDS-007 — Error and Exception Standard v1.0
- RFDS-008 — Logging and Evidence Standard v1.0
- RFDS-009 — Testing Standard v1.0
- RFDS-010 — Driver Review Checklist v1.0
- RFDS-011 — Release Process v1.0
- RFDS-012 — GUI Integration Specification v1.0
- RFDS-013 — Capability Model v1.0
- RFDS-014 — Driver Configuration Model Specification v1.0
- RFDS-015 — Plugin Architecture v1.0
- RFDS-017 — AI Driver Contract v3.0
- RFDS-018 — AI Test Bench Contract v1.0
- RFDS-019 — Robot Framework Driver Call and Protocol Conformance Test Specification v1.1
- RFDS-020 — Driver Implementation Lifecycle v1.1

#### 2.1.1 Evidence standard (RFDS-008)

RFDS-008 (Logging and Evidence Standard v1.0) governs the evidence this driver produces. The
requirements below are taken from the standard itself, not inferred from other drivers' behaviour.

**Canonical result directory** (RFDS-008 §11) — runtime results shall not be mixed with
source-controlled package content:

```text
results/<activity>/<driver_or_bench>/<timestamp>_<run_id>/
├── evidence_manifest.json
├── run_summary.json
├── run_summary.md
├── environment.json
├── software_inventory.json
├── driver_inventory.json
├── device_identity.json
├── configuration/
│   ├── effective_configuration.redacted.json
│   └── configuration_fingerprint.json
├── robot/
│   ├── output.xml
│   ├── log.html
│   ├── report.html
│   └── xunit.xml
├── events/
│   ├── events.jsonl
│   ├── operations.jsonl
│   ├── errors.jsonl
│   ├── safety.jsonl
│   └── resource_locks.jsonl
├── protocol/
│   ├── outbound_trace.log
│   ├── inbound_trace.log
│   ├── exchanges.jsonl
│   └── attachments/
├── coverage/
│   ├── keyword_coverage.csv
│   └── requirement_coverage.csv
├── attachments/
├── cleanup/
│   ├── cleanup_summary.json
│   └── final_state.json
└── integrity/
    ├── checksums.sha256
    └── provenance.json
```

Only applicable files are mandatory, but per RFDS-008 §11 `run_summary.json` and
`evidence_manifest.json` **shall state why expected files are absent** — silence is not an
acceptable representation of a missing artifact.

`events/safety.jsonl` and `events/resource_locks.jsonl` are directly applicable to this driver:
§21 safety actions and the §5.2 locking model both produce records that belong in them.

**Core principles applied to this driver** (RFDS-008 §6):

- **§6.1 no silent success** — an operation that did not demonstrably succeed shall not be recorded
  as successful; `final_status` shall be derived from recorded outcomes, never fixed;
- **§6.2 no silent evidence loss** — dropped or truncated evidence shall be recorded as such;
- **§6.3 raw evidence preservation** — parsed values never replace the raw protocol trace;
- **§6.6 simulation honesty** — simulator evidence shall be distinguishable and shall never be
  presented as proof of physical accuracy, wiring, electrical behaviour, or hardware safety;
- **§6.7 finite finalization** — evidence writers shall use finite timeouts and shall not block
  shutdown; every run created shall nonetheless be finalized;
- **§6.8 append-only** — finalized records shall not be rewritten without a new revision;
- **§11.1 atomic result-root allocation** — the result directory shall not overwrite a previous
  run; on collision the driver shall allocate a different run ID or fail visibly.

**Run identity** (RFDS-008 §9, §10): run ID, required identifiers, sub-second wall-clock
timestamps, monotonic time, clock status, and per-stream sequence numbers.

Trace capture shall attach before the connection is opened (§28).

#### 2.1.2 Standards not in the baseline

The following RFDS documents are deliberately not part of this driver's source set. Each shall be
confirmed at Phase 1 Gate 1 and recorded in `release/requirements_traceability.csv` with the stated
disposition rather than left unmentioned:

```yaml
RFDS-011: IN_SCOPE        # Release Process v1.0 -- added to §2.1; governs §3.2, §35, §50-§53
RFDS-013: IN_SCOPE        # Capability Model v1.0 -- added to §2.1; see §7.2 and §37
RFDS-016: NOT_APPLICABLE  # no such document exists in AI_Guides/; the set runs 001-015, 017-020
```

Every RFDS document held in `AI_Guides/` is now either in the source set above or carries a
disposition here. No RFDS document is silently omitted from traceability.

### 2.3 Recorded inter-guide conflict

RFDS-001-GOV-004 requires a detected conflict between specifications to be recorded and resolved
through a correction, interpretation note, architecture decision, or time-limited deviation.
"Silent interpretation is prohibited." One such conflict applies to this driver.

```yaml
conflict: RFDS-004 §6 vs RFDS-005 §6.1
  RFDS-004 §6:  transport package tree rooted at src/rf_<driver_name>/
  RFDS-005 §6.1: "A new RFDS driver shall not use a src/ layout.
                  RFDS-005 is the sole normative source for this rule."
  resolution: INTERPRETATION_NOTE
  basis: >
    RFDS-001 §7.2 assigns package and repository structure to RFDS-005 and
    transport abstraction to RFDS-004. RFDS-005 therefore governs whether a
    src/ layout is used; RFDS-004 governs the module layout within the
    package. This driver uses the flat RFDS-005 root with the RFDS-004
    transport/ module tree inside it.
  recorded_in: api/deviations.yaml
```

### 2.4 Error model (RFDS-007)

The driver shall implement or import the **complete RFDS-007 §6 canonical exception hierarchy**
rooted at `DriverError` — not merely the few types this plan names in passing. Device-specific
subclasses may be added; canonical classes shall not be renamed, omitted, or re-parented.

Of particular relevance here:

- `DriverOperationUncertainError` (under `DriverStateError`) is the canonical type for the
  uncertain-delivery case §22.2 addresses, and shall be used for it;
- `DriverUnsupportedOperationError` (under `DriverDeviceError`) is the type for model gating (§18),
  the internal-DMM gate (§4.4), and unconfigured auxiliary capabilities;
- `DriverTimeoutError` (under `DriverTransportError`) is the type for §22 deadline expiry.

**Error codes** shall follow RFDS-007 §8.1 — `RFDS-<DOMAIN>-<NNN>`, three-character uppercase
domain, zero-padded 001–999 — drawn from the RFDS-007 §9 canonical catalogue. Codes shall not be
invented per driver where a canonical code exists.

Exception payload fields, the public failure message format, and Robot Framework failure behaviour
shall follow RFDS-007 §10, §11, and §12 respectively. §28.1's error vectors shall assert the code
and payload, not only the exception type.

### 2.5 GUI integration (RFDS-012)

RFDS-012 is in the source set and shall be addressed rather than deferred.

```yaml
target_gui_compatibility_level: GUI-L1
```

**GUI-L0** (RFDS-012 §8.1) requires import without hardware activity, a loading and validating
RFDS-017 contract, an inventoriable public API, displayable identity and version, and deterministic
reporting of unknown metadata. **GUI-L1** (§8.2) adds presentable connection profiles; connect,
verify, identify, diagnose and disconnect through the public API; and state and errors mapped to
generic GUI status.

The RFDS-012 §9 eligibility criteria — stable identity, valid contract, current contract lock,
deterministic keyword inventory, no hardware activity during import or metadata discovery, explicit
connection profiles, finite timeouts, documented errors and recovery, safe-state information, and
structured return values — are already required elsewhere in this plan and shall be cross-checked
against §9 at Gate 5 rather than re-derived.

Capability projection (§10) and required information surfaces (§12) shall be satisfied through the
RFDS-013 capability model (§7.2), not through a separate GUI-specific description.

### 2.2 Device source

- Keysight / Agilent 34970A / 34972A Command Reference

This command reference is the authoritative source for device SCPI command syntax, supported models,
channel behavior, module behavior, status, errors, trigger functions, measurements, and
remote-control protocol behavior.

It is held in the repository at:

```text
reference/Keysight_34970A_34972A_Command_Reference.md    # Keysight version 2.00, 2009-2014
reference/SOURCE_VERIFICATION.md                          # per-item verification record
```

Every device-behaviour claim in this plan shall cite it. `SOURCE_VERIFICATION.md` records each
resolved item with line citations, and is the evidence that §1's no-invention rule was honoured.

### 2.3 Project repository

Project repository:

`https://github.com/ami3go/RobotFrameworks_hw_drivers`

---

## 3. Driver Identity

The driver shall be implemented as a family driver.

### 3.1 Canonical identity

```text
Project/root:       rf_keysight349xx/
Python import:      rf_keysight349xx
Distribution:       rf-keysight349xx
Plugin ID:          keysight.349xx
Robot library:      rf_keysight349xx.Keysight349xxLibrary
Library module:     rf_keysight349xx.library
Library class:      Keysight349xxLibrary
```

The package root shall export the library class directly, matching the
`rf_<device>.<Device>Library` convention already used by the other drivers in the project
repository, so Robot suites import it as:

```robotframework
Library    rf_keysight349xx.Keysight349xxLibrary
```

If an additional shorter class name is retained for internal use, the exported
`Keysight349xxLibrary` name shall remain the canonical public identity and shall be stable across
revisions.

### 3.2 Package naming

Naming follows RFDS-011 §6.1 and §6.2. The `-gN` suffix used in earlier revisions of this plan was
invented and is non-conformant: RFDS-011 encodes the gate in the third version field.

Public release ZIP (RFDS-011 §6.1, `vYY.RR` zero-padded per §5.2):

```text
rf_keysight349xx_v26.01.zip
```

Engineering gate ZIPs (RFDS-011 §6.2, `vYY.PP.GG` = year, phase, gate per §5.3):

```text
rf_keysight349xx_v26.01.01.zip    Phase 1, Gate 1
rf_keysight349xx_v26.01.02.zip    Phase 1, Gate 2
rf_keysight349xx_v26.01.03.zip    Phase 1, Gate 3
rf_keysight349xx_v26.01.04.zip    Phase 1, Gate 4
rf_keysight349xx_v26.01.05.zip    Phase 1, Gate 5
```

Release candidates use `vYY.RR-rc.N` (RFDS-011 §5.4). An engineering gate version shall not consume
a public `RR` sequence (§5.3), and after publication a public version identifies one immutable
artifact set — a rebuild under the same version is permitted only if byte-identical (§5.6).

The ZIP shall contain exactly one stable package root:

```text
rf_keysight349xx/
```

### 3.3 Version fields

Two distinct version values exist and shall be defined explicitly, because a mismatch between them
is a known failure mode elsewhere in the project repository (a hardware suite there asserts source
version equality and aborts at suite setup when the vendored copy has drifted):

Per RFDS-011 §5.5 the Python package version is a normalized representation of the same release
identity:

```text
RFDS public identity  (archives, history, reviews, release notes):  v26.01
Source release version (RELEASE_VERSION in version.py):             "26.01"
Distribution version   (project.version in pyproject):              "26.1"
```

For an engineering gate package the mapping is `v26.01.03` → `26.1.3`.

Zero padding remains mandatory in archive names, history files, review filenames, and release notes
even where the packaging tool normalizes it (RFDS-011 §5.5). The mapping shall be deterministic and
validated by `scripts/build_release.py`.

Requirements:

- both values shall be derived from a single source of truth so they cannot drift independently;
- the driver shall expose the source release version through `Get Driver Information`;
- any suite asserting an expected version shall state which of the two it means;
- the three-part scheme used here differs from the two-part scheme used by earlier drivers in the
  repository, so release tooling and any cross-driver version comparison shall be confirmed to
  accept it at Phase 1 Gate 1.

---

## 4. Supported Instrument Family

### 4.1 Mainframes

Planned support:

- Keysight / Agilent 34970A
- Keysight 34972A

### 4.2 Model-specific behavior

The driver shall not assume both models support the same interfaces or commands.

Expected distinction:

```text
34970A
├── GPIB
└── RS-232

34972A
├── LAN
├── USB / VISA
└── 34972A-specific LAN and memory functionality
```

The driver shall determine the connected model using `*IDN?`.

### 4.3 Module discovery

During connection the driver shall discover installed modules in slots:

```text
100
200
300
```

Module discovery shall be used to construct the effective runtime capability model.

Supported card families are expected to include:

- 34901A
- 34902A
- 34903A
- 34904A
- 34905A
- 34906A
- 34907A
- 34908A

Support for each card shall be marked separately as:

- implemented;
- simulator tested;
- hardware tested;
- excluded;
- unknown.

### 4.4 Internal DMM

The internal DMM is an **option** on these mainframes. A frame without it — or with it disabled —
remains a fully functional switch and routing unit but cannot measure.

The driver shall therefore treat DMM availability as a first-class capability gate, on equal footing
with the model gating in §18:

- DMM presence and enabled state shall be discovered during connection (§6) using
  `INSTrument:DMM?`. The Command Reference qualifies measurement commands with "(see
  `INSTrument:DMM` command) or not installed in the mainframe", confirming both that the DMM is
  optional and that it can be disabled in software — the installed-versus-enabled distinction below;
- the result shall form part of the effective runtime capability model;
- every measurement, scan, statistics, and temperature capability shall be gated on it (§11.1);
- calling a DMM-dependent keyword on a frame without an available DMM shall raise a normalized
  `DriverUnsupportedOperationError` **before** transmission, not produce a device error;
- switching, routing, and 34907A digital I/O, totalizer, and DAC capabilities shall remain available
  when the DMM is absent, since they do not depend on it.

The distinction between "not installed" and "installed but disabled" shall be preserved in the
capability model and in diagnostics, because only the second is recoverable by configuration.

The simulator (§27) already models internal DMM state and shall be able to present both a
DMM-equipped and a switch-only frame.

---

## 5. Top-Level Architecture

```text
Robot Framework
      │
      ▼
library.py
RFDS canonical public API
      │
      ▼
BaseInstrumentLibrary
RFDS lifecycle / sessions / timeout /
locking / evidence / errors
      │
      ▼
core/
device semantics
      │
      ▼
protocol/
SCPI generation + response parsing
      │
      ▼
RFDS transport interface
      │
      ├── VISA
      ├── Serial
      ├── TCP/LAN
      └── Simulator / protocol spy
             │
             ▼
       34970A / 34972A
```

### 5.1 Architectural requirements

The implementation shall:

- derive from the approved `BaseInstrumentLibrary`;
- perform zero hardware I/O during module import;
- perform zero hardware I/O during library construction;
- disable uncontrolled automatic Robot Framework keyword exposure;
- expose only intentional public keywords;
- use the RFDS transport abstraction;
- keep protocol serialization separate from transport;
- keep device semantics separate from Robot Framework adapters;
- guarantee finite blocking behavior;
- clean up partial connection attempts;
- produce observable protocol evidence;
- avoid unsafe implicit retries.

### 5.3 `rfds-core` base package (RFDS-003 §8)

The approved `BaseInstrumentLibrary` is delivered as the separately versioned distribution
**`rfds-core`** (RFDS-003 §8.1), imported as:

```python
from rfds_core import BaseInstrumentLibrary
```

Requirements:

- the driver **shall declare a compatible `rfds-core` version range** in its installation metadata
  (RFDS-003 §8.2):

  ```toml
  dependencies = [
    "rfds-core>=1.0,<2.0",
  ]
  ```

- the driver **shall not maintain a modified private copy** of the base-class source under the same
  identity (RFDS-003 §8.3). An offline release package may bundle an approved `rfds-core` wheel only
  where it matches the declared dependency and its checksum;
- the effective `rfds-core` version **shall be recorded** in `Get Driver Information`, in the
  diagnostic bundle, and in the evidence run's `software_inventory.json` (RFDS-003 §8.4, RFDS-008
  §11).

This is a Phase 1 Gate 2 deliverable, not a late integration step.

### 5.4 Python language baseline (RFDS-006 §5)

```toml
requires-python = ">=3.10"
```

Per RFDS-006 §5.1 the driver shall declare its supported versions in `pyproject.toml`, shall be
tested on the lowest declared version and on the highest version the release claims, and shall not
rely on an undeclared interpreter version or implementation-specific behaviour.

Source rules (RFDS-006 §5.2, §5.3): UTF-8 encoding; LF line endings except where a platform script
requires otherwise; exactly one trailing newline; no tabs for Python indentation; `from __future__
import annotations` where forward references benefit.

### 5.5 Resource declaration and access mode (RFDS-001-RES)

**RFDS-001-RES-001** requires each driver *and* bench contract to identify resources requiring
controlled access. Delegating entirely to the §26 bench contract does not discharge it — the
requirement names both.

| Resource | Scope | Access mode | Notes |
|---|---|---|---|
| Communication session | per alias | exclusive | one transport per alias (§5.2) |
| Mainframe | whole instrument | exclusive while held | device lock via `SYSTem:LOCK:REQuest?` |
| GPIB address / LAN socket / USB / serial port | per transport | exclusive | declared in §23 configuration |
| Internal DMM | whole instrument | exclusive | contended by scan **and** monitor mode (§4.4, §12.1) |
| Scan engine | whole instrument | exclusive | one scan at a time |
| Reading memory | whole instrument | exclusive | consumed destructively by `R?` / `DATA:REMove?` (§22.3) |
| Routing channels | per channel | exclusive, ownership-declared | owned set per §21 |
| Digital I/O ports | per port | exclusive, ownership-declared | 34907A |
| DAC channels | per channel | exclusive, ownership-declared | 34907A channels 04/05 |
| Totalizer | per module | exclusive | destructive read mode (§16.3) |
| Configuration profile files | per path | shared read / exclusive write | §23 |
| Evidence result directory | per run | exclusive | atomic allocation, RFDS-008 §11.1 |

**RFDS-001-RES-003 — default concurrency posture.** Concurrency is **disabled by default**.
Concurrent access shall not be enabled for any resource above until it is proven safe for that
resource on this instrument family. OQ-14 (concurrent scans from different sessions) is therefore
**refused by default** until decided, not permitted-pending-decision.

### 5.2 Concurrency and resource locking

§8 requires multi-connection support and §29.1 requires resource-locking tests, so the locking model
shall be specified rather than implied.

A mainframe is a genuinely shared resource: two sessions can address the same slot, the same relay,
or the same scan engine. The hazard is concrete — `FETCh?`, `R?`, and `DATA:REMove?` consume shared
reading memory, so a scan initiated by one session can have its readings consumed by another.

**The instrument provides a locking mechanism**; the driver shall use it rather than implement a
purely driver-side scheme:

```text
SYSTem:LOCK:REQuest?     request the lock (returns grant/deny)
SYSTem:LOCK:RELease      release the lock
SYSTem:LOCK:OWNer?       query the current owner
SYSTem:LOCK:NAME?        query the lock name
```

Device-level locking covers cross-process and cross-application contention, which a driver-side lock
cannot see. Driver-side locking remains necessary for intra-process session coordination, so the two
compose: the device lock guards the mainframe, the driver lock guards this process's sessions.

`SYSTEM:RWLock` (remote/local lockout) is a separate, `INTERNAL` concern and shall not be exposed as
a locking keyword.

The specification shall define:

- **lock granularity** — session, mainframe, scan engine, and per-slot resources, and which of these
  the device lock covers versus the driver lock;
- **acquisition semantics** — blocking with a finite timeout, or immediate failure;
- **contention behaviour** — what a second session receives when a resource is held;
- **scan exclusivity** — whether concurrent scan operations from different sessions are permitted or
  refused, and which session owns reading memory for the duration;
- **release on failure** — locks shall not survive a failed operation or a dropped transport.

Locking shall never be silently advisory. If a resource cannot be locked, the operation shall fail
explicitly rather than proceed unsynchronised.

---

## 6. Connection Workflow

Connection sequence:

```text
Open selected transport
      ↓
Query *IDN?
      ↓
Parse manufacturer / model / serial / firmware
      ↓
Validate supported mainframe
      ↓
Discover installed modules
      ↓
Discover internal DMM presence / enabled state
      ↓
Discover relevant runtime state
      ↓
Build effective capability model
  (model + modules + DMM availability)
      ↓
Cache identity, module inventory, DMM availability
      ↓
Connection state = CONNECTED
```

Internal-DMM discovery is a mandatory connection step, not an optional probe: the effective
capability model cannot be constructed without it, because measurement, scan, statistics, and
temperature capabilities all depend on it (§4.4, §11.1).

If DMM availability cannot be established, it shall be recorded as `UNKNOWN` and the dependent
capabilities shall fail closed with `DriverUnsupportedOperationError` rather than being optimistically
assumed present.

A failed connection attempt shall:

- close opened resources;
- clear partially initialized state;
- retain useful diagnostics;
- return a normalized RFDS exception.

---

## 7. Mandatory RFDS Universal API

The driver shall implement all mandatory universal keywords:

```text
Connect
Disconnect
Is Connected
Get Connection State
Check Communication
Get Identity
Get Driver Information
Get Driver Capabilities
Set Communication Timeout
Get Communication Timeout
```

### 7.1 Semantic rules

- `Get Identity` shall normally use cached identity.
- Live refresh shall require an explicit operation.
- `Is Connected` shall not perform surprise hardware I/O.
- `Check Communication` shall perform an actual communication probe.
- Communication timeout shall always be finite.
- Return values shall be Robot Framework-compatible.
- Keyword names shall remain stable across revisions.

### 7.2 Mandatory RFDS-013 capability discovery keywords

RFDS-013 §7.1 mandates six public discovery keywords in addition to RFDS-002's
`Get Driver Capabilities`:

```text
Get Capability Model
Get Driver Capability
Find Driver Capabilities
Get Driver Features
Refresh Driver Capabilities
Validate Driver Capabilities
```

RFDS-013 §7.1 is explicit that `Get Capability Model` and `Get Driver Capabilities` are
**deliberately distinct** and that a driver shall implement **both**:

| Keyword | Returns |
|---|---|
| `Get Driver Capabilities` (RFDS-002 §8.8) | the fixed, flat `list[str]` of RFDS-002 group-level capability names |
| `Get Capability Model` (RFDS-013 §7.1) | the richer RFDS-013 structure, or a filtered capability list |
| `Get Driver Capability` | one capability by exact capability ID |
| `Find Driver Capabilities` | capabilities matching structured filters |
| `Get Driver Features` | normalized device and driver feature data |
| `Refresh Driver Capabilities` | re-evaluated configured and live capability information |
| `Validate Driver Capabilities` | a structured validation result for the model and its bindings |

The AI Driver Contract shall map each RFDS-002 group name to its corresponding RFDS-013
`capability_id` entries.

This is the conformant home for the runtime capability state this plan already depends on: the
internal-DMM gate (§4.4), the installed module inventory (§4.3), model gating (§18), and the
per-card topology, current-channel, and pairing data recorded in §11.3, §14.1, and §15.2.
`Refresh Driver Capabilities` is what re-evaluates them after a reconnect.

---

## 8. Conditional RFDS API Groups

Where the corresponding capability is implemented, the complete applicable keyword group shall also be implemented.

Expected groups include:

- multi-connection;
- device error queue;
- channel discovery and validation;
- measurement;
- switching / relay control;
- reset / preset;
- safe shutdown;
- raw protocol I/O;
- configuration;
- diagnostics.

Partial implementation of a declared RFDS capability group shall not be accepted without an approved deviation.

### 8.1 Raw protocol I/O

Raw protocol I/O is the universal bypass: with it, every exclusion in §19 and every safety rule in
§21 becomes advisory, because the caller can transmit the underlying command directly. It shall
therefore be specified rather than merely listed.

Keywords:

RFDS-002 §9.11 fixes the permitted canonical names; earlier revisions of this plan invented
`Raw SCPI Write` / `Raw SCPI Query`, which are non-conformant:

```text
Write Raw Command(command, alias=None) -> None
Query Raw Command(command, alias=None, timeout_s=None) -> str | bytes
Read Raw Response(alias=None, timeout_s=None) -> str | bytes
```

Opt-in gate keywords (RFDS-002 §9.11 requires raw I/O be "disabled by default or require explicit
opt-in when it can bypass driver safety validation"; the gate keywords themselves are additional to
the canonical operation names, not substitutes for them):

```text
Enable Raw IO
Disable Raw IO
```

Requirements:

- raw I/O shall be **disabled by default** and shall remain disabled until `Enable Raw IO` is
  called with an explicit confirmation argument;
- all raw keywords shall carry the RFDS-002 §9.11 mandated tags `rfds:raw_io` and
  `rfds:high_risk`;
- secrets shall be redacted in raw traffic (RFDS-002 §9.11);
- raw I/O shall not be presented as the primary public API and shall not replace domain-level
  keywords (RFDS-002 §9.11);
- the AI Driver Contract shall warn that raw I/O may invalidate state tracking (RFDS-002 §9.11);
- enabling raw I/O shall be recorded as a state transition in the AI contract and in evidence;
- every raw exchange shall appear in protocol evidence exactly as any other exchange (§2.1.1);
- raw I/O shall **not** exempt the caller from §19 exclusions or §21 ownership rules, and that
  limitation shall be stated explicitly in the AI contract entry for each raw keyword;
- the driver shall not parse, interpret, or cache device state inferred from raw traffic — state
  learned through raw I/O is `UNKNOWN` to the capability model;
- raw I/O shall not be used internally by any other keyword.

The driver shall document that raw I/O can place the instrument in a state the capability model does
not describe, and that recovery from such a state is the caller's responsibility.

### 8.2 Session recovery

§28.1 requires a recovery vector for every keyword and §29.1 requires recovery tests, so the
recovery capability shall be defined explicitly:

```text
Recover Connection
```

Requirements:

- the keyword shall re-establish the transport and restore the session to a known state;
- it shall state whether session configuration is preserved or reset, and that behaviour shall be
  deterministic rather than transport-dependent;
- it shall abort any scan the session had initiated, because reading memory ownership cannot be
  reasoned about across a transport break;
- it shall **not** silently re-apply owned safe states or re-close previously closed relays;
  post-recovery routing state shall be re-queried, never assumed;
- if the pre-recovery ownership set cannot be re-established, recovery shall fail explicitly rather
  than continue with an unverified ownership model.

---

## 9. System and Identity Functions

Planned functions:

```text
Get Instrument Information
Get Installed Modules
Get Module Information
Get SCPI Version
Run Self Test
Reset Device
Preset Device
Clear Status
Get Line Frequency
```

The exact exported Robot keyword names shall be finalized in the public API contract before implementation.

### 9.1 Reset and preset are ownership-violating operations

`Reset Device` and `Preset Device` are **not** ordinary system keywords on this instrument family.
On these mainframes a device reset opens all channel relays and returns the instrument to its
default state, which is precisely what §21 forbids the driver from doing blindly, and it does so in
a single call that bypasses the entire ownership model on a frame that may carry another team's
wiring.

Disposition:

RFDS-002 §9.8 fixes the canonical signature, which has no confirmation parameter:

```text
Reset Device(alias=None, wait_until_ready=True, timeout_s=None) -> dict
```

Earlier revisions of this plan added a confirmation argument. That diverges from a canonical
signature without an approved deviation and is withdrawn. RFDS-002 §9.8's own remedy for the hazard
is documentation, which this plan now discharges explicitly:

```yaml
Reset Device:
  status: PUBLIC
  risk: HIGH
  signature: RFDS-002 §9.8 canonical -- unmodified
  reset_type: device reset to Factory Reset State
  output_behavior: |
    Per the Command Reference "Module Factory Reset State" table:
      34901A / 34902A / 34908A : All Channels Open
      34903A / 34904A          : All Channels Open
      34905A / 34906A          : Channels s11 and s21 Selected
      34907A                   : Both DIO Ports = Input,
                                 Totalizer Count = 0,
                                 Both DACs = 0 VDC
  settings: cleared to defaults
  reconnect_behavior: session preserved; routing and DAC state invalidated
  ready_time: to be measured during Phase 2 HIL
  safety_risk: >
    Opens every relay AND zeroes both DACs AND clears the totalizer. Violates
    §21's "never blindly open or close every relay" and "never blindly zero
    every DAC" simultaneously. Not safe on a shared frame carrying another
    team's wiring.
  ownership_gate: >
    Permitted only where the §26 bench contract declares whole-frame ownership.

Preset Device:
  status: PUBLIC
  risk: HIGH
  command: "SYSTem:PRESet"
  side_effect: |
    The Command Reference "Module Instrument Preset State" table is IDENTICAL
    to the Factory Reset table above for module hardware: all relays open,
    both DACs 0 VDC, totalizer cleared, DIO ports = Input.
    Preset is NOT a lighter-weight alternative to Reset at the hardware level.
  ownership_gate: same as Reset Device

Clear Status:
  status: PUBLIC
  risk: NONE
  side_effect: status registers only; no routing impact
```

Requirements:

- the RFDS-002 §9.8 canonical signature shall be used unmodified;
- every RFDS-002 §9.8 documentation duty above (reset type, output behavior, settings, reconnect
  behavior, ready time, safety risk) shall appear in the public documentation, not only here;
- the reset keywords shall be gated on the §26 bench contract declaring whole-frame ownership; where
  it does not, the driver shall refuse with `DriverUnsupportedOperationError` rather than reset;
- if a confirmation argument is later judged necessary despite RFDS-002, it shall be recorded as an
  approved deviation in `api/deviations.yaml`, never introduced silently;
- the AI contract entry (§25) shall record the state transition as affecting **all** routing
  resources, not only owned ones;
- the documented side effect shall be verified against the command reference before implementation;
  if the reset behaviour differs from the above, the disposition shall be corrected, not the
  documentation quietly relaxed;
- where the bench contract (§26) declares whole-frame ownership, the confirmation gate may be
  satisfied by that declaration rather than per-call.

`Clear Status` is the safe member of this group and shall be documented as such.

### 9.2 Complete keyword inventory (authoritative)

**`api/public_api.yaml` is the sole authoritative keyword inventory.** It is the **union** of two
disjoint sources, and neither source alone is the inventory:

```yaml
device_facing:   protocol/vendor_command_coverage.yaml     # ~121 keywords, each SCPI-bound
driver_level:    RFDS-002 §8/§9, RFDS-013 §7.1, RFDS-014   #  ~34 keywords, no SCPI at all
public_api.yaml: device_facing ∪ driver_level               # ~155 keywords -- authoritative
```

**Why the union is necessary.** Driver-level keywords emit no SCPI: `Connect` opens a transport,
`Import Driver Configuration` manipulates a JSON document, `Get Capability Model` reads a YAML file.
A command-derived table can only ever contain device-facing keywords. v1.6 and v1.7 declared that
table authoritative for the whole public API, which excluded 33 of the 34 mandatory RFDS keywords —
`Get Identity` survived only because it maps to `*IDN?`. As written, those revisions said a
conformant driver needs no `Connect`.

**Scope of the coverage map's authority (D2).** `vendor_command_coverage.yaml` is authoritative
**only over the command↔keyword binding** — which vendor command backs a device-facing keyword, and
what disposition each command carries. It is *not* authoritative about whether a keyword should
exist, what it returns, or whether it is mandatory. Those are owned by RFDS-002, RFDS-013, and
RFDS-014 under RFDS-001 §7.2, and RFDS-001 §7.1 places those specifications above this task
document. A generated artifact shall not take precedence over a normative specification.

**General rule.** *An inventory assembled from one source is authoritative only over that source's
domain.* This is the recurring defect of revisions v1.5–v1.7, recorded here so it is not repeated.

Exact signatures, argument names, units, and return schemas are **not** fixed here; they are the
Phase 1 Gate 1 public API contract deliverable (§39). This section fixes the *set* and its device
binding, nothing more.

#### Driver-level keywords (no vendor command)

Mandatory, and absent from the device-facing table by construction:

| Source | Keywords |
|---|---|
| RFDS-002 §8 | `Connect`, `Disconnect`, `Is Connected`, `Get Connection State`, `Check Communication`, `Get Identity`*, `Get Driver Information`, `Get Driver Capabilities`, `Set Communication Timeout`, `Get Communication Timeout` |
| RFDS-013 §7.1 | `Get Capability Model`, `Get Driver Capability`, `Find Driver Capabilities`, `Get Driver Features`, `Refresh Driver Capabilities`, `Validate Driver Capabilities` |
| RFDS-014 | `Get Driver Configuration Schema`, `Get Driver Default Configuration`, `Get Driver Configuration`, `Validate Driver Configuration`, `Import Driver Configuration`, `Export Driver Configuration`, `Save Driver Configuration`, `Load Driver Configuration`, `List Driver Configuration Profiles`, `Delete Driver Configuration Profile`, `Reset Driver Configuration` |
| RFDS-002 §9.10 / §9.11, §8.1, §8.2 | `Safe Shutdown`, `Recover Connection`, `Enable Raw IO`, `Disable Raw IO`, `Write Raw Command`, `Query Raw Command`, `Read Raw Response` |

\* `Get Identity` is device-facing (`*IDN?`) and also appears in the table below; it is the one
overlap between the two sources.

Multi-connection keywords (RFDS-002 §9.1) are additionally required and are driver-level.

#### Device-facing keywords (SCPI-bound)


**§4.3 — Module discovery**

| Keyword | Vendor command(s) |
|---|---|
| `Get Module Information` | `SYSTem:CTYPe?` |

**§4.4 — Internal DMM capability gate**

| Keyword | Vendor command(s) |
|---|---|
| `Get Internal DMM State` | `INSTrument:DMM:INSTalled?` |
| `Set Internal DMM State` | `INSTrument:DMM`, `INSTrument:DMM?` |

**§5.2 — Concurrency and resource locking**

| Keyword | Vendor command(s) |
|---|---|
| `Acquire Instrument Lock` | `SYSTem:LOCK:REQuest?` |
| `Get Instrument Lock Name` | `SYSTem:LOCK:NAME?` |
| `Get Instrument Lock Owner` | `SYSTem:LOCK:OWNer?` |
| `Release Instrument Lock` | `SYSTem:LOCK:RELease` |

**§7 — Mandatory universal API**

| Keyword | Vendor command(s) |
|---|---|
| `Get Identity` | `*IDN?` |

**§9 — System and identity**

| Keyword | Vendor command(s) |
|---|---|
| `Clear Display Text` | `DISPlay:TEXT:CLEar` |
| `Get Line Frequency` | `SYSTem:LFRequency?` |
| `Get SCPI Version` | `SYSTem:VERSion?` |
| `Run Self Test` | `*TST?` |
| `Set Display State` | `DISPlay`, `DISPlay?` |
| `Set Display Text` | `DISPlay:TEXT`, `DISPlay:TEXT?` |
| `Set Instrument Date` | `SYSTem:DATE`, `SYSTem:DATE?` |
| `Set Instrument Time` | `SYSTem:TIME`, `SYSTem:TIME?` |

**§9.1 — Reset and preset (high risk)**

| Keyword | Vendor command(s) |
|---|---|
| `Clear Status` | `*CLS` |
| `Preset Device` | `SYSTem:PRESet` |
| `Preset Module` | `SYSTem:CPON` |
| `Reset Device` | `*RST` |

**§10 — Device error queue**

| Keyword | Vendor command(s) |
|---|---|
| `Get Device Error` | `SYSTem:ERRor?` |

**§11 — Measurement**

| Keyword | Vendor command(s) |
|---|---|
| `Configure AC Voltage` | `CONFigure:VOLTage:AC`, `[SENSe:]VOLTage:AC:BANDwidth`, `[SENSe:]VOLTage:AC:BANDwidth?`, `[SENSe:]VOLTage:AC:RANGe` … (+3) |
| `Configure DC Voltage` | `CONFigure:VOLTage:DC`, `INPut:IMPedance:AUTO`, `INPut:IMPedance:AUTO?`, `[SENSe:]VOLTage:DC:APERture` … (+9) |
| `Configure Frequency` | `CONFigure:FREQuency`, `[SENSe:]FREQuency:APERture`, `[SENSe:]FREQuency:APERture?`, `[SENSe:]FREQuency:RANGe:LOWer` … (+5) |
| `Configure Period` | `CONFigure:PERiod`, `[SENSe:]PERiod:APERture`, `[SENSe:]PERiod:APERture?`, `[SENSe:]PERiod:VOLTage:RANGe` … (+3) |
| `Configure Resistance` | `CONFigure:RESistance`, `[SENSe:]RESistance:APERture`, `[SENSe:]RESistance:APERture?`, `[SENSe:]RESistance:NPLC` … (+9) |
| `Get Channel Configuration` | `CONFigure?` |
| `Get Channel Function` | `[SENSe:]FUNCtion`, `[SENSe:]FUNCtion?` |
| `Measure AC Voltage` | `MEASure:VOLTage:AC?` |
| `Measure DC Voltage` | `MEASure:VOLTage:DC?` |
| `Measure Frequency` | `MEASure:FREQuency?` |
| `Measure Period` | `MEASure:PERiod?` |
| `Measure Resistance` | `MEASure:RESistance?` |
| `Set Autozero` | `[SENSe:]ZERO:AUTO`, `[SENSe:]ZERO:AUTO?` |
| `Set Channel Function` | `[SENSe:]FUNCtion`, `[SENSe:]FUNCtion?` |

**§11.3 — Current measurement (34901A ch 21-22)**

| Keyword | Vendor command(s) |
|---|---|
| `Configure AC Current` | `CONFigure:CURRent:AC`, `[SENSe:]CURRent:AC:BANDwidth`, `[SENSe:]CURRent:AC:BANDwidth?`, `[SENSe:]CURRent:AC:RANGe` … (+5) |
| `Configure DC Current` | `CONFigure:CURRent:DC`, `[SENSe:]CURRent:DC:APERture`, `[SENSe:]CURRent:DC:APERture?`, `[SENSe:]CURRent:DC:NPLC` … (+7) |
| `Measure AC Current` | `MEASure:CURRent:AC?` |
| `Measure DC Current` | `MEASure:CURRent:DC?` |

**§12 — Scan, trigger and acquisition**

| Keyword | Vendor command(s) |
|---|---|
| `Abort Scan` | `ABORt` |
| `Clear Reading Memory` | `DATA:REMove?` |
| `Configure Scan List` | `ROUTe:SCAN`, `ROUTe:SCAN?` |
| `Configure Trigger Source` | `ROUTe:CHANnel:ADVance:SOURce`, `ROUTe:CHANnel:ADVance:SOURce?`, `TRIGger:SOURce`, `TRIGger:SOURce?` |
| `Fetch Readings` | `FETCh?` |
| `Get Last Reading` | `DATA:LAST?` |
| `Get Reading Count` | `DATA:POINts?` |
| `Get Scan List` | `ROUTe:SCAN`, `ROUTe:SCAN?` |
| `Get Scan List Size` | `ROUTe:SCAN:SIZE?` |
| `Get Scan Start Time` | `SYSTem:TIME:SCAN?` |
| `Get Trigger Count` | `TRIGger:COUNt`, `TRIGger:COUNt?` |
| `Get Trigger Source` | `TRIGger:SOURce`, `TRIGger:SOURce?` |
| `Get Trigger Timer` | `TRIGger:TIMer`, `TRIGger:TIMer?` |
| `Initiate Scan` | `INITiate` |
| `Set Channel Delay` | `ROUTe:CHANnel:DELay`, `ROUTe:CHANnel:DELay:AUTO`, `ROUTe:CHANnel:DELay:AUTO?`, `ROUTe:CHANnel:DELay?` |
| `Set Reading Count Threshold` | `DATA:POINts:EVENt:THReshold`, `DATA:POINts:EVENt:THReshold?` |
| `Set Reading Format` | `FORMat:READing:ALARm`, `FORMat:READing:ALARm?`, `FORMat:READing:CHANnel`, `FORMat:READing:CHANnel?` … (+6) |
| `Set Trigger Count` | `TRIGger:COUNt`, `TRIGger:COUNt?` |
| `Set Trigger Timer` | `TRIGger:TIMer`, `TRIGger:TIMer?` |
| `Trigger Scan` | `*TRG` |

**§12.1 — Monitor mode**

| Keyword | Vendor command(s) |
|---|---|
| `Configure Channel Monitor` | `ROUTe:MONitor`, `ROUTe:MONitor?` |
| `Read Monitor Data` | `ROUTe:MONitor:DATA?` |
| `Set Monitor State` | `ROUTe:MONitor:STATe`, `ROUTe:MONitor:STATe?` |

**§13 — Statistics**

| Keyword | Vendor command(s) |
|---|---|
| `Clear Channel Statistics` | `CALCulate:AVERage:CLEar` |
| `Get Channel Average` | `CALCulate:AVERage:AVERage?` |
| `Get Channel Count` | `CALCulate:AVERage:COUNt?` |
| `Get Channel Maximum` | `CALCulate:AVERage:MAXimum?` |
| `Get Channel Minimum` | `CALCulate:AVERage:MINimum?` |
| `Get Channel Peak To Peak` | `CALCulate:AVERage:PTPeak?` |
| `Get Maximum Timestamp` | `CALCulate:AVERage:MAXimum:TIME?` |
| `Get Minimum Timestamp` | `CALCulate:AVERage:MINimum:TIME?` |

**§14 — Temperature**

| Keyword | Vendor command(s) |
|---|---|
| `Configure RTD` | `[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]`, `[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]?`, `[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE`, `[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE?` … (+4) |
| `Configure Temperature` | `CONFigure:TEMPerature`, `[SENSe:]TEMPerature:APERture`, `[SENSe:]TEMPerature:APERture?`, `[SENSe:]TEMPerature:NPLC` … (+3) |
| `Configure Thermistor` | `[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE`, `[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE?` |
| `Configure Thermocouple` | `[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk`, `[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk?`, `[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction`, `[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE` … (+4) |
| `Get Reference Junction` | `[SENSe:]TEMPerature:RJUNction?` |
| `Measure Temperature` | `MEASure:TEMPerature?` |
| `Set Temperature Units` | `UNIT:TEMPerature`, `UNIT:TEMPerature?` |

**§14.1 — Four-wire and resistance**

| Keyword | Vendor command(s) |
|---|---|
| `Configure 4 Wire Resistance` | `CONFigure:FRESistance`, `[SENSe:]FRESistance:APERture`, `[SENSe:]FRESistance:APERture?`, `[SENSe:]FRESistance:NPLC` … (+9) |
| `Measure 4 Wire Resistance` | `MEASure:FRESistance?` |
| `Set Four Wire Mode` | `ROUTe:CHANnel:FWIRe`, `ROUTe:CHANnel:FWIRe?` |

**§15.2 — Switching and routing**

| Keyword | Vendor command(s) |
|---|---|
| `Close Channel` | `ROUTe:CLOSe`, `ROUTe:CLOSe?` |
| `Close Channel Exclusive` | `ROUTe:CLOSe:EXCLusive` |
| `Close Channels` | `ROUTe:CLOSe`, `ROUTe:CLOSe?` |
| `Open Channel` | `ROUTe:OPEN`, `ROUTe:OPEN?` |
| `Open Channels` | `ROUTe:OPEN`, `ROUTe:OPEN?` |

**§16.1 — 34907A digital input**

| Keyword | Vendor command(s) |
|---|---|
| `Configure Digital Input` | `CONFigure:DIGital:BYTE` |
| `Read Digital Byte` | `MEASure:DIGital:BYTE?`, `[SENSe:]DIGital:DATA:{BYTE|WORD}?` |
| `Read Digital Word` | `[SENSe:]DIGital:DATA:{BYTE|WORD}?` |

**§16.2 — 34907A digital output**

| Keyword | Vendor command(s) |
|---|---|
| `Get Digital Output` | `SOURce:DIGital:STATe?` |
| `Write Digital Byte` | `SOURce:DIGital:DATA[:{BYTE|WORD}]`, `SOURce:DIGital:DATA[:{BYTE|WORD}]?` |
| `Write Digital Word` | `SOURce:DIGital:DATA[:{BYTE|WORD}]`, `SOURce:DIGital:DATA[:{BYTE|WORD}]?` |

**§16.3 — 34907A totalizer**

| Keyword | Vendor command(s) |
|---|---|
| `Clear Totalizer` | `[SENSe:]TOTalize:CLEar:IMMediate` |
| `Configure Totalizer` | `CONFigure:TOTalize` |
| `Get Totalizer Edge` | `[SENSe:]TOTalize:SLOPe`, `[SENSe:]TOTalize:SLOPe?` |
| `Read Totalizer` | `MEASure:TOTalize?`, `[SENSe:]TOTalize:DATA?` |
| `Set Totalizer Edge` | `[SENSe:]TOTalize:SLOPe`, `[SENSe:]TOTalize:SLOPe?` |
| `Set Totalizer Read Mode` | `[SENSe:]TOTalize:TYPE`, `[SENSe:]TOTalize:TYPE?` |
| `Start Totalizer` | `[SENSe:]TOTalize:STARt:IMMediate` |
| `Stop Totalizer` | `[SENSe:]TOTalize:STOP[:IMMediate]` |

**§16.4 — 34907A DAC**

| Keyword | Vendor command(s) |
|---|---|
| `Get DAC Voltage` | `SOURce:VOLTage`, `SOURce:VOLTage?` |
| `Set DAC Voltage` | `SOURce:VOLTage`, `SOURce:VOLTage?` |

**§17 — Alarms and scaling**

| Keyword | Vendor command(s) |
|---|---|
| `Clear Alarm` | `OUTPut:ALARm:CLEar:ALL`, `OUTPut:ALARm{1|2|3|4}:CLEar` |
| `Configure Alarm Output` | `OUTPut:ALARm:MODE`, `OUTPut:ALARm:MODE?`, `OUTPut:ALARm:SLOPe`, `OUTPut:ALARm:SLOPe?` … (+2) |
| `Configure Digital Pattern Alarm` | `CALCulate:COMPare:DATA`, `CALCulate:COMPare:DATA?`, `CALCulate:COMPare:STATe`, `CALCulate:COMPare:STATe?` … (+2) |
| `Configure Digital Pattern Mask` | `CALCulate:COMPare:MASK`, `CALCulate:COMPare:MASK?` |
| `Disable Scaling` | `CALCulate:SCALe:STATe`, `CALCulate:SCALe:STATe?` |
| `Enable Lower Alarm` | `CALCulate:LIMit:LOWer:STATe`, `CALCulate:LIMit:LOWer:STATe?` |
| `Enable Scaling` | `CALCulate:SCALe:STATe`, `CALCulate:SCALe:STATe?` |
| `Enable Upper Alarm` | `CALCulate:LIMit:UPPer:STATe`, `CALCulate:LIMit:UPPer:STATe?` |
| `Get Alarm State` | `STATus:ALARm:CONDition?`, `STATus:ALARm[:EVENt]?`, `SYSTem:ALARm?` |
| `Set Lower Alarm Limit` | `CALCulate:LIMit:LOWer`, `CALCulate:LIMit:LOWer?` |
| `Set Scaling Gain` | `CALCulate:SCALe:GAIN`, `CALCulate:SCALe:GAIN?` |
| `Set Scaling Offset` | `CALCulate:SCALe:OFFSet`, `CALCulate:SCALe:OFFSet:NULL`, `CALCulate:SCALe:OFFSet?` |
| `Set Scaling Unit` | `CALCulate:SCALe:UNIT`, `CALCulate:SCALe:UNIT?` |
| `Set Upper Alarm Limit` | `CALCulate:LIMit:UPPer`, `CALCulate:LIMit:UPPer?` |

**§18.1 — 34972A LAN**

| Keyword | Vendor command(s) |
|---|---|
| `Get LAN Configuration` | `SYSTem:COMMunicate:LAN:CONTrol?`, `SYSTem:COMMunicate:LAN:DOMain?`, `SYSTem:COMMunicate:LAN:MAC?` |
| `Set LXI Identify` | `LXI:IDENtify[:STATE]`, `LXI:IDENtify[:STATE]?` |

**§18.2 — 34972A USB and files**

| Keyword | Vendor command(s) |
|---|---|
| `Configure USB Log Format` | `MMEMory:FORMat:READing:CSEParator`, `MMEMory:FORMat:READing:CSEParator?`, `MMEMory:FORMat:READing:RLIMit`, `MMEMory:FORMat:READing:RLIMit?` |
| `Export Readings To USB` | `MMEMory:EXPort?` |
| `List USB Configuration Files` | `MMEMory:IMPort:CATalog?` |
| `Set Scan Logging To USB` | `MMEMory:LOG[:ENABle]`, `MMEMory:LOG[:ENABle]?` |

**Drift guard.** Three checks, guarding three edges. Each earlier revision guarded one and was
defeated at another.

1. **reference → map** — re-extract commands from
   `reference/Keysight_34970A_34972A_Command_Reference.md` and fail when any declared command is
   absent from the map.

   This check **shall not reuse the map generator's extractor output as its expected set**: v1.6
   asserted the map against the list its own generator produced, which proved only self-consistency
   and is how a false 100% coverage claim survived a commit.

   It **shall reconcile at least two independent extractions**, not one. A single extraction is
   demonstrably insufficient — three methods have been applied to this reference and none is a
   superset of the others:

   | Method | Commands | Missed |
   |---|---:|---|
   | block titles (v1.6) | 193 | 158 |
   | per-block Syntax sections (v1.7) | 347 | the 4 RTD/FRTD `OCOMpensated` forms |
   | `Commands A-Z` index (v1.9) | 342 | 12 colon-free commands (`ABORt`, `FETCh?`, `INITiate`, …) |

   Every discrepancy between extractions shall be resolved to either a real command or a documented
   notation artifact — abbreviated aliases and optional-node bracket differences are artifacts;
   anything else is a real command. Unresolved discrepancies fail the check.
2. **map → `api/public_api.yaml`** — fail when a `PUBLIC` command has no bound keyword, or when a
   device-facing keyword in the map is absent from `public_api.yaml`.
3. **guides → `api/public_api.yaml`** — fail when any mandatory RFDS-002 §8/§9, RFDS-013 §7.1, or
   RFDS-014 keyword is absent from `public_api.yaml`.

**Driver-level keywords are exempt from the command-binding requirement.** The v1.7 guard failed
when a keyword appeared in `public_api.yaml` but not in the map — which would have failed the build
for correctly implementing the mandatory API, with deletion as the obvious way to make it pass. A
guard that punishes conformance is worse than no guard.

**Capability-group completeness (D4).** Every mapped command carries a `capability_group`. RFDS-002
§9 makes a group's full keyword set mandatory once the capability is declared, and §8 forbids partial
implementation without an approved deviation. The guard shall therefore also fail when a declared
capability group is missing any keyword of its group.

All checks are part of the §29.1 verification sequence.

**Counts.** ~155 public keywords total — ~121 device-facing across **351** dispositioned vendor
commands, plus ~34 mandatory driver-level keywords carrying no command. That is roughly **two and a half times** the keyword surface of the
largest existing driver in the repository (`rf_ngi_n83624`, 62 keywords), and the §38 twelve-phase
estimate was made before any of these numbers were known. Scope shall be re-assessed at Phase 1
Gate 5 against the actual Gate 1–5 effort, using ~155 rather than 121.

---

## 10. Device Error Queue

The driver shall implement:

RFDS-002 §9.2 canonical signatures:

```text
Get Device Error(alias=None) -> dict
Get All Device Errors(alias=None, max_count=100) -> list[dict]
Clear Device Errors(alias=None) -> None
Device Error Queue Should Be Empty(alias=None) -> None
```

RFDS-002 §9.2 also fixes the error dictionary schema:

```yaml
code: 0
message: No error
raw: '0,"No error"'
source: device
```

`raw` preserves the unparsed device response, satisfying RFDS-008 §6.3 raw-evidence preservation.

Exceptions raised from this group shall carry an RFDS-007 §8 code, the RFDS-007 §10 payload fields,
and the RFDS-007 §11 public message format (§2.4).

### 10.1 Error handling requirements

The driver shall:

- parse `SYST:ERR?` responses strictly;
- preserve device error number and message;
- distinguish no-error from malformed response;
- raise `DriverProtocolError` for malformed error responses;
- never interpret malformed SCPI as `0,"No error"`;
- provide complete queue draining with bounded iteration;
- record device error evidence in conformance tests.

### 10.2 Drain bound

RFDS-002 §9.2 already provides the bound as a canonical argument — `max_count`, default `100` — and
requires that "the driver shall prevent unbounded reads from an error queue". Earlier revisions of
this plan placed the bound in configuration instead; that is withdrawn in favour of the canonical
argument.

On reaching the bound the driver shall **not** report the queue as successfully emptied. It shall
return the errors collected so far together with an explicit truncation indicator, so the caller can
distinguish "the queue is empty" from "the queue did not empty within the bound". Silently
presenting a truncated drain as a clean queue is prohibited on the same grounds as §10.1's
malformed-response rule.

`Device Error Queue Should Be Empty` shall fail — not pass — when the drain was truncated.

---

## 11. Measurement Engine

Planned measurement capabilities:

```text
Measure DC Voltage
Measure AC Voltage
Measure DC Current
Measure AC Current
Measure Resistance
Measure 4 Wire Resistance
Measure Frequency
Measure Period
```

For applicable measurement families the driver should also expose:

```text
Configure <Quantity>
Measure <Quantity>
Get <Quantity> Configuration
```

### 11.1 Measurement requirements

The implementation shall:

- validate internal DMM availability before transmission (§4.4);
- validate channels before transmission;
- validate installed card compatibility;
- validate model restrictions;
- validate range and resolution arguments;
- return numeric values rather than raw SCPI text where practical;
- preserve unit metadata where appropriate;
- expose clear exceptions for unsupported combinations.

DMM availability is checked first, because on a switch-only frame no measurement argument
combination is valid regardless of channel or card. The resulting failure shall be a normalized
`DriverUnsupportedOperationError` raised locally, with no command transmitted.

The same gate applies to the scan and acquisition engine (§12), the statistics functions (§13), and
the temperature engine (§14), all of which depend on the internal DMM.

### 11.3 Card and channel restrictions (source verification required)

Measurement availability is not uniform across cards and channels. The following restrictions shall
be **verified against the command reference** and recorded as capability-model data before Phase 3,
rather than left to generic "card compatibility" validation:

```yaml
current_measurement:
  status: RESOLVED
  capable_channels:
    34901A: [21, 22]        # the only current-capable channels in the family
    34902A: []
    34903A: []
    34904A: []
    34905A: []
    34906A: []
    34907A: []
    34908A: []
  source: Command Reference, "34901A 20 Channel Multiplexer (2/4-wire) Module (channels 21..."

four_wire_resistance:
  status: RESOLVED
  pairing_offset:
    34901A: 10             # channel n in Bank 1 pairs with n+10 in Bank 2
    34902A: 8              # channel n in Bank 1 pairs with n+8
    34908A: null           # single-ended; no four-wire support
  source: Command Reference, "pairs channel n in Bank 1 with channel n+10 (34901A) or n+8 (34902A)"
```

A DC or AC current request on any channel outside `34901A: [21, 22]` shall raise
`DriverUnsupportedOperationError` before transmission.

Once recorded, these restrictions shall be enforced as **pre-transmission** validation per §11.1,
producing `DriverUnsupportedOperationError` rather than a device error.

### 11.2 Unsupported or unverified functions

Continuity and diode measurement shall not be implemented unless an authoritative device source establishes corresponding supported behavior.

Initial disposition:

```yaml
continuity: NOT_APPLICABLE
diode:      NOT_APPLICABLE
reason: >
  Neither function exists on this instrument family. A full-text search of the
  Keysight 34970A/34972A Command Reference for "continuity" and "diode" returns
  zero occurrences. These are 34401A-class DMM functions, not 349xx functions.
```

No substitute implementation shall be invented by mapping these functions to resistance or voltage
measurements — there is no device function to substitute for.

---

## 12. Scan and Acquisition Engine

Planned scan-related operations:

```text
Configure Scan List
Get Scan List
Clear Scan List

Configure Trigger Source
Get Trigger Source
Set Trigger Count
Get Trigger Count
Set Trigger Timer
Get Trigger Timer

Initiate Scan
Abort Scan
Read Scan
Fetch Readings
Read Buffered Readings
Get Reading Count
Clear Reading Memory
Get Scan Start Time
```

The driver shall preserve the semantic distinctions between:

```text
INITiate
FETCh?
READ?
R?
DATA:REMove?
```

These commands shall not be treated as interchangeable because they have different acquisition, buffering, and reading-memory behavior.

`R?` and `DATA:REMove?` remove readings from memory and are therefore **destructive reads** subject
to §22.3, not ordinary queries.

### 12.1 Monitor mode (source verification required)

These mainframes provide a monitor capability that continuously reads a single channel independently
of the scan list. It is absent from this plan and shall receive an explicit disposition rather than
remain unmentioned:

Confirmed present in the command reference:

```text
ROUTe:MONitor
ROUTe:MONitor?
ROUTe:MONitor:DATA?
ROUTe:MONitor:STATe
ROUTe:MONitor:STATe?
```

```yaml
monitor_mode:
  status: PUBLIC
  risk: LOW
  note: >
    Continuously reads one channel independently of the scan list. The reference
    states alarms are evaluated "during a scan or a monitor measurement", so
    monitor and scan are distinct acquisition modes that both consume the
    internal DMM.
  gates:
    - §4.4 internal-DMM availability
    - §5.2 locking -- monitor and an active scan contend for the DMM
```

Planned keywords: `Configure Channel Monitor`, `Get Channel Monitor`, `Read Monitor Data`,
`Set Monitor State`, `Get Monitor State`. Exact canonical names shall be fixed in the public API
contract (§9).

---

## 13. Statistics

Planned statistics functions:

```text
Get Channel Minimum
Get Channel Maximum
Get Channel Average
Get Channel Count
Get Channel Peak To Peak
Clear Channel Statistics
Get Minimum Timestamp
Get Maximum Timestamp
```

Recommended structured return format:

```python
{
    "channel": 103,
    "minimum": 1.234,
    "maximum": 1.241,
    "average": 1.237,
    "peak_to_peak": 0.007,
    "count": 100,
    "minimum_timestamp": "2026-08-17T16:31:36.341Z",
    "maximum_timestamp": "2026-08-17T16:32:04.118Z"
}
```

The timestamp fields correspond to the `Get Minimum Timestamp` and `Get Maximum Timestamp`
keywords listed above and shall be present in the structured return so the aggregate result is
self-contained. Where the device cannot supply a timestamp, the field shall be `None` rather than
omitted or silently defaulted.

The public API shall not leak undocumented SCPI formatting into higher-level Robot Framework tests.

---

## 14. Temperature Engine

Planned sensor support:

```text
Thermocouple
2-wire RTD
4-wire RTD
Thermistor
```

Configuration shall include applicable device settings such as:

```text
Thermocouple type
Reference junction type
Reference junction value
Thermocouple check
RTD type
RTD reference resistance
Thermistor type
Temperature units
```

### 14.1 Channel-pair validation

The implementation shall understand four-wire pairing rules for supported cards rather than treating
all channel numbers as independent.

Invalid pairings shall be rejected before protocol transmission when deterministically known.

The pairing rule is **card-dependent**: the paired channel is offset from the source channel by a
fixed amount that differs between multiplexer cards, and four-wire operation reduces the usable
channel count on the card.

```yaml
four_wire_pairing:
  status: RESOLVED
  offset:
    34901A: 10             # n pairs with n+10
    34902A: 8              # n pairs with n+8
  unsupported:
    - 34908A               # 40-channel single-ended
  source: >
    Command Reference: "pairs channel n in Bank 1 with channel n+10 in Bank 2
    (34901A) or n+8 (34902A) to provide source and measurement connections".
```

Configuring a four-wire function occupies both channels of each pair, so the usable channel set is
halved and the paired channel shall not be independently addressable while the function is active. Channel
enumeration (§15) and channel validation shall both reflect the reduced channel set when a four-wire
function is configured — reporting the full channel list while a four-wire function is active would
misrepresent the instrument.

---

## 15. Switching and Routing

Planned switching functions:

```text
List Switch Channels
Open Channel
Close Channel
Open Channels
Close Channels
Get Channel State
Open All Owned Channels
Channel Should Be Open
Channel Should Be Closed
```

### 15.2 Card-class-aware switching (source verification required)

The keyword set above shall not assume uniform switching behaviour. The supported cards span at
least three distinct topologies, and a uniform `Close Channels` will either fail or produce an
unrequested state depending on which card is installed:

```yaml
switching_topologies:
  status: RESOLVED
  by_card:
    34901A: multiplexer            # 20 Channel Multiplexer (2/4-wire)
    34902A: multiplexer            # 16 Channel Multiplexer
    34903A: actuator               # 20 Channel Actuator/GP Switch
    34904A: matrix                 # 4 x 8 Two-Wire Matrix
    34905A: rf_multiplexer
    34906A: rf_multiplexer
    34908A: multiplexer            # 40 Channel Single-Ended
  matrix_addressing:
    form: row/column crosspoint
    example: "channel 234 = intersection of row 3 and column 4"
    source: Command Reference, ROUTe:CLOSe description
```

Requirements now resolvable from source:

- **multiplexer** cards are break-before-make within a bank; a multi-channel close within one bank
  shall be rejected before transmission;
- **34903A actuator** relays are independent; simultaneous closure is valid;
- **34904A matrix** is addressed as `<slot><row><column>` — a crosspoint model is required, and it
  shall not be addressed as a flat multiplexer channel;
- **34905A/34906A** RF multiplexers reset to "Channels s11 and s21 Selected" rather than all-open,
  which the safe-state model (§21) shall account for.

Requirements:

- each installed card's topology class shall be recorded in the capability model, verified against
  the command reference;
- `Close Channels` shall validate the request against the installed card's topology and reject
  same-bank multiplexer conflicts **before** transmission, consistent with §11.1;
- the matrix card shall either receive a crosspoint addressing model or an explicit `EXCLUDED`
  disposition — it shall not be addressed as if it were a multiplexer;
- `Get Channel State` shall return topology-appropriate state.

### 15.1 Resource ownership

The driver shall track resources owned by the current session.

It shall not assume ownership of every relay or switch channel in the mainframe.

Safe shutdown shall act only on explicitly owned resources unless the bench contract explicitly grants broader ownership.

---

## 16. 34907A Multifunction Module

The 34907A shall have a dedicated capability implementation.

### 16.1 Digital input

```text
Read Digital Byte
Read Digital Word
```

### 16.2 Digital output

```text
Write Digital Byte
Write Digital Word
Get Digital Output
```

Conditional, pending source verification:

```yaml
Get Digital Direction:
  status: NOT_APPLICABLE
  reason: >
    No queryable digital-direction command exists. A full-text search of the
    Command Reference for a direction query (DIGital...DIRection, :DIRection,
    DIGital...MODE) returns no such command.
  note: >
    Direction state does exist -- both reset tables show "Both DIO Ports =
    Input" -- but it is not readable over the remote interface.
```

The keyword is **dropped**. It shall not be implemented.

Driver-side synthesis of a direction register — inferring and caching direction from prior reads and
writes, then presenting it as device state — is prohibited, on the same grounds as §11.2: it would
report invented device behavior as measured fact.

Where direction *is* established as observable, direction changes shall be represented as explicit
state transitions and side effects in the AI contract.

### 16.3 Totalizer

```text
Start Totalizer
Stop Totalizer
Read Totalizer
Clear Totalizer
Set Totalizer Edge
Get Totalizer Edge
Set Totalizer Read Mode
```

### 16.4 DAC

```text
Set DAC Voltage
Get DAC Voltage
```

DAC operations shall be classified as state-changing and potentially safety-relevant.

Blind automatic retries shall be prohibited for uncertain state-changing DAC writes.

The DAC output range is resolved from source:

```yaml
dac_output:
  status: RESOLVED
  command: "SOURce:VOLTage <voltage>,(@<ch_list>)"
  range_v: [-12.0, +12.0]
  resolution_v: 0.001
  channels: [04, 05]        # per 34907A slot, e.g. @304 and @305
  source: Command Reference, SOURce:VOLTage parameter table
```

The range shall be validated **before transmission**; a request outside −12 V to +12 V shall raise a
local validation error rather than being transmitted and rejected by the device. Values shall be
quantised or rejected at 0.001 V resolution rather than silently truncated by the instrument.

Write verification shall use the bounded-poll reconciliation of §22.2, not a single immediate
readback.

---

## 17. Alarms and Scaling

Planned alarm functions:

```text
Set Lower Alarm Limit
Set Upper Alarm Limit
Enable Lower Alarm
Enable Upper Alarm
Get Alarm Limits
Clear Alarm
Get Alarm State
```

Planned scaling functions:

```text
Set Scaling Gain
Set Scaling Offset
Set Scaling Unit
Enable Scaling
Disable Scaling
```

Planned digital-pattern functions:

```text
Configure Digital Pattern Alarm
Configure Digital Pattern Mask
```

All documented state changes caused by alarm configuration shall be recorded in the AI contract and protocol vectors.

---

## 18. 34972A-Specific Functions

34972A-only functionality shall be exposed only when the connected model supports it.

Calling a model-specific function on an unsupported mainframe shall raise a normalized
`DriverUnsupportedOperationError`.

### 18.1 LAN capabilities are split by communication impact

Model gating alone is insufficient for the LAN family. When the driver is connected over LAN — the
primary 34972A transport per §30 — changing the IP address, subnet mask, gateway, DHCP mode, or
hostname destroys the connection delivering the command. The command may or may not have been
applied before the link dropped, and §22.2 reconciliation is **impossible over the affected
transport**, because the path required to query the result no longer exists.

```yaml
lan_query:
  status: PUBLIC
  risk: NONE
  members: [hostname query, IP query, subnet query, gateway query,
            DHCP state query, MAC query, LAN status]

lan_configuration:
  status: EXCLUDED
  risk: HIGH
  members: [set IP, set subnet, set gateway, set DHCP mode, set hostname]
  reason: >
    Changes the transport the command is delivered over. §22.2 reconciliation
    cannot be performed on the affected connection. Network provisioning is a
    separate procedure, not general test automation.
```

If any LAN write is later promoted to public it shall: require an explicit confirmation argument; be
documented as terminating the session; and be **prohibited when the active transport is the one
being reconfigured** — permitted over USB while changing LAN parameters, never over LAN.

### 18.2 Remaining 34972A families

```text
USB drive catalog
Configuration file import
Scan logging to USB
Memory/file operations
```

These shall receive individual dispositions in the vendor coverage audit (§20). Configuration file
import in particular can alter instrument state wholesale and shall be risk-classified accordingly,
not treated as a routine file operation.

---

## 19. Calibration and Destructive Diagnostic Commands

Calibration and service-level commands shall not automatically become public Robot Framework keywords.

Default disposition:

```text
Calibration write commands:        EXCLUDED
Calibration security changes:      EXCLUDED
Relay-cycle counter reset:         EXCLUDED
Engineering DIAG POKE operations:  EXCLUDED
```

Read-only diagnostic operations may be exposed where safe and justified.

Explicit decision required before Phase 8:

```yaml
relay_cycle_count_read: UNDECIDED
```

Resetting the relay-cycle counter is excluded above, but *reading* it is a non-destructive query
carrying real relay-maintenance value. Whether it becomes a public read-only diagnostic shall be an
explicit recorded decision in `protocol/vendor_command_coverage.yaml`, not an omission. The same
applies to any other read-only calibration or service query considered under open question 5.

Every excluded vendor command shall remain visible in the vendor command coverage inventory.

---

## 20. Vendor Command Coverage Audit

Create:

```text
protocol/vendor_command_coverage.yaml
```

Every relevant command from the supplied device command reference shall receive an explicit disposition.

Example:

```yaml
- command: "SOURce:VOLTage"
  status: PUBLIC
  keyword: "Set DAC Voltage"

- command: "CALibration?"
  status: EXCLUDED
  reason: "Calibration/service operation requires separate service procedure."

- command: "DIAGnostic:POKE:SLOT:DATA"
  status: EXCLUDED
  reason: "Engineering/service operation not suitable for general automation."

- command: "<unverified-command>"
  status: UNKNOWN
  reason: "Authoritative behavior not established."
```

Allowed statuses:

```text
PUBLIC
PRIVATE
INTERNAL
EXCLUDED
NOT_APPLICABLE
UNKNOWN
DEPRECATED
```

This file shall prove that the vendor command source was reviewed systematically.

---

## 21. Safety Model

Safe shutdown shall be ownership-aware.

Example configuration:

```yaml
safety:
  abort_active_scan: true

  switching:
    owned_channels:
      - 201
      - 202
    safe_state:
      201: OPEN
      202: OPEN

  digital_outputs:
    owned_ports:
      - 301
    safe_values:
      301: 0

  dac_outputs:
    owned_channels:
      - 304
      - 305
    safe_voltage_v:
      304: 0.0
      305: 0.0
```

### 21.1 Safety rules

The driver shall:

- never blindly open or close every relay;
- never blindly zero every DAC;
- never assume exclusive ownership of shared bench resources;
- avoid replaying uncertain state-changing writes;
- log safety actions;
- use RFDS-018 bench data for deployment-specific safe states;
- fail closed when required safety information is unknown.

### 21.2 Behaviour when no ownership is declared

"Fail closed" shall be defined explicitly, because the default installation declares no ownership at
all — §23.1 requires defaults to contain no bench-specific data — and the ambiguous readings of that
phrase include the dangerous one ("act on everything").

With no ownership configured, `Safe Shutdown` shall:

1. abort any active scan — §21 requires this unconditionally and it depends on no ownership data;
2. report every ownership-dependent action as `SKIP`, each with an explicit reason;
3. return an overall result that distinguishes "placed in a safe state" from "no safe state was
   established", and shall **never** report an unqualified success it did not achieve;
4. touch no relay, digital output, or DAC channel.

The return value shall include a per-action outcome list so callers can assert on individual
actions rather than a single boolean:

```python
{
    "safe": True,
    "actions": [
        {"action": "scan_abort",      "status": "PASS"},
        {"action": "switching_safe",  "status": "SKIP", "reason": "no owned channels configured"},
        {"action": "digital_safe",    "status": "SKIP", "reason": "no owned ports configured"},
        {"action": "dac_safe",        "status": "SKIP", "reason": "no owned DAC channels configured"},
    ],
}
```

A `SKIP` is an honest report that nothing was owned, not a failure. Reporting `PASS` for an action
that was never performed is prohibited.

---

## 22. Retry and Recovery Rules

### 22.1 Read/query operations

Per RFDS-004 §14.1 the **default replay policy for all write and transaction operations is
`NEVER`**. Retry is the exception, permitted only where a precondition is proven.

RFDS-004 §14.2 permits an automatic retry only when one of these is **proven** — not assumed, and
not inferred from the operation's name:

- no outbound byte was transmitted;
- connection establishment failed before a session was created;
- the protocol layer explicitly marked the operation as idempotent and safe to replay;
- a read-only transaction is documented as replay-safe;
- a backend-internal partial operation can be completed without repeating already accepted data.

Operations that may satisfy the third or fourth condition here:

```text
*IDN?
selected read-only status queries
```

Even for these, the precondition shall be established rather than presumed. §22.3 adds a stricter
prohibition, which RFDS-001 §7.1 permits a lower-level document to do.

`SYST:ERR?` is **not** in this category. See §22.3.

### 22.2 State-changing operations

Automatic blind retry shall not be used where delivery may have occurred.

Examples:

```text
ROUT:CLOS ...
SOUR:VOLT ...
digital output writes
memory writes
configuration-changing commands
```

For uncertain delivery, recovery shall use an explicit reconciliation strategy:

```text
query state
compare expected state
recover or fail explicitly
```

Reconciliation shall be a **bounded poll**, not a single immediate readback. Relays and DAC outputs
have real settling time, and an instrument may acknowledge a write before its readback register
reflects it; a single instantaneous query therefore produces false failures on real hardware.

Requirements:

- poll until the observed state matches the requested state, or until a deadline expires;
- the timeout and poll interval shall be configurable per §23, with documented defaults;
- verification failure shall raise an error carrying the requested value, the last observed value,
  the attempt count, and elapsed time — enough to distinguish "never applied" from "applied too
  slowly";
- reconciliation shall never be silently skipped when verification is enabled.

Where reconciliation is impossible on the affected transport, the operation shall be excluded rather
than left unverifiable — see §18.1.

### 22.3 Destructive reads

A third category exists between §22.1 and §22.2: operations that are read-only with respect to
device *configuration* but state-changing with respect to device *buffers*.

```text
SYST:ERR?          pops an entry from the error queue
R?                 reads and removes readings from memory
DATA:REMove?       removes a specified count from reading memory
```

```yaml
retry: PROHIBITED
```

Automatic retry of a destructive read is prohibited. If the command was transmitted and the response
was lost, the removed data is gone; a retry returns the *next* entry, or an empty result, and the
loss is invisible.

For `SYST:ERR?` this is not merely a lost diagnostic. The error queue is how the driver learns that a
**previous state-changing command failed**, so silently discarding an entry can mask a failed relay
or DAC write and produce a false clean state — exactly what §10.1 exists to prevent.

On timeout or malformed response, a destructive read shall surface the failure and report the
affected buffer state as `UNKNOWN`. It shall never be reported as empty or error-free.

---

### 22.4 Device performance contract (RFDS-001-PERF-001)

Required fields. Values marked `TBM` shall be **measured** during Phase 2 HIL and recorded here; they
shall not be estimated, and an unmeasured value shall not be presented as a specification.

```yaml
expected_connection_time_s:   TBM      # per transport: GPIB, RS-232, LAN, USB
normal_keyword_latency_s:     TBM      # per keyword class: query, configure, switch
stabilization_delay_s:
  relay_settle:               TBM      # §22.2 bounded-poll reconciliation depends on this
  dac_settle:                 TBM
  dmm_range_change:           TBM
maximum_operation_timeout_s:  TBM      # per operation class; finite by §5
retry_count_and_backoff:               # §22.1 -- default policy is NEVER (RFDS-004 §14.1)
  queries:                    bounded, preconditions per §22.1
  writes:                     0 (no blind retry, §22.2)
  destructive_reads:          0 (prohibited, §22.3)
acquisition_throughput:       TBM      # readings/s during scan
polling_interval_s:
  setpoint_verify:            configurable, §23
  monitor_mode:               TBM
cancellation_latency_s:       TBM      # Robot Framework stop -> operation abandoned
concurrency_limitations:      see §5.5 -- concurrency disabled by default
known_slow_operations:
  - Run Self Test
  - full 24-channel scan
  - Reset Device / Preset Device (all relays reopen)
```

Per RFDS-001-PERF-001 these are a *contract*, not a target: performance optimization shall not
compromise safety, correctness, or evidence. §25's per-keyword `timing` / `timeout` /
`stabilization` fields, and RFDS-018 §6.9's bench scheduling rules, both roll up from this table and
shall remain consistent with it.

## 23. Driver Configuration Model

The package shall implement all mandatory RFDS configuration keywords:

```text
Get Driver Configuration Schema
Get Driver Default Configuration
Get Driver Configuration
Validate Driver Configuration
Import Driver Configuration
Export Driver Configuration
Save Driver Configuration
Load Driver Configuration
List Driver Configuration Profiles
Delete Driver Configuration Profile
Reset Driver Configuration
```

Configuration layout:

```text
config/
├── schema.json
├── schema.lock
├── default.json
└── examples/
    ├── simulator.json
    ├── 34970a_gpib.json
    ├── 34970a_rs232.json
    ├── 34972a_lan.json
    └── 34972a_usb.json
```

One configuration example shall exist per qualified transport in §30, so the configuration set and
the HIL matrix cannot diverge.

### 23.1 Configuration requirements

Defaults shall:

- remain disconnected;
- contain no private IP addresses;
- contain no personal COM ports;
- contain no credentials;
- contain no bench-specific serial numbers;
- validate before application;
- never silently fall back from an explicitly requested invalid profile.

---

## 24. Plugin Architecture

Add:

```text
plugin.py
plugin_manifest.json
```

Expected plugin operations:

```python
get_descriptor()
validate_environment()
create_library()
discover_hardware()
```

Requirements:

- importing the plugin performs no hardware I/O;
- descriptor retrieval performs no hardware I/O;
- `create_library()` returns an unconnected driver;
- discovery is explicit and bounded;
- simulation shall never silently replace requested hardware.

The package shall expose the RFDS-015 §8 entry point through `pyproject.toml` under the group
**`rfds.drivers`**:

```toml
[project.entry-points."rfds.drivers"]
"keysight.349xx" = "rf_keysight349xx.plugin"
```

The entry-point key shall equal the RFDS-015 §7.1 plugin ID and the `plugin_id` declared in both
`resources/plugin_manifest.json` and `ai/ai_contract.yaml` (RFDS-017 §4).

---

## 25. AI Driver Contract

Create before implementation:

```text
ai/ai_contract.yaml
ai/ai_contract.lock
```

RFDS-017 is the **sole normative source** for the structure and required fields of
`ai_contract.yaml` and `ai_contract.lock`. The list below is indicative; where it and RFDS-017
differ, RFDS-017 governs, and a field expressing a value owned by another RFDS specification shall
use that specification's canonical vocabulary or fail contract validation.

`ai_contract.yaml` shall declare a root `identity` section whose `plugin_id` **shall equal** the
RFDS-015 plugin manifest `plugin_id` (RFDS-017 §4) — here `keysight.349xx` (§3.1). Both files shall
be reachable at release time as a `repository_path`, or as a `package_resource` per RFDS-015 §9.2.1
where runtime access is required.

Each exported Robot Framework keyword shall include:

```text
canonical keyword
aliases
signature
purpose
inputs
input types
units
return schema
preconditions
postconditions
side effects
state transition
risk level
idempotency
timing
timeout
stabilization
retry policy
errors
resource ownership
verification oracle
supported models
supported modules
protocol operation
```

The contract shall explicitly model:

```text
34970A vs 34972A
installed module map
internal DMM installed/enabled
scan state
digital I/O direction
owned routing resources
34907A DAC state
transport type
```

The AI contract, capability model, public API inventory, and RFDS-019 protocol vectors shall remain synchronized.

---

## 26. RFDS-018 Test Bench Contract

The package shall provide a template:

```text
ai/system_ai_contract.template.yaml
```

Per RFDS-005 §6 this template lives beside the AI contract in `ai/`, not in a separate directory.

Per RFDS-018 §5 the **deployed** contract is named `system_ai_contract.yaml` and **shall live at the
deployment/bench level, outside any single driver's package tree**. Only the template ships with
this driver.

RFDS-018 §6 fixes ten mandatory sections; a bench contract for this driver shall provide all of
them:

| § | Section | Content for this driver |
|---|---|---|
| 6.1 | Available Drivers | `plugin_id` `keysight.349xx`, approved version range, Robot alias, pointer to this driver's `ai_contract.yaml` |
| 6.2 | Physical Topology | wiring between mainframe slots, relay paths, DUT interfaces, measurement points |
| 6.3 | Shared Resources | GPIB/LAN/USB/serial resources and any exclusive bench resources, consistent with §23 configuration and the RFDS-017 `exclusive_resources` declaration |
| 6.4 | Signal Graph | producers and consumers so a planner can trace a signal across drivers |
| 6.5 | Preferred Measurement Sources | which instrument measures each quantity where this driver and another both could |
| 6.6 | Requirement Coverage | system requirements mapped to drivers and RFDS-017 verification objectives |
| 6.7 | Test Templates | multi-driver workflows expressed via driver aliases and RFDS-013 capability IDs, not hard-coded keyword sequences |
| 6.8 | Bench Constraints | operator actions, safety zones, maximum simultaneous operations, environmental limits |
| 6.9 | Scheduling Rules | resource conflicts, driver ordering, stabilization rules consistent with RFDS-017 `stabilization_delay`, parallel execution limits |
| 6.10 | Global Safety | bench-wide forbidden sequences and the emergency shutdown workflow, executable in terms of aliases and keywords |

Sections 6.3, 6.8, 6.9, and 6.10 are where this driver's ownership model (§21) meets the bench: the
owned relay, digital-output, and DAC resources declared in §21 shall be consistent with the bench
contract's shared-resource and safety-zone declarations.

The driver package shall not invent laboratory wiring or bench safety assumptions.

---

## 27. Stateful Protocol Simulator

A protocol-boundary simulator shall be implemented.

The simulator shall emulate at least:

```text
34970A identity
34972A identity
installed cards
internal DMM state
measurement configuration
scan list
routing state
trigger source
trigger count
trigger timer
reading memory
statistics
error queue
34907A digital I/O
34907A totalizer
34907A DAC
alarms
scaling
34972A-only capability behavior
```

### 27.1 Fault injection

The simulator shall support deterministic faults:

```text
timeout
delayed response
empty response
malformed response
malformed error queue response
unsupported command
device error
disconnect mid-query
partial read
reconnect
protocol recovery test
```

### 27.2 Unmodelled resources

The simulator shall either model an addressed resource faithfully or reject the command as an
unsupported-command fault (§27.1). **Acknowledging a write that was not performed is prohibited.**

The prohibited behaviour is specific: accepting a write to a routing channel, digital port, or DAC
channel the simulator does not model, returning success, and then reporting the unchanged value on
readback. Every write-verify round trip against that resource then fails permanently, and the
failure presents as a driver or hardware defect rather than a simulator gap.

A conformance check shall assert that every channel the capability model reports as available is
actually modelled by the simulator, so the two cannot drift.

Simulator evidence shall always be labeled as simulator evidence.

Simulator results shall not be used to claim physical accuracy, real transport timing, or hardware safety validation.

---

## 28. RFDS-019 Protocol Conformance

Required tree:

```text
tests/conformance/
├── driver_call_protocol_conformance.robot
├── resources/
│   ├── conformance_keywords.resource
│   └── conformance_variables.resource
├── data/
│   ├── keyword_inventory.yaml
│   ├── protocol_vectors.yaml
│   └── exclusions.yaml
└── expected/
    └── response_schemas/
```

### 28.1 Required conformance coverage

For every exported public Robot Framework keyword:

```text
inventory status
canonical name
aliases
arguments/defaults
callability
device-facing classification
protocol vector
actual outbound protocol
raw inbound response
parsed return value
protocol error vectors
recovery vector
evidence reference
```

### 28.2 Acceptance target

The conformance suite shall provide:

- 100% public keyword inventory;
- 100% supported keyword callability;
- 100% device-facing keyword protocol-vector coverage or approved exclusion;
- outbound protocol verification;
- inbound protocol verification where applicable;
- return-value verification;
- error-vector verification;
- recovery verification;
- traceable evidence.

Trace capture shall begin before initial connection and identity traffic so that connection-time protocol operations are not omitted from evidence.

---

## 29. Testing Strategy

The completed project shall contain:

```text
tests/
├── unit/
├── protocol/
├── transport/
├── integration/
├── simulator/
├── robot/
├── conformance/
├── replay/
├── regression/
├── compatibility/
├── hil/
├── performance/
└── soak/
```

### 29.1 Mandatory verification sequence

**Deliverable gating (E1).** Several steps compare artifacts that are themselves Phase 1 Gate 1
deliverables. Until those exist the step **shall report `NOT_RUN`, never `PASS`** — RFDS-001-CLS-003
bars `NOT_RUN` from satisfying release acceptance, and RFDS-008 §6.1 bars recording an unperformed
check as success. A check that "passes" because its input is missing provides no assurance while
occupying a line in the acceptance sequence.

| Step | Requires | Available from |
|---|---|---|
| 22 metadata synchronization | `ai/ai_contract.yaml`, `ai_contract.lock` | Phase 1 Gate 1 |
| 24 structure validation, guards 2–3 | `api/public_api.yaml` | Phase 1 Gate 1 |
| 24 capability-group completeness | `capability/capability_model.yaml` | Phase 1 Gate 1 |
| 24 structure validation, guard 1 | reference + coverage map | **available now** |

Guard 1 is runnable today and shall be run today; it is what found the four missing RTD commands
in v1.9.


1. Python compilation checks
2. Ruff
3. Type checking
4. Unit tests
5. Protocol serialization tests
6. Protocol parsing tests
7. Transport contract tests
8. Simulator tests
9. Python integration tests
10. Robot Framework acceptance tests
11. RFDS-019 conformance
12. Timeout tests
13. Malformed-response tests
14. Device-error tests
15. Recovery tests
16. Clean-wheel installation test
17. Real 34970A HIL
18. Real 34972A HIL when claimed supported
19. Card-specific HIL
20. Resource-locking tests
21. Evidence completeness tests — every created run is finalized, `final_status` is derived from
    recorded errors rather than fixed, and the manifest and checksums cover every artifact (§2.1.1)
22. Metadata synchronization check — `validate_ai_contract` passes and no lock is stale (§32.1)
23. Plugin tests — entry point, manifest, import safety, provider lifecycle (RFDS-015 §8)
24. Structure validation — `validate_structure.py` passes, including packaged-resource parity
    (§37.1) and all three §9.2 drift checks: reference→map, map→`public_api.yaml`, and
    guides→`public_api.yaml`, plus capability-group completeness
25. Performance tests
26. Soak/stability tests

---

## 30. Hardware-in-the-Loop Matrix

Qualification shall be recorded by mainframe, transport, and module.

### 30.1 Mainframes

```text
34970A
34972A
```

### 30.2 Transports

```text
34970A GPIB
34970A RS-232
34972A LAN / VISA
34972A USB / VISA
```

### 30.3 Modules

```text
34901A
34902A
34903A
34904A
34905A
34906A
34907A
34908A
```

### 30.4 Internal DMM dimension

Because v1.1 made internal-DMM availability a first-class capability gate (§4.4), a switch-only
frame is a distinct qualification target rather than a degraded case of a measuring one:

```text
DMM present
DMM absent / disabled
```

The DMM-absent configuration shall be qualified at least on the simulator, verifying that every
DMM-dependent keyword raises `DriverUnsupportedOperationError` locally and that switching, digital
I/O, totalizer, and DAC capabilities remain available.

Each combination shall carry an explicit status:

```text
NOT_TESTED
SIMULATOR_TESTED
HARDWARE_TESTED
EXCLUDED
NOT_APPLICABLE
```

No unsupported HIL combination shall be silently represented as validated.

---

## 31. Examples

Fifteen runnable examples are required — the full set listed below. Ten is the RFDS floor; this
driver's acceptance target is the complete list, so the check is unambiguous.

Planned examples:

`examples/connection/` is additionally mandated by RFDS-004 §6 and shall hold one runnable
connection example per supported transport.

```text
01_identity_and_modules.robot
02_dc_voltage_measurement.robot
03_resistance_2wire.robot
04_resistance_4wire.robot
05_temperature_thermocouple.robot
06_temperature_rtd.robot
07_scan_multiple_channels.robot
08_triggered_scan.robot
09_buffered_readings.robot
10_statistics.robot
11_switch_control.robot
12_34907a_digital_io.robot
13_34907a_totalizer.robot
14_34907a_dac.robot
15_configuration_and_diagnostics.robot
```

Every example shall support a simulator profile.

Hardware examples shall require explicit connection configuration.

No example shall contain hard-coded personal addresses, IPs, COM ports, or credentials.

---

## 32. Scripts

The package shall include scripts for Windows and Linux where practical.

Planned scripts:

The set below is mandated by RFDS-005 §6. Earlier revisions of this plan renamed some entries and
omitted others; the RFDS-005 names are authoritative.

```text
scripts/
├── setup_venv.bat
├── setup_venv.ps1
├── setup_venv.sh
├── run_example.bat
├── run_example.ps1
├── run_example.sh
├── run_all_examples.bat
├── run_all_examples.ps1
├── run_all_examples.sh
├── run_tests.bat
├── run_tests.ps1
├── run_tests.sh
├── run_hil_tests.bat
├── run_hil_tests.ps1
├── run_hil_tests.sh
├── run_call_protocol_conformance.bat
├── run_call_protocol_conformance.ps1
├── run_call_protocol_conformance.sh
├── generate_libdoc.bat
├── generate_libdoc.ps1
├── generate_libdoc.sh
├── validate_structure.py
├── validate_ai_contract.py
├── validate_call_protocol_conformance.py
├── compare_public_api.py
└── build_release.py
```

Device-specific additions are permitted, but no mandated script shall be renamed or omitted.

### 32.1 Synchronization tooling is mandatory

§25 requires the AI contract, capability model, public API inventory, and RFDS-019 protocol vectors
to remain synchronized, and §37 provides `ai/ai_contract.lock` and `config/schema.lock`. A
synchronization requirement with no tooling to enforce it drifts silently.

- `generate_metadata` shall regenerate the public API inventory, AI contract, capability model,
  keyword inventory, and generated documentation from the implementation, so they cannot be
  hand-edited out of agreement.
- `validate_ai_contract` shall verify the contract against the implementation and verify the lock
  hash, and shall **fail** on mismatch.

Adding, renaming, or removing a public keyword shall fail the verification sequence until the
metadata is regenerated. A stale lock is a release-blocking failure (§53).

---

## 33. Documentation

The package shall include current documentation for every release.

### 33.1 README

`README.md` shall include:

- supported instruments;
- supported modules;
- installation;
- quick start;
- connection examples;
- simulator usage;
- Robot Framework usage;
- limitations;
- safety notes;
- conformance status;
- HIL status;
- links to detailed documentation.

### 33.2 GitHub Pages

GitHub Pages shall be updated for every driver revision.

Planned documentation:

RFDS-005 §6 mandates the first block; the second is device-specific and additional.

```text
docs/
├── index.md                          # RFDS-005 mandated
├── installation.md                   # RFDS-005 mandated
├── quick_start.md                    # RFDS-005 mandated
├── keywords.md                       # RFDS-005 mandated
├── architecture.md                   # RFDS-005 mandated
├── configuration.md                  # RFDS-005 mandated
├── compatibility.md                  # RFDS-005 mandated
├── migration.md                      # RFDS-005 mandated
├── support_policy.md                 # RFDS-005 mandated
├── examples.md                       # RFDS-005 mandated
├── safety.md                         # RFDS-005 mandated
├── call_protocol_conformance.md      # RFDS-005 mandated
├── hardware_validation.md            # RFDS-005 mandated
├── troubleshooting.md                # RFDS-005 mandated
├── release_notes.md                  # RFDS-005 mandated
│
├── plugin_integration.md             # RFDS-015 §8 mandated
│
├── capability_model.md               # device-specific (RFDS-013)
├── modules.md                        # device-specific
├── measurements.md                   # device-specific
├── scanning.md                       # device-specific
├── switching.md                      # device-specific
├── 34907a.md                         # device-specific
└── simulator.md                      # device-specific
```

---

## 34. PyCharm and Robot Framework Guide

Required guide folder:

```text
guide/
├── pycharm_robot_framework_setup.md
├── windows_setup.md
├── linux_setup.md
├── hardware_setup.md
├── transport_setup.md            # RFDS-004 §6 mandated
├── configuration_profiles.md
└── troubleshooting.md
```

The PyCharm guide shall include:

- Python interpreter setup;
- virtual environment creation;
- package installation;
- Robot Framework installation;
- Robot Framework language support;
- library import configuration;
- project source root;
- running Robot tests;
- debugging Python driver code;
- selecting simulator profiles;
- selecting real hardware profiles.

---

## 35. History Folder

Required:

```text
history/
```

Each meaningful driver change shall have a traceable history record.

Recommended naming:

RFDS-005 §6 requires `history/README.md` and `history/v<version>.md`, with `<version>` in the
RFDS-011 forms (§3.2):

```text
history/
├── README.md
├── v26.01.01.md      Phase 1, Gate 1
├── v26.01.02.md      Phase 1, Gate 2
├── v26.01.03.md      Phase 1, Gate 3
├── v26.01.04.md      Phase 1, Gate 4
├── v26.01.05.md      Phase 1, Gate 5
└── v26.01.md         public release
```

Each history record shall include:

```text
date
version
gate
changed requirements
changed files
new capabilities
changed capabilities
bug fixes
known limitations
tests executed
evidence references
```

---

## 36. Review Folder

Required:

```text
review/
```

Each major gate shall have a code/release review.

Recommended files:

RFDS-005 §6 mandates version-prefixed review artifacts, not gate-prefixed ones:

```text
review/
├── README.md
├── v<version>_code_review.md
├── v<version>_architecture_review.md
├── v<version>_robot_api_review.md
├── v<version>_documentation_review.md
├── v<version>_conformance_review.md
├── v<version>_security_review.md
├── v<version>_compatibility_review.md
├── v<version>_release_readiness.md
├── requirement_traceability.md
├── known_risks.md
└── evidence/
    └── v<version>/
```

`<version>` follows RFDS-011 (§3.2): `v26.01` for a public release, `v26.01.03` for an engineering
gate. A driver-specific `safety_review.md` may be added given this driver's hazard profile, but not
in place of any mandated artifact.

Review shall use RFDS-010 as the minimum checklist, and shall adopt its normative machinery rather
than only its topics:

- **required inputs and outputs** per RFDS-010 §7 and §8;
- **finding severities** per RFDS-010 §9 — `CRITICAL`, `MAJOR`, `MINOR` only. Any open Critical
  finding blocks every production or conditional-production verdict (§9.1). A Major finding normally
  blocks production release and may be waived only under RFDS-010 §22;
- **checklist item statuses** per RFDS-010 §10;
- **review occasions** per RFDS-010 §5 and reviewer independence per §6.

The severity definitions are directly applicable to this driver: RFDS-010 §9.1 classifies "failure
to reach the declared safe state", "uncontrolled … relay topology", and "false PASS" as Critical —
which is what §21's ownership model, §15.2's switching topology rules, and §2.1.1's derived
`final_status` exist to prevent.

---

## 37. Planned Package Structure

```text
rf_keysight349xx/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── AGENTS.md
├── pyproject.toml
├── mkdocs.yml
│
├── rf_keysight349xx/
│   ├── __init__.py
│   ├── library.py
│   ├── version.py
│   ├── plugin.py
│   ├── sessions.py
│   ├── converters.py
│   ├── capabilities.py
│   ├── configuration.py
│   ├── diagnostics.py
│   ├── evidence.py
│   ├── exceptions.py
│   ├── models.py
│   ├── py.typed
│   ├── resources/
│   │   ├── plugin_manifest.json            # RFDS-015 §8
│   │   └── configuration/                  # RFDS-014 §6
│   │       ├── schema.json
│   │       ├── schema.lock
│   │       └── default.json
│   │
│   ├── core/
│   │   ├── instrument.py
│   │   ├── measurement.py
│   │   ├── scanner.py
│   │   ├── switching.py
│   │   ├── temperature.py
│   │   ├── digital_io.py
│   │   ├── totalizer.py
│   │   ├── dac.py
│   │   ├── alarms.py
│   │   └── scaling.py
│   │
│   ├── protocol/
│   │   ├── scpi.py
│   │   ├── parsers.py
│   │   ├── commands.py
│   │   └── vendor_command_coverage.yaml
│   │
│   └── transport/                          # RFDS-004 §6 -- singular
│       ├── __init__.py
│       ├── base.py
│       ├── config.py
│       ├── errors.py
│       ├── models.py
│       ├── codec.py
│       ├── tracing.py
│       └── backends/
│           ├── __init__.py
│           ├── visa.py
│           ├── serial.py
│           ├── tcp.py
│           └── simulator.py
│
├── api/
│   ├── public_api.yaml
│   ├── unknowns.yaml
│   └── deviations.yaml
│
├── config/
│   ├── schema.json
│   ├── schema.lock
│   ├── default.json
│   ├── example.json
│   ├── hil_resources.example.yaml
│   ├── profiles/
│   │   ├── simulator.json
│   │   ├── 34970a_gpib.json
│   │   ├── 34970a_rs232.json
│   │   ├── 34972a_lan.json
│   │   └── 34972a_usb.json
│   └── migrations/
│       └── README.md
│
├── ai/
│   ├── ai_contract.yaml
│   ├── ai_contract.lock
│   └── system_ai_contract.template.yaml
│
├── capability/
│   ├── capability_model.yaml
│   ├── capability_model.schema.json
│   └── examples/
│       ├── capability_snapshot.json
│       └── capability_query_examples.robot
│
├── robot_resources/
│   ├── common.resource
│   └── variables.example.yaml
│
├── generated/
│   ├── libdoc/
│   └── api_manifest/
│
├── tests/
│   ├── unit/
│   ├── protocol/
│   ├── transport/
│   ├── integration/
│   ├── robot/
│   ├── simulator/
│   ├── replay/
│   ├── conformance/
│   ├── capability/
│   │   ├── capability_model_validation.robot
│   │   ├── capability_binding_validation.robot
│   │   └── capability_runtime_discovery.robot
│   ├── regression/
│   ├── compatibility/
│   ├── hil/
│   ├── performance/
│   ├── soak/
│   ├── plugin/                             # RFDS-015 §8
│   │   ├── test_entry_point.py
│   │   ├── test_manifest.py
│   │   ├── test_import_safety.py
│   │   └── test_provider_lifecycle.py
│   ├── support/
│   └── data/
│       └── configuration/                  # RFDS-014 §6
│
├── examples/
│   ├── index.yaml
│   ├── README.md
│   └── *.robot
│
├── scripts/
│   ├── *.ps1
│   └── *.sh
│
├── guide/
│   └── *.md
│
├── docs/
│   └── *.md
│
├── history/
├── review/
│
├── dist/
│
├── results/
│   └── .gitkeep                            # RFDS-009 §7; runtime evidence root per RFDS-008 §11
│
└── release/
    ├── release_manifest.json
    ├── rfds_revisions.yaml
    ├── decisions.yaml
    ├── open_questions.yaml
    ├── requirements_traceability.csv
    ├── compatibility_report.json
    ├── validation_report.json
    ├── sbom.spdx.json
    └── checksums.sha256
```

### 37.1 Layout requirements

The package uses a **flat package root** — `rf_keysight349xx/rf_keysight349xx/` — not a `src/`
layout. This matches every driver already in the project repository; introducing a `src/` layout
here would make this driver the only one of its kind and would require bespoke handling in the
structural validators, which assert a fixed package root.

Adopting `src/` would be a repository-wide decision requiring an approved deviation. It shall not be
introduced by a single driver.

`evidence.py` implements the RFDS-008 evidence engine described in §2.1.1. It is a mandatory module,
not an optional add-on: §28 conformance acceptance depends on the artifacts it writes.

**Transport module tree.** `transport/` is singular and follows RFDS-004 §6, including the
`backends/` layer. Only supported backends are present — RFDS-004 §6 permits omitting unsupported
backends but states they "shall not be present as non-functional placeholders". `usb.py` is omitted
pending the 34972A USB transport decision (§30); if that transport is qualified, the backend is
added then, not stubbed now.

The `src/` question raised by RFDS-004 §6's own tree is resolved by the recorded interpretation note
in §2.3, per RFDS-001 §7.2 and RFDS-001-GOV-004.

**Packaged runtime resources.** `resources/plugin_manifest.json` and `resources/configuration/`
exist because the repository-level `config/` and manifest are not installed with the wheel. The
packaged copies shall be kept byte-identical to their repository counterparts by
`generate_metadata`, and a divergence shall fail `validate_structure.py`.

**`results/`** is the runtime evidence root (RFDS-009 §7) and shall never hold source-controlled
content (RFDS-008 §11).

---

## 38. Implementation Lifecycle

The project shall use 12 implementation phases.

Each phase contains five gates:

```text
Gate 1 — Architecture & Skeleton
Gate 2 — Core Implementation
Gate 3 — Extended Features
Gate 4 — Tests & Documentation
Gate 5 — Review & Release
```

---

## 39. Phase 1 — Requirements, Contracts, Architecture, Skeleton

### Gate 1

- Freeze authoritative source set.
- Create requirement traceability matrix.
- Create package skeleton.
- Define driver identity.
- Define public API inventory.
- Define initial capability inventory.
- Define AI contract skeleton.
- Define protocol vector schema.
- Define vendor command coverage inventory.
- Record all unresolved behavior as `UNKNOWN`.

### Gate 2

- Implement base library structure.
- Integrate `rfds-core` `BaseInstrumentLibrary`; declare the pinned dependency range (§5.3).
- Implement RFDS transport interfaces.
- Implement simulator transport skeleton.
- Implement normalized exceptions.
- Implement timeout framework.
- Implement session state model.

### Gate 3

- Add transport observation hooks.
- Add configuration schema framework.
- Add capability model framework, including the internal-DMM gate (§4.4).
- Add plugin provider skeleton.
- Add ownership model.
- Add logging/evidence infrastructure implementing RFDS-008 (§2.1.1): run directory layout,
  operation records, error records, protocol exchange capture, run finalization, and manifest plus
  checksum generation.

### Gate 4

- Unit-test base state machine.
- Test zero-I/O import/construction.
- Test timeout behavior.
- Test partial-connect cleanup.
- Test evidence-run completeness: every created run is finalized, including runs whose session was
  never opened, and `final_status` reflects recorded errors rather than a fixed value.
- Create initial documentation.
- Create initial PyCharm setup guide.

### Gate 5

- Architecture review.
- API review.
- safety model review.
- RFDS requirement review.
- Generate Gate-1 phase package.

---

## 40. Phase 2 — Connection, Identity, Modules, System, Errors

### Gate 1

- Define protocol vectors for connection.
- Define identity parser.
- Define module discovery behavior.
- Define system/error API.

### Gate 2

- Implement connect/disconnect.
- Implement `*IDN?`.
- Implement module discovery.
- Implement communication probe.
- Implement SCPI version.
- Implement error queue.

### Gate 3

- Add 34970A/34972A model branching.
- Add connection-error recovery.
- Add malformed `SYST:ERR?` handling.
- Add self-test and status behavior.

### Gate 4

- Robot tests.
- simulator tests.
- RFDS-019 vectors.
- documentation.
- examples.

### Gate 5

- Code review.
- protocol review.
- conformance review.
- package review.
- gate ZIP.

---

## 41. Phase 3 — Measurement Engine

Implement:

- DC voltage;
- AC voltage;
- DC current;
- AC current;
- 2-wire resistance;
- 4-wire resistance;
- frequency;
- period;
- applicable measurement configuration.

Each measurement keyword shall receive:

- public API definition;
- AI contract entry;
- protocol vector;
- unit test;
- simulator behavior;
- Robot test;
- documentation;
- example;
- RFDS-019 evidence.

---

## 42. Phase 4 — Scan, Trigger, Acquisition, Memory, Statistics

Implement:

- scan list;
- trigger source;
- trigger count;
- trigger timer;
- initiate;
- abort;
- read;
- fetch;
- buffered read;
- reading count;
- reading memory;
- statistics;
- min/max timestamps.

Special attention shall be given to differing memory semantics of `READ?`, `FETCh?`, `R?`, and `DATA:REMove?`.

---

## 43. Phase 5 — Temperature

Implement:

- thermocouple;
- RTD;
- thermistor;
- temperature units;
- four-wire pairing;
- module restrictions;
- sensor-specific configuration.

The simulator shall reproduce valid and invalid sensor/module combinations.

---

## 44. Phase 6 — Switching and Routing

Implement:

- channel enumeration;
- open;
- close;
- multi-channel operations;
- switch-state query;
- ownership;
- safe-state behavior.

Switching commands shall use conservative retry semantics.

---

## 45. Phase 7 — 34907A Digital I/O, Totalizer, DAC

Implement:

- digital byte/word input;
- digital byte/word output;
- direction state;
- totalizer;
- DAC output;
- DAC readback;
- ownership;
- safety;
- fault recovery.

This phase requires explicit high-risk protocol vectors for state-changing functions.

---

## 46. Phase 8 — Alarms, Scaling, Status, Diagnostics

Implement:

- alarm limits;
- alarm enable/disable;
- alarm state;
- digital compare/mask;
- scaling;
- supported status queries;
- safe diagnostics.

Service-only operations remain excluded.

---

## 47. Phase 9 — 34972A-Specific Functions

Implement only functions established by authoritative 34972A documentation.

Expected areas:

- LAN configuration/status;
- hostname;
- DHCP;
- network parameters;
- USB storage catalog;
- file/memory operations;
- logging.

Model gating shall be mandatory.

---

## 48. Phase 10 — Configuration, Safety, Recovery, Plugin, AI/GUI Integration

Complete:

- RFDS-014 configuration API;
- configuration profiles;
- safe shutdown;
- ownership reconciliation;
- retry policy;
- session recovery;
- plugin architecture;
- final AI contract;
- capability model;
- GUI integration metadata.

---

## 49. Phase 11 — Full Verification and Documentation

Complete:

- RFDS-019;
- regression suite;
- compatibility suite;
- replay tests;
- clean-wheel test;
- simulator qualification;
- real HIL;
- module HIL;
- examples;
- README;
- GitHub Pages;
- guide;
- traceability;
- review evidence.

---

## 50. Phase 12 — Production Qualification

Complete:

- performance;
- concurrency;
- soak;
- stability;
- security review;
- safety review;
- package review;
- SBOM;
- checksums;
- release manifest;
- final production-readiness review.

No production claim shall be made while mandatory acceptance evidence remains `NOT_RUN`.

---

### 50.1 Supply-chain and security evidence (RFDS-001-SEC)

**RFDS-001-SEC-002** — a P1 or B1 release shall identify:

```yaml
direct_runtime_dependencies:   # name + exact version range
  - rfds-core>=1.0,<2.0        # §5.3
  - <VISA runtime, if the VISA backend is shipped>
development_test_dependencies: # name + version
licences:                      # per dependency, including transitive where material
vendored_source_or_binaries:   # none expected; see SEC-003
required_external_sdks:        # e.g. a vendor VISA installer, with install provenance
vulnerability_review_status:   # tool, date, findings, disposition
unresolved_supply_chain_risks: # explicit, or "none"
```

**RFDS-001-SEC-003** — two prohibitions:

- a release **shall not contain undocumented binary dependencies or executables**;
- security controls **shall not be represented as product or electrical safety certification**. The
  §21 safety model concerns instrument and bench safety; it makes no certification claim.

This is more than paperwork here: the driver takes a hard dependency on `rfds-core` (§5.3) and may
require a vendor VISA runtime, which SEC-002 requires declaring with its licence and provenance.
`release/sbom.spdx.json` (§37) carries the machine-readable form; the fields above are the required
content, not merely the file's existence.

---

## 51. Release Maturity Progression

Recommended progression:

```text
D0
architecture / incomplete development
     ↓
D1
complete simulator + RFDS-019 validation
     ↓
D2
representative real hardware validated
     ↓
P1
full production acceptance
```

**RFDS-001-CLS-001** requires every packaged revision to declare exactly one release class from
`D0`, `D1`, `D2`, `P1`, `B1`. The declaration shall appear in the release manifest, and §53's
acceptance criteria shall be evaluated against the RFDS-001 §8.2 applicability matrix **for the
declared class** — that matrix is what selects which requirements are mandatory, so without a
declared class nothing selects them.

`B1` (integrated bench) is not a target for this driver in isolation; it applies to a bench release
that includes it, governed by the RFDS-018 contract in §26.

The first substantial target should be:

```text
rf_keysight349xx_v26.01 — D1
```

Promotion beyond D1 requires real hardware evidence.

---

## 52. Requirement Traceability

Create:

```text
release/requirements_traceability.csv
```

Recommended fields:

```text
requirement_id
source_document
source_section
requirement_summary
implementation_artifact
test_artifact
evidence_artifact
status
deviation_id
notes
```

**RFDS-001-CLS-003** fixes the allowed dispositions as a closed set of four. Earlier revisions of
this plan listed eight; `IMPLEMENTED`, `UNKNOWN`, and `EXCLUDED` were invented and are withdrawn —
`IMPLEMENTED` in particular reads as success while asserting nothing about verification, which is
the exact gap `PASS` versus `NOT_RUN` exists to expose.

```yaml
PASS:            verified
FAIL:            verified as not meeting the requirement
NOT_APPLICABLE:  requires a recorded rationale
DEVIATION:       requires an approved deviation identifier
```

`NOT_RUN` may be tracked as a working state during implementation but **shall not satisfy release
acceptance** (RFDS-001-CLS-003) and shall not appear as a final disposition.

No mandatory requirement shall disappear from traceability.

**Seeded requirement set (A6).** `release/requirements_traceability.csv` is seeded with **all 132
RFDS-001 numbered requirements**, each carrying a disposition. Before v1.10 the plan cited only four
of them, all added reactively when a review happened to hit one — so a gap in an area the plan had
never visited had no mechanism that would surface it. That is precisely how findings A1–A5 went
unnoticed through nine passes.

Seeding is the control, not the paperwork: an unaddressed requirement is now a visible `NOT_RUN` row
rather than an absence. RFDS-001-CLS-002's applicability matrix also becomes usable, since it keys
mandatory requirements off the declared release class and cannot be applied to a set that was never
enumerated.

The other 18 guides carry roughly 3,195 unnumbered `shall` statements and cannot be seeded by
identifier. They shall be traced by document and section per §52's `source_document` /
`source_section` fields.

The release shall additionally record the exact revision of every RFDS specification used for
validation (RFDS-001-GOV-003), emitted to `release/rfds_revisions.yaml`. A newer subordinate
specification shall not be assumed retroactively unless the release is revalidated against it. This
record is a §53 release-blocking check: the baseline drift corrected in v1.3 went unnoticed across
three revisions precisely because no machine-checkable record existed.

---

## 53. Definition of Done

**RFDS-001-ACC-001 governs P1 acceptance.** The criteria below incorporate it rather than
paraphrasing it; where this list and RFDS-001-ACC-001 differ, ACC-001 governs (RFDS-001 §7.1).

ACC-001's enumerated criteria, each mapped to where this plan satisfies it:

| RFDS-001-ACC-001 criterion | This plan |
|---|---|
| release ZIP name and stable internal root pass automated validation | §3.2, `validate_structure.py` (§32) |
| `release_manifest` exists and matches package contents | §37, §50 |
| all mandatory package paths and artifacts exist | §37, §37.1 |
| library imports and **Libdoc generation succeeds** | §32 `generate_libdoc`, §29.1 |
| 100% of exported public keywords covered | §28.2, §9.2 |

`RFDS-001-ACC-002` (B1 bench acceptance) is dispositioned `NOT_APPLICABLE` for this driver in
isolation — it governs a bench release that includes this driver, per §26 — with the rationale
recorded in `release/requirements_traceability.csv`.


The driver is ready for production review only when all of the following are true:

- package structure conforms to RFDS;
- all mandatory universal keywords exist;
- applicable conditional keyword groups are complete;
- all exported keywords are in RFDS-019 inventory;
- every device-facing keyword has a protocol vector or approved exclusion;
- protocol transmission is verified;
- response parsing is verified;
- malformed responses are tested;
- timeout behavior is tested;
- recovery behavior is tested;
- configuration API is complete;
- AI contract is synchronized;
- capability model is synchronized;
- safe shutdown is ownership-aware;
- simulator suite passes;
- real-device evidence exists for claimed hardware support;
- examples are runnable;
- all fifteen examples listed in §31 exist and are runnable;
- README is current;
- GitHub Pages are current;
- setup guides are current;
- history is current;
- code reviews are present;
- release manifest is generated;
- SBOM is generated;
- checksums are generated;
- clean installation test passes;
- raw protocol I/O is gated and disabled by default (§8.1);
- no destructive read is retry-eligible (§22.3);
- reconciliation is a bounded poll with configurable timeout (§22.2);
- safe shutdown reports per-action outcomes and never claims an unachieved safe state (§21.2);
- every simulator-modelled resource matches the capability model (§27.2);
- the AI contract lock is current and `validate_ai_contract` passes (§32.1);
- every `SOURCE_VERIFICATION_REQUIRED` item is resolved against the command reference;
- every vendor command carries a disposition and every `PUBLIC` command is bound to a keyword (§20);
- `api/public_api.yaml` is the union of the device-facing map and the mandatory driver-level
  keywords, and every mandatory RFDS-002 §8/§9, RFDS-013 §7.1 and RFDS-014 keyword is present (§9.2);
- every `PUBLIC` command binds to a keyword, and every declared capability group is complete (§9.2);
- every RFDS citation names a version held in `AI_Guides/` (§2.1), and the revision set is emitted
  to `release/rfds_revisions.yaml` (§52);
- the packaged revision declares exactly one RFDS-001 release class, and acceptance is evaluated
  against the RFDS-001 §8.2 matrix for that class (§51);
- `rfds-core` is declared with a pinned range and its effective version is recorded in driver
  information, diagnostics, and `software_inventory.json` (§5.3);
- the RFDS-007 §6 exception hierarchy is implemented and every raised exception carries an
  RFDS-007 §8 code (§2.4);
- the transport tree matches RFDS-004 §6 with no placeholder backends (§37.1);
- packaged `resources/configuration/` and `resources/plugin_manifest.json` match their repository
  counterparts (§37.1);
- no traceability entry remains `NOT_RUN` (§52);
- all six RFDS-013 capability discovery keywords are implemented (§7.2);
- release identity conforms to RFDS-011 §5 and §6 (§3.2, §3.3);
- the package layout matches RFDS-005 §6 with no renamed or omitted mandatory path (§37);
- `ai_contract.yaml` identity `plugin_id` equals the RFDS-015 manifest `plugin_id` (§25);
- no mandatory release criterion remains `NOT_RUN`.

---

## 54. Initial Open Questions

Resolved against the Command Reference in v1.5 — see `reference/SOURCE_VERIFICATION.md`:

```yaml
OQ-3  continuity supported:          NOT_APPLICABLE  # no such function
OQ-4  diode supported:               NOT_APPLICABLE  # no such function
OQ-11 monitor mode:                  PUBLIC          # ROUTe:MONitor group
OQ-12 card topology / channels:      RESOLVED        # §11.3, §14.1, §15.2
OQ-13 DAC output range:              RESOLVED        # -12 V to +12 V, 0.001 V
OQ-15 Preset Device side effect:     RESOLVED        # identical to *RST
B4    Get Digital Direction:         NOT_APPLICABLE  # no queryable command
B3    internal DMM discovery:        RESOLVED        # INSTrument:DMM?
```

The following remain explicit. None is answerable from the device source — each is a deployment fact
or a project policy decision:

1. Exact final public keyword naming for every device-specific function (public API contract, §9).
2. **OQ-5** — which calibration/service queries, if any, become read-only public diagnostics.
   `CALibration?` exists; exposure is a project call, not a device fact.
3. Relay-cycle-counter *read* exposure (§19).
4. Exact safe states for deployment-specific relay, digital-output, and DAC resources — a bench
   contract input (§26), not a device property.
5. **OQ-8** — which real hardware combinations are available for HIL (§30).
6. **OQ-9** — which firmware revisions require compatibility exceptions.
7. **OQ-14** — whether concurrent scan operations from different sessions are permitted or refused
   (§5.2). The contention set is now identified: scan engine, reading memory, and the internal DMM,
   with monitor mode contending for the DMM as well. The policy remains a driver decision.
8. Whether any module-specific timing restrictions require additional stabilization parameters.

These questions shall not be silently resolved by assumptions.

### 54.1 Deviation control (RFDS-001-DEV)

**RFDS-001-DEV-001** fixes the record every deviation shall carry:

```yaml
deviation_id:     DEV-2026-001
requirement_id:   RFDS-001-TEST-004
severity:         Major
reason:           Real hardware unavailable
risk:             Protocol verified only using the simulator
scope:            Release v26.01
owner:            Driver maintainer
approved_by:      Release authority
approval_date:    2026-07-26
expiry:           2026-12-31
```

**RFDS-001-DEV-002** constraints, all release-blocking:

- a **Critical** finding shall not be waived for a P1 or B1 release;
- **Major** deviations shall be exceptional, scoped, and **time-limited**;
- an **expired deviation shall fail release acceptance**;
- a deviation shall **not silently transfer** to a newer release — it is re-approved or it lapses;
- the release manifest shall list **all active deviation identifiers**.

Deviations live in `api/deviations.yaml` and are referenced by `deviation_id` from
`release/requirements_traceability.csv` (§52) and from `release/release_manifest.json`.

**Deviations this plan already contemplates.** Both were recorded before this schema existed and are
incomplete until they carry it:

| Candidate | Origin | Status |
|---|---|---|
| RFDS-004 §6 `src/` layout vs RFDS-005 §6.1 | §2.3 interpretation note | Recorded as an interpretation note, not a deviation; needs `owner`, `approved_by`, `approval_date`. An interpretation note under RFDS-001-GOV-004 is a valid alternative to a deviation, but the approval fields are required either way |
| `Reset Device` confirmation argument | §9.1 fallback option | Not exercised — the canonical RFDS-002 §9.8 signature is used. If ever adopted it requires a full DEV-001 record |

---

## 55. Implementation Principle

The driver shall be built source-first and evidence-first:

```text
RFDS requirement
      ↓
device source
      ↓
public capability
      ↓
AI contract
      ↓
protocol vector
      ↓
implementation
      ↓
simulator / unit test
      ↓
Robot Framework test
      ↓
RFDS-019 evidence
      ↓
real hardware evidence
      ↓
release review
```

This traceability chain is the central acceptance model for the project.

It governs revision as much as authorship. Revisions v1.1 and v1.2 of this plan were produced by
reasoning from repository observation rather than from the RFDS documents themselves, and each
introduced defects the standards had already ruled on — an invented evidence-standard title, raw-I/O
keyword names that ignored the canonical set, a confirmation argument bolted onto a canonical
signature, and a configuration setting duplicating a canonical argument. A plausible answer derived
from precedent is not a sourced answer. Every change to this document shall cite the RFDS section or
device-source passage that justifies it.
