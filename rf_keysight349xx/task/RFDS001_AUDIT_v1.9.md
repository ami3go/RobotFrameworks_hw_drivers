# RFDS-001 Requirement Audit — Spec v1.9

**Audited:** `RF_Keysight349xx_Driver_Implementation_Plan_v1.9.md`
**Against:** `AI_Guides/RFDS-001_Platform_Requirements_v1.1.md` — **132 numbered requirements**
**Audit date:** 2026-08-18
**Method:** RFDS-001 is the only guide carrying stable requirement identifiers
(`RFDS-001-<AREA>-<NNN>`). All 132 were extracted mechanically, grouped by area, screened for topic
coverage, and the high-risk subset was then read in full and checked against the spec.
**Scope:** specification only — no implementation exists.

> **Why this is an audit and not a review.** Previous passes asked "is the spec good?". This one
> asks a checkable question per requirement: *is RFDS-001-XXX-NNN satisfied, and by what?* The
> other 18 guides carry ~3,195 unnumbered `shall` statements and cannot be audited this way; they
> were covered by `CYCLING_REVIEW_v1.3.md`.

---

## 1. Result

| Disposition | Count |
|---|---:|
| Addressed | ~120 |
| **Not addressed — findings below** | **10** |
| Arguably not applicable, but undeclared | 2 |

**No critical findings.** Six major gaps, all in areas the plan has never touched rather than areas
it got wrong — release governance, performance, supply chain, and resource declaration.

**One systemic finding (A6) underlies the rest:** the plan cites **4 of 132** RFDS-001 requirement
IDs. Nothing binds the requirement set into §52's traceability matrix, so a gap in an untouched area
has no mechanism that would surface it. This audit is the first thing to look.

---

## 2. Major findings

### A1 — No deviation schema, and no deviation constraints

**RFDS-001-DEV-001** requires every deviation to record: `deviation_id`, `requirement_id`,
`severity`, `reason`, `risk`, `scope`, `owner`, `approved_by`, `approval_date`, `expiry`.

**RFDS-001-DEV-002** adds constraints that are release-blocking in nature:

- Critical findings **shall not** be waived for P1 or B1;
- Major deviations shall be exceptional, scoped, and **time-limited**;
- an **expired deviation shall fail release acceptance**;
- a deviation shall not silently transfer to a newer release;
- the release manifest **shall list all active deviation identifiers**.

The plan references `api/deviations.yaml` in §2.3 (the recorded RFDS-004/005 conflict) and §9.1 (the
`Reset Device` fallback), and §52 has a bare `deviation_id` column. **No schema, and none of the five
constraints, appear anywhere.** The single `expiry` occurrence in v1.9 is unrelated — it refers to a
§22 timeout deadline.

This matters here specifically: the plan already contemplates two deviations, and §2.3's
interpretation note has no owner, approval, or expiry recorded.

### A2 — No device-specific performance contract

**RFDS-001-PERF-001** requires the driver to document, where applicable: expected connection time,
normal keyword latency, stabilization delay, maximum operation timeout, retry count and backoff,
acquisition throughput, polling interval, cancellation latency, concurrency limitations, and known
slow operations.

**None of these ten appears in v1.9.** Searched: `keyword latency`, `stabilization delay`,
`acquisition throughput`, `cancellation latency` — zero occurrences each.

The omission is conspicuous because §25 requires *per-keyword* `timing`, `timeout`, and
`stabilization` fields in the AI contract, and RFDS-018 §6.9 requires bench scheduling to be
"consistent with each driver's RFDS-017 `stabilization_delay` values". The per-keyword obligation is
recorded; the driver-level contract those values roll up into is not.

Relevant device facts are already known and unrecorded: scan throughput, relay settling time (which
§22.2's bounded-poll reconciliation depends on), and monitor-mode polling interval.

### A3 — RFDS-001-ACC-001's P1 acceptance criteria are not adopted

**RFDS-001-ACC-001** enumerates specific numbered criteria a P1 driver shall satisfy — automated
validation of ZIP name and internal root, `release_manifest.yaml` matching package contents, all
mandatory paths present, library import and **Libdoc generation** succeeding, 100% of exported public
keywords covered, and more.

§53's Definition of Done is the plan's own list. It overlaps substantially but is not derived from
ACC-001 and never cites it, so there is no check that the two agree. `Libdoc` appears in v1.9 only
as a script name (§32), never as an acceptance criterion.

**RFDS-001-ACC-002** (B1 bench acceptance) is likewise uncited; it is plausibly out of scope for a
single driver, but that is a disposition the plan should state rather than omit.

### A4 — No resource declaration or access-mode model

**RFDS-001-RES-001** requires each driver *and* bench contract to identify relevant resources —
communication sessions, ports, addresses, USB devices, buses, SDK handles, power rails, channels,
fixtures, relays, measurement paths, DUT interfaces, and files requiring controlled access.

**RFDS-001-RES-002** requires each resource to declare an access mode.

§5.2 specifies *locking* and §26 delegates bench resources to the RFDS-018 contract, but the plan has
no driver-level resource inventory and no per-resource access mode. RES-001 explicitly applies to
both the driver and the bench contract, so delegating entirely to §26 does not discharge it.

**RFDS-001-RES-003** ("concurrency disabled by default when not proven safe") is *partially* met —
§5.2 requires explicit locking — but the plan never states a default concurrency posture, and OQ-14
leaves concurrent scanning undecided. The safe reading of RES-003 is that it must default to
disabled until proven, which the plan should say outright.

### A5 — Supply-chain evidence incomplete

**RFDS-001-SEC-002** requires P1/B1 releases to identify direct runtime dependencies and versions,
development and test dependencies, **licences**, vendored source or binaries, required external SDKs
and installers, **vulnerability-review status**, and unresolved supply-chain risks.

§50 lists SBOM and checksums; §37 has `release/sbom.spdx.json`. Absent: licences, vulnerability
review status, and unresolved supply-chain risks. Searched `vulnerab` — zero occurrences.

**RFDS-001-SEC-003** requires that a release contain no undocumented binary dependencies or
executables, and that security controls not be represented as product or electrical safety
certification. Neither statement appears. The only `provenance` hit is `integrity/provenance.json`
in the RFDS-008 evidence tree, which is a different artifact.

This has teeth for this driver: it depends on `rfds-core` (§5.3) and may use a VISA runtime, both of
which SEC-002 would require declaring.

### A6 — The requirement set is not bound into traceability (systemic)

**RFDS-001-REQ-003** requires each applicable mandatory requirement to be traceable through:

```text
Requirement → implementation → verification method → result → evidence → review decision
```

§52 defines a CSV with `requirement_id`, `source_document`, `source_section`, and the rest — the
right *shape*. But nothing enumerates which requirements apply, and **v1.9 cites only 4 of RFDS-001's
132 identifiers** (`CLS-001`, `CLS-003`, `GOV-003`, `GOV-004`) — all four added reactively when an
earlier review happened to hit them.

This is the mechanism-level cause of A1–A5. Each is a requirement in an area the plan simply never
visited, and with no requirement inventory there is nothing that would notice. RFDS-001-CLS-002's
applicability matrix compounds it: it keys mandatory requirements off the declared release class, so
without an enumerated set the matrix cannot be applied either.

**Fix:** seed `release/requirements_traceability.csv` with all 132 RFDS-001 identifiers and a
disposition each, before Gate 1. It is a mechanical step and it converts A1–A5 from "things nobody
looked for" into rows that are visibly `NOT_RUN`.

---

## 3. Undeclared non-applicability

**RFDS-001-VIS-001** (coherent driver ecosystem) and **RFDS-001-VIS-002** (platform priorities) are
the only requirements whose subject matter is absent from the spec entirely. Both are plausibly
platform-level rather than driver-level — but RFDS-001-CLS-003 requires *every* mandatory requirement
to carry a disposition, and `NOT_APPLICABLE` requires a recorded rationale. Silence is not a
disposition.

---

## 4. Verified as addressed

Spot-checked in full rather than assumed:

| Requirement | Where satisfied |
|---|---|
| `GOV-001` precedence | §2.3 records the RFDS-004/005 conflict and its basis in §7.2 |
| `GOV-004` conflict resolution | §2.3 — the interpretation note, added after `CYCLING_REVIEW` C004-2 |
| `CLS-001` release class | §51 requires a declared class per packaged revision |
| `CLS-003` dispositions | §52 reduced to the four permitted values; `NOT_RUN` barred from acceptance |
| `PKG-001/002/003` naming | §3.2 — `vYY.RR` and `vYY.PP.GG` per RFDS-011 |
| `SAFE-002/003` safe init/teardown | §21, §21.2 — ownership-aware, per-action outcomes |
| `IO-002` finite blocking | §5, §22 |
| `IO-008` protocol observation | §2.1.1 — RFDS-008 trace capture before connect |
| `ERR-001/002/003` | §2.4 — RFDS-007 hierarchy, codes, payload fields |
| `AI-001/002/003` | §25 — contract, synchronization, lock |
| `SIM-002` simulator boundary | §27, §27.2 |
| `CONF-001/002` RFDS-019 | §28 |
| `LIFE-001/002` phase and gate | §38, §39 |

---

## 5. Required actions

1. **A6 first** — seed `release/requirements_traceability.csv` with all 132 RFDS-001 identifiers and
   a disposition each. This is the control that makes the rest visible.
2. **A1** — add the RFDS-001-DEV-001 deviation schema and the five DEV-002 constraints; apply them
   to the two deviations the plan already contemplates.
3. **A2** — add a §-level performance contract covering PERF-001's ten fields.
4. **A4** — add a driver-level resource declaration with access modes; state the default concurrency
   posture explicitly.
5. **A5** — extend §50 to SEC-002's full evidence set and add SEC-003's two prohibitions.
6. **A3** — bind §53 to RFDS-001-ACC-001, and give ACC-002 an explicit disposition.
7. Give `VIS-001`/`VIS-002` a recorded `NOT_APPLICABLE` with rationale.

None requires new information.

---

## 6. Status

```text
Audited:               v1.9 against RFDS-001 v1.1 (132 numbered requirements)
Method:                mechanical extraction + full read of the high-risk subset
Implementation:        NOT STARTED — no code written
Critical:              0
Major:                 6  (A1-A6)
Undeclared N/A:        2  (VIS-001, VIS-002)
RFDS-001 IDs cited:    4 of 132
Other 18 guides:       ~3,195 unnumbered "shall" statements — not auditable by ID;
                       covered by CYCLING_REVIEW_v1.3.md
Recommended next step: v1.10 applying items 1-7
```
