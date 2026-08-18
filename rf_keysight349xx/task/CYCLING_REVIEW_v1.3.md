# Cycling Guide Review — Spec v1.3, one RFDS document at a time

> **STATUS: CLOSED — all findings resolved.** Cycle 1 (21 findings) and cycle 2 (RFDS-006, 010,
> 012, 018) were both applied in **v1.4**; see the v1.4 revision-history table for the
> finding-to-section mapping. **The current specification is
> `RF_Keysight349xx_Driver_Implementation_Plan_v1.4.md`.** All 19 RFDS guides have now been
> reviewed. Retained as the historical record — do not read the findings below as open.

**Reviewed document:** `RF_Keysight349xx_Driver_Implementation_Plan_v1.3.md`
**Method:** each RFDS guide in `AI_Guides/` taken in turn and checked against the spec in isolation
**Review date:** 2026-08-18
**Predecessors:** `SPEC_REVIEW.md` (v1.0), `DEEP_REVIEW_v1.1.md` (v1.1), `GUIDE_CONFORMANCE_REVIEW_v1.2.md` (v1.2)
**Scope:** specification only — no implementation exists, and none was written for this review.

Finding IDs are `C<guide>-<n>`, e.g. `C004-1` is the first finding against RFDS-004.

---

## Cycle status

| # | Guide | Reviewed | Findings |
|---|---|---|---|
| 001 | Platform Requirements v1.1 | ✅ | 3 |
| 002 | Mandatory Public API v1.0 | ✅ (prior cycle) | closed in v1.3 |
| 003 | BaseInstrumentLibrary v1.0 | ✅ | 3 |
| 004 | Transport Layer v1.0 | ✅ | 4 |
| 005 | Driver Package v1.3 | ✅ (prior cycle) | closed in v1.3 |
| 006 | Coding Standard v1.0 | ⬜ next cycle | — |
| 007 | Error and Exception v1.0 | ✅ | 3 |
| 008 | Logging and Evidence v1.0 | ✅ (prior cycle) | closed in v1.3 |
| 009 | Testing Standard v1.0 | ◐ partial (§7) | 2 |
| 010 | Driver Review Checklist v1.0 | ⬜ next cycle | — |
| 011 | Release Process v1.0 | ✅ (prior cycle) | closed in v1.3 |
| 012 | GUI Integration v1.0 | ⬜ next cycle | — |
| 013 | Capability Model v1.0 | ✅ (prior cycle) | closed in v1.3 |
| 014 | Configuration Model v1.0 | ◐ partial (§6) | 2 |
| 015 | Plugin Architecture v1.0 | ✅ (§7, §8) | 4 |
| 017 | AI Driver Contract v3.0 | ◐ partial | closed in v1.3 |
| 018 | AI Test Bench Contract v1.0 | ⬜ next cycle | — |
| 019 | Call and Protocol Conformance v1.1 | ◐ partial | — |
| 020 | Implementation Lifecycle v1.1 | ✅ (prior cycle) | closed in v1.3 |

**This cycle: 21 new findings across 7 guides.** Four guides and three partials remain.

---

## RFDS-001 — Platform Requirements v1.1

### C001-1 — §52 traceability status values exceed the permitted set (major)

**RFDS-001-CLS-003** fixes the allowed dispositions for every mandatory requirement:

```text
PASS
FAIL
NOT_APPLICABLE   with rationale
DEVIATION        with approved deviation identifier
```

and states plainly: "`NOT_RUN` shall not satisfy release acceptance."

Spec §52 declares eight allowed values:

```text
PASS  IMPLEMENTED  NOT_APPLICABLE  UNKNOWN  EXCLUDED  DEVIATION  FAIL  NOT_RUN
```

`IMPLEMENTED`, `UNKNOWN`, and `EXCLUDED` are invented; the set is closed. `IMPLEMENTED` is the
most dangerous of the three — it reads as success but asserts nothing about verification, which is
exactly the gap `PASS` versus `NOT_RUN` exists to expose.

`NOT_RUN` may be tracked as a working state but shall not appear as an acceptance disposition.

**Fix:** reduce §52 to the four permitted values; require rationale on `NOT_APPLICABLE` and a
deviation identifier on `DEVIATION`; state that `NOT_RUN` blocks acceptance.

### C001-2 — No release-class declaration (major)

**RFDS-001-CLS-001**: "Every packaged revision shall declare exactly one release class" from
D0 / D1 / D2 / P1 / B1.

Spec §51 describes a D0→D1→D2→P1 *progression* and names D1 as the first substantial target, but
never requires each packaged revision to *declare* its class, and omits B1 from the enumeration.
Since RFDS-001 §8.2's applicability matrix keys every mandatory requirement off the declared class,
nothing in the plan currently selects which requirements apply.

**Fix:** require a declared release class per packaged revision, recorded in the release manifest,
and bind §53's Definition of Done to RFDS-001 §8.2 for the declared class.

### C001-3 — RFDS revision set not recorded per release (minor)

**RFDS-001-GOV-003**: "Each release shall record the exact revision of every RFDS specification used
for validation. A newer subordinate specification shall not be assumed retroactively unless the
release is revalidated against it."

v1.3 §2.1 now lists correct versions (G1), but nothing requires that list to be emitted into release
evidence. Given that the v1.0–v1.2 baseline drift went unnoticed for three revisions, a machine-
checkable per-release record is the control that would have caught it.

**Fix:** add an RFDS revision manifest to `release/`, and make it a §53 release-blocking check.

---

## RFDS-003 — BaseInstrumentLibrary v1.0

### C003-1 — `rfds-core` dependency never declared (critical)

**RFDS-003 §8.2**: "Each RFDS driver **shall** declare a compatible `rfds-core` version range in its
installation metadata", with the worked example:

```toml
dependencies = [
  "rfds-core>=1.0,<2.0"
]
```

The spec references "the approved `BaseInstrumentLibrary`" in §5 and §39 Gate 2 but never names
`rfds-core`, never requires the dependency declaration, and §37 shows no such dependency.

This is verifiably live in the repository — `rf_hp34401a` declares exactly
`rfds-core>=1.0,<2.0` in both `pyproject.toml` and `requirements.txt`.

**Fix:** name `rfds-core` in §5, require the pinned range in §37's `pyproject.toml`, and add the
dependency to Phase 1 Gate 2.

### C003-2 — No prohibition on a private base-class copy (major)

**RFDS-003 §8.3**: "A driver shall not maintain a modified private copy of the base-class source
under the same identity." An offline package may bundle an approved `rfds-core` wheel only if it
matches the declared dependency and checksum.

The spec says nothing. Given §5's instruction to "derive from the approved `BaseInstrumentLibrary`"
without naming the distribution, a vendored copy is the likely default reading.

**Fix:** state the prohibition and the bundled-wheel checksum condition.

### C003-3 — `rfds-core` version not surfaced in driver info or diagnostics (major)

**RFDS-003 §8.4**: "Driver information and diagnostic bundles shall record the effective `rfds-core`
version."

Spec §7's `Get Driver Information` and §9's diagnostics say nothing about it, and §2.1.1's evidence
contract omits it — although RFDS-008 §11 mandates `software_inventory.json`, which is its natural
home.

**Fix:** require the effective `rfds-core` version in `Get Driver Information`, in the diagnostic
bundle, and in `software_inventory.json`.

---

## RFDS-004 — Transport Layer v1.0

### C004-1 — Transport module layout is wrong (critical)

**RFDS-004 §6** mandates equivalent files to:

```text
transport/                    ← singular
├── __init__.py
├── base.py
├── config.py
├── errors.py
├── models.py
├── codec.py
├── tracing.py
└── backends/
    ├── visa.py
    ├── serial.py
    ├── tcp.py
    ├── usb.py
    └── simulator.py
```

Spec v1.3 §37 has:

```text
transports/                   ← plural
├── factory.py
└── simulator.py
```

Wrong directory name, no `backends/` layer, and seven mandated modules absent. `factory.py` is not
in RFDS-004's layout. The spec's §5 architecture names VISA, Serial, TCP/LAN and Simulator
transports, so at least four backend modules are required.

RFDS-004 §6 does permit omitting *unsupported* backends — but "they shall not be present as
non-functional placeholders", which is a separate rule the plan should carry.

**Fix:** replace `transports/` with the RFDS-004 `transport/` tree, including only supported
backends.

### C004-2 — Inter-guide conflict on `src/` is unrecorded (major)

RFDS-004 §6's tree is rooted at `src/rf_<driver_name>/`. RFDS-005 §6.1 states the opposite: "A new
RFDS driver shall not use a `src/` layout. RFDS-005 is the sole normative source for this rule."

Per RFDS-001 §7.2, RFDS-005 owns package structure and RFDS-004 owns transport behaviour, so
RFDS-005 governs the `src/` question and RFDS-004 governs the module layout *within* the package.
That resolution is defensible — but **RFDS-001-GOV-004 requires a detected conflict to be recorded
and resolved through a correction, interpretation note, architecture decision, or deviation.
"Silent interpretation is prohibited."**

v1.3 applies the resolution silently.

**Fix:** record this conflict and its resolution as an interpretation note in `api/deviations.yaml`
or an architecture decision, citing RFDS-001 §7.2.

### C004-3 — Retry preconditions weaker than RFDS-004 §14 (major)

**RFDS-004 §14.1**: "The default replay policy for all write and transaction operations shall be
`NEVER`."

**RFDS-004 §14.2** permits an automatic retry only when one of five conditions is *proven*:

- no outbound byte was transmitted;
- connection establishment failed before a session was created;
- the protocol layer explicitly marked the operation idempotent and safe to replay;
- a read-only transaction is documented as replay-safe;
- a backend-internal partial operation can be completed without repeating accepted data.

Spec §22.1 permits bounded retry for operations "demonstrably safe and idempotent" and names
`*IDN?` — a weaker, judgement-based test. §22 also never states the `NEVER` default.

The spec's §22.3 destructive-read category is *stricter* than RFDS-004 and should be retained;
RFDS-001 §7.1 permits a lower-level document to add stricter requirements.

**Fix:** state the `NEVER` default, adopt the five proven conditions verbatim as the retry
precondition, and keep §22.3 as an additional restriction.

### C004-4 — Missing transport guide and connection examples (minor)

RFDS-004 §6 mandates `guide/transport_setup.md` and `examples/connection/`; it also splits transport
tests into `tests/unit/transport/` and `tests/integration/transport/`, where the spec has a flat
`tests/transport/`.

**Fix:** add both artifacts and relocate the transport tests.

---

## RFDS-007 — Error and Exception Standard v1.0

### C007-1 — Canonical exception hierarchy never adopted (critical)

**RFDS-007 §6**: "Each driver shall implement or import the following canonical hierarchy",
approximately thirty classes rooted at `DriverError` — `DriverConfigurationError`,
`DriverValidationError` (with `DriverArgumentTypeError`, `DriverArgumentValueError`,
`DriverRangeError`, `DriverUnsupportedValueError`), `DriverStateError` (with
`DriverPreconditionError`, `DriverOperationUncertainError`), `DriverConnectionError`,
`DriverTransportError` (five subclasses), `DriverProtocolError` (five subclasses),
`DriverDeviceError` (four subclasses including `DriverUnsupportedOperationError`),
`DriverResourceError`, and others.

The spec names only four exception types in passing — `DriverProtocolError`,
`DriverUnsupportedOperationError`, `DriverSafetyError`, `DriverLimitViolationError` — and never
requires the hierarchy. Two of those four are not visible in the §6 tree at all, so their placement
is undefined.

Note `DriverOperationUncertainError` exists specifically for the §22.2 uncertain-delivery case the
plan reasons about at length, and the plan never uses it.

**Fix:** require the RFDS-007 §6 hierarchy in `exceptions.py`; map every exception the plan names to
its canonical parent; adopt `DriverOperationUncertainError` for uncertain writes.

### C007-2 — Error code standard never referenced (major)

**RFDS-007 §8.1** fixes the format `RFDS-<DOMAIN>-<NNN>` with three-character uppercase domains and
a zero-padded 001–999 identifier, over a canonical domain catalogue (`CFG`, `ARG`, `STA`, `CON`,
`SAF`, `TMO`, `PRT`, …).

The spec never mentions error codes. Since RFDS-007 §9 supplies a canonical catalogue, codes are not
free-form and cannot be invented per driver.

**Fix:** require RFDS-007 §8/§9 codes on every raised exception, and add code coverage to the §28
error-vector requirements.

### C007-3 — Mandatory exception data and message format unstated (major)

RFDS-007 §10 mandates exception data fields and §11 a public failure message format; §12 governs
Robot Framework behaviour. The spec specifies none of these, yet §28.1 requires "protocol error
vectors" whose expected content is exactly this.

**Fix:** bind §10's error handling and §28's error vectors to RFDS-007 §10–§12.

---

## RFDS-009 — Testing Standard v1.0 *(partial — §7 only)*

### C009-1 — `tests/` set diverges and `results/` is missing (major)

**RFDS-009 §7** mandates: `unit/`, `integration/`, `robot/`, `compatibility/`, `replay/`,
`conformance/`, `hil/`, `performance/`, `support/`, `data/`, plus `config/hil_resources.example.yaml`
and `results/.gitkeep`.

v1.3 §37 provides most, and adds `protocol/`, `transport/`, `simulator/`, `regression/`, `soak/`,
`capability/` — additions are permitted. But **`results/.gitkeep` is absent**, and RFDS-008 §11
requires runtime results to be written outside source-controlled content, making `results/` the
designated location. Its absence means no declared home for evidence.

**Fix:** add `results/.gitkeep`; confirm `config/hil_resources.example.yaml` (already added in v1.3).

### C009-2 — Mandated test scripts partially missing (minor)

RFDS-009 §7 requires `run_tests.{bat,ps1,sh}` and `run_hil_tests.{bat,ps1,sh}`. v1.3 §32 now carries
both after the G11 fix — verified conformant. Recorded here only to close the check.

---

## RFDS-014 — Configuration Model v1.0 *(partial — §6 only)*

### C014-1 — Package-internal configuration resources missing (major)

**RFDS-014 §6** mandates a package-internal copy in addition to the repository `config/` tree:

```text
rf_<driver_name>/resources/configuration/
├── schema.json
├── schema.lock
└── default.json
```

v1.3 §37 has `rf_keysight349xx/resources/` (added under G10) but not the `configuration/`
subdirectory or its three files. Without them the installed wheel has no schema or defaults at
runtime — the repository `config/` tree is not packaged.

**Fix:** add `resources/configuration/{schema.json,schema.lock,default.json}` and require them to be
kept identical to the repository copies by `generate_metadata`.

### C014-2 — `config/migrations/README.md` and `tests/data/configuration/` missing (minor)

RFDS-014 §6 mandates both. v1.3 has `config/migrations/` (empty) and `tests/data/` but neither named
artifact.

---

## RFDS-015 — Plugin Architecture v1.0

### C015-1 — Plugin manifest in the wrong location (major)

**RFDS-015 §8** requires `rf_<driver_name>/resources/plugin_manifest.json` — inside the package, so
it is importable at runtime.

Spec §24 says "Add: `plugin.py`, `plugin_manifest.json`" without a path, and §37 does not show it at
all. A repository-root manifest would not be packaged.

**Fix:** place it at `rf_keysight349xx/resources/plugin_manifest.json` in §37.

### C015-2 — `tests/plugin/` layer absent (major)

RFDS-015 §8 mandates four named tests:

```text
tests/plugin/
├── test_entry_point.py
├── test_manifest.py
├── test_import_safety.py
└── test_provider_lifecycle.py
```

`test_import_safety.py` is the enforcement of §24's own "importing the plugin performs no hardware
I/O" requirement, which the plan states but never tests.

**Fix:** add `tests/plugin/` with the four tests; add plugin tests to §29.1.

### C015-3 — `docs/plugin_integration.md` missing (minor)

Mandated by RFDS-015 §8; absent from §33 even after the G13 fix.

### C015-4 — Entry-point group not named (minor)

RFDS-015 §8 requires the `rfds.drivers` entry-point declaration in `pyproject.toml`. Spec §24 refers
to "the required RFDS plugin entry point" without naming the group, leaving it to inference.

**Plugin ID verified conformant.** `keysight.349xx` satisfies RFDS-015 §7.1 — lowercase, two
dot-separated segments, characters limited to `a-z`/`0-9`/`_`, no version, no transport name.
RFDS-015 §7.2 confirms it need not match the project folder or import package. No finding.

---

## Summary

| Severity | Count | IDs |
|---|---:|---|
| Critical | 3 | C003-1, C004-1, C007-1 |
| Major | 12 | C001-1, C001-2, C003-2, C003-3, C004-2, C004-3, C007-2, C007-3, C009-1, C014-1, C015-1, C015-2 |
| Minor | 6 | C001-3, C004-4, C009-2, C014-2, C015-3, C015-4 |

**The three critical findings share a pattern with the earlier reviews:** each is a mandatory
artifact or contract the plan gestures at without adopting. §5 says "derive from the approved
`BaseInstrumentLibrary`" without naming `rfds-core`; §37 has a `transports/` directory that is not
the mandated `transport/` tree; the plan raises four exception types without the thirty-class
hierarchy they belong to.

None requires the Keysight command reference. All are document edits.

### Recommended order for v1.4

1. **C003-1, C004-1, C007-1** — the three critical adoptions.
2. **C001-1, C001-2** — traceability dispositions and release-class declaration; these gate §53.
3. **C004-2** — record the `src/` conflict rather than resolving it silently (RFDS-001-GOV-004).
4. **C014-1, C015-1, C015-2** — packaged runtime artifacts and the plugin test layer.
5. Remaining majors and minors.

### Next cycle

Not yet reviewed: **RFDS-006** (coding standard), **RFDS-010** (review checklist — likely to
restructure §36), **RFDS-012** (GUI integration — the plan mentions GUI metadata only once, in §48),
**RFDS-018** (bench contract). Partial: **RFDS-009** beyond §7, **RFDS-014** beyond §6,
**RFDS-017**, **RFDS-019**.

Given that every completed cycle so far has produced findings, the remaining four guides should be
expected to as well, and v1.4 should not be treated as final until they are done.
