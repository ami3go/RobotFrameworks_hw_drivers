# Guide Conformance Review — Spec v1.2 against `AI_Guides/`

> **STATUS: CLOSED — all findings resolved.** This review covers **v1.2**. Every finding below
> (G1–G15) was applied in **v1.3**; see the v1.3 revision-history table for the finding-to-section
> mapping. **The current specification is `RF_Keysight349xx_Driver_Implementation_Plan_v1.3.md`.**
> Retained as the historical record — do not read the findings below as open.

**Reviewed document:** `RF_Keysight349xx_Driver_Implementation_Plan_v1.2.md`
**Reviewed against:** all 19 RFDS specifications in `AI_Guides/` (28,501 lines)
**Review date:** 2026-08-18
**Predecessor reviews:** `SPEC_REVIEW.md` (v1.0), `DEEP_REVIEW_v1.1.md` (v1.1)
**Scope:** specification only — no implementation exists, and none was written for this review.

---

## 1. Verdict

**v1.2 is NOT conformant with the RFDS guide set. Do not enter Phase 1 Gate 1.**

The two previous reviews assessed the plan on its own terms and against repository convention.
Neither checked it against the actual normative documents in `AI_Guides/`. Doing so changes the
picture materially: **15 conformance defects**, of which 4 are critical.

The most consequential finding is that the plan's declared authoritative baseline is itself wrong.
§2.1 cites four RFDS versions that do not exist in the guide set. A plan whose foundational premise
is "every capability shall be traceable to an RFDS requirement" cannot proceed while it cites
requirements documents that cannot be opened.

Three findings — **G7, G8, G9** — are defects in edits **I introduced in v1.2**. Fixing the deep
review's findings without first consulting the guides caused me to invent keyword names and
mechanisms that the standards already specify differently. Those are recorded here with the same
weight as the others.

### What the plan gets right

Verified as conformant, not assumed:

- **§7 mandatory universal keywords** match RFDS-002 §8 exactly — all ten, correct names, correct set.
- **§28 conformance tree** matches RFDS-005 §10.2 path for path.
- **Safe shutdown as mandatory** is correct: RFDS-002 §9.10 makes it mandatory for drivers that
  "switch hazardous power", which this driver does.
- **B1's flat-layout fix** now has a normative citation: RFDS-005 §6.1 states "A new RFDS driver
  shall not use a `src/` layout."
- **§38's five gates** match RFDS-020 exactly.

---

## 2. Critical findings

### G1 — Four cited RFDS versions do not exist

**Where:** §2.1 authoritative source set.

| Spec §2.1 cites | Actual file in `AI_Guides/` |
|---|---|
| RFDS-001 Platform Requirements **v1.2** | Platform Requirements **v1.1** |
| RFDS-002 Mandatory Public API and Keyword Standard **v1.1** | **v1.0** |
| RFDS-003 BaseInstrumentLibrary Common Base Class Design **v2.0** | **v1.0** |
| RFDS-004 Transport Layer Specification **v2.0** | **v1.0** |

Four of sixteen cited documents name versions that are not present. RFDS-003 and RFDS-004 are cited
two major versions ahead of what exists.

This is not a citation formality. §1 requires every capability to trace to "a project RFDS
requirement", and §52 requires a traceability matrix with `source_document` and `source_section`
fields. Both are unbuildable against documents that cannot be located, and any requirement traced to
"RFDS-004 v2.0" is untraceable by definition.

**Recommendation:** Correct all four to the versions present in `AI_Guides/`. If newer revisions
genuinely exist outside the repository, they shall be added to `AI_Guides/` before being cited —
the guide set is the baseline, and a plan may not cite a baseline the project does not hold.

### G2 — Release identity violates RFDS-011 throughout

**Where:** §3.2, §3.3, §35; also the "Target release family" in the document header.

RFDS-011 §6.1 and §6.2 define the mandatory ZIP names:

```text
public:            rf_<driver_name>_vYY.RR.zip
engineering gate:  rf_<driver_name>_vYY.PP.GG.zip
```

with `vYY.RR` (§5.2) zero-padded and `vYY.PP.GG` (§5.3) being year, **phase**, **gate**.

| Artifact | Spec v1.2 | RFDS-011 requires |
|---|---|---|
| Public ZIP | `rf_keysight349xx_v26.01.00.zip` | `rf_keysight349xx_v26.01.zip` |
| Gate 1 ZIP | `rf_keysight349xx_v26.01.00-g1.zip` | `rf_keysight349xx_v26.01.01.zip` |
| Gate 5 ZIP | `rf_keysight349xx_v26.01.00-g5.zip` | `rf_keysight349xx_v26.01.05.zip` |
| History file | `v26.01.00-g1.md` | `v<version>.md` per RFDS-005 §6 |

The `-gN` suffix is invented; RFDS-011 encodes the gate in the third version field. The three-part
public version is also wrong — `vYY.RR` is two fields.

RFDS-020's versioning section says the same thing independently, and RFDS-011 §6.2's own worked
example is `rf_keysight34970_v26.03.04.zip` — the guide set already anticipates a Keysight 34970
driver and shows exactly the form this plan does not use.

**This finding also invalidates my v1.2 §3.3 edit**, which defined source version `26.01.00` and
distribution `26.1.0`. Per RFDS-011 §5.5 the correct mapping is `v26.01` → `26.1`.

**Recommendation:** Replace the entire release-identity scheme in §3.2, §3.3, §35, and the header
with the RFDS-011 forms. Note RFDS-011 §5.3: an engineering gate version "shall not consume a public
`RR` sequence".

### G3 — RFDS-013 Capability Model is mandatory, present, and omitted

**Where:** §2.1 (absent), §2.1.2 (marked `UNKNOWN` by my v1.1 edit), §9, §37.

`AI_Guides/RFDS-013_Capability_Model_v1.0.md` exists (2,281 lines) and defines a **mandatory,
machine-readable capability model**. My v1.1 edit recorded it as `UNKNOWN` pending confirmation;
having now read it, that disposition is wrong — it is in force.

RFDS-013 §7.1 mandates **six** public discovery keywords:

```robotframework
Get Capability Model
Get Driver Capability
Find Driver Capabilities
Get Driver Features
Refresh Driver Capabilities
Validate Driver Capabilities
```

The plan lists only `Get Capability Model`, and lists it in §9 among system/identity functions
rather than as capability discovery. Five mandatory keywords are missing from the public API
inventory entirely.

RFDS-013 §7.1 is also explicit that `Get Capability Model` and RFDS-002's `Get Driver Capabilities`
are **deliberately distinct** — the latter returns a flat `list[str]` of group names, the former the
richer RFDS-013 structure — and that "a driver shall implement both", with the AI contract mapping
each RFDS-002 group name to its RFDS-013 `capability_id` entries. The plan treats them as one
concept.

RFDS-013 further mandates an artifact tree the plan does not have:

```text
capability/
├── capability_model.yaml
├── capability_model.schema.json
├── capability_taxonomy_extensions.yaml      # optional
└── examples/
    ├── capability_snapshot.json
    └── capability_query_examples.robot
tests/capability/
├── capability_model_validation.robot
├── capability_binding_validation.robot
└── capability_runtime_discovery.robot
```

The plan's §37 has `capabilities/capabilities.yaml` — wrong directory name, wrong filename, no
schema, no examples, no `tests/capability/` layer.

This finding compounds B3 from the first review: the internal-DMM gate added in v1.1 is exactly the
kind of runtime capability state RFDS-013 exists to express, and it currently has nowhere
conformant to live.

**Recommendation:** Add RFDS-013 to §2.1; add the six keywords to the public API inventory; replace
`capabilities/` with the RFDS-013 `capability/` tree; add the `tests/capability/` layer; and map the
DMM gate, module inventory, and model gating into the capability model.

### G4 — RFDS-011 Release Process is omitted though normatively referenced

**Where:** §2.1 (absent), §2.1.2 (marked `UNKNOWN`).

`RFDS-011_Release_Process_v1.0.md` exists (1,866 lines) and is listed as a **normative reference by
RFDS-020**, which the plan does cite. It governs release identity (G2), ZIP naming, version
immutability, and the release gates the plan's §50–§53 describe informally.

RFDS-011 §5.6 adds a requirement absent from the plan: after publication a version identifies one
immutable artifact set, and a rebuild under the same version is permitted "only when it produces
byte-identical artifacts".

**Recommendation:** Add RFDS-011 to §2.1 and align §3.2, §35, §50, §51, and §53 to it.

---

## 3. Major findings

### G5 — RFDS-016 does not exist

§2.1.2 (my v1.1 edit) lists RFDS-016 with disposition `UNKNOWN`. There is no RFDS-016 in
`AI_Guides/`; the set runs 001–015 and 017–020, with 016 absent. The correct disposition is
"no such document", not `UNKNOWN` — the latter implies an unread requirement that might apply.

### G6 — RFDS-008 title is wrong

§2.1 (my v1.1 edit) names it "Live Evidence and Run Record Standard". The actual title is
**"Logging and Evidence Standard v1.0"**. I invented a plausible-sounding title rather than reading
the file. The §2.1.1 artifact contract I wrote should also be re-derived from the actual 2,105-line
standard rather than from repository observation, since it was written from what other drivers
happen to produce.

### G7 — Raw I/O keyword names violate RFDS-002 §9.11

My v1.2 §8.1 specified `Enable Raw SCPI`, `Disable Raw SCPI`, `Raw SCPI Write`, `Raw SCPI Query`.

RFDS-002 §9.11 gives the **permitted canonical names**:

```text
Write Raw Command(command, alias=None) -> None
Query Raw Command(command, alias=None, timeout_s=None) -> str | bytes
Read Raw Response(alias=None, timeout_s=None) -> str | bytes
```

`Raw SCPI Write` and `Raw SCPI Query` are non-conformant and shall be renamed. RFDS-002 also
requires the tags `rfds:raw_io` and `rfds:high_risk`, which §8.1 does not name, and requires that
"the AI Driver Contract shall warn that raw I/O may invalidate state tracking" — §8.1 states the
equivalent in prose but not as an AI-contract obligation.

The enable/disable gate itself is compatible: RFDS-002 requires raw I/O be "disabled by default or
require explicit opt-in when it can bypass driver safety validation", which is what §8.1 mandates.
Only the operation names are wrong.

### G8 — `Reset Device` confirmation gate conflicts with the canonical signature

My v1.2 §9.1 (fixing C2) requires "an explicit confirmation argument" on `Reset Device`.

RFDS-002 §9.8 fixes the canonical signature:

```text
Reset Device(alias=None, wait_until_ready=True, timeout_s=None) -> dict
```

There is no confirmation parameter, and RFDS-002 §9.8's remedy for the hazard is documentation, not
a gate — it requires the docs to state reset type, output behavior, settings preserved or cleared,
reconnect behavior, expected ready time, and safety risk.

The C2 hazard is real: a device reset opening all relays genuinely does conflict with §21 ownership.
But the fix as written silently diverges from a canonical signature.

**Recommendation:** Either (a) keep the canonical signature and satisfy the hazard through the §9.8
documentation requirements plus a capability/bench-contract gate, or (b) retain the confirmation
argument as an **approved deviation** recorded in `api/deviations.yaml`. Option (a) is preferable;
either way the divergence must be explicit, which it currently is not.

### G9 — Error-queue bound is a keyword argument, not a configuration setting

My v1.2 §10.2 (fixing M11) requires the drain bound to be "defined in configuration (§23)".

RFDS-002 §9.2 already fixes it as a keyword argument with a default:

```text
Get All Device Errors(alias=None, max_count=100) -> list[dict]
```

RFDS-002 §9.2 additionally mandates an error dictionary schema the plan's §10 never states:

```yaml
code: 0
message: No error
raw: '0,"No error"'
source: device
```

**Recommendation:** Move the bound to `max_count` with default 100, keep the truncation-reporting
requirement (which RFDS-002 does not specify and which strengthens it), and add the mandated error
dictionary schema to §10.

### G10 — §37 package layout diverges from RFDS-005 §6 in mandatory paths

RFDS-005 §6 states that "Mandatory paths shall not be renamed, relocated, or replaced by equivalent
content in an undocumented location." The following do exactly that:

| Spec v1.2 §37 | RFDS-005 §6 requires |
|---|---|
| `bench/system_ai_contract.template.yaml` | `ai/system_ai_contract.template.yaml` |
| `config/examples/` | `config/example.json`, `config/profiles/`, `config/hil_resources.example.yaml`, `config/migrations/` |
| `capabilities/capabilities.yaml` | `capability/capability_model.yaml` (see G3) |
| `release/release_manifest.yaml` | `release/release_manifest.json` |
| — | `rf_<driver>/models.py` (missing) |
| — | `rf_<driver>/resources/` (missing) |
| — | `robot_resources/common.resource`, `variables.example.yaml` (missing) |
| — | `generated/libdoc/`, `generated/api_manifest/` (missing) |
| — | `tests/support/`, `tests/data/` (missing) |

`api/public_api.yaml`, `api/unknowns.yaml`, and `api/deviations.yaml` are not in RFDS-005's tree
either; RFDS-005 uses `generated/api_manifest/`. Since RFDS-005 permits added device-specific files,
`api/` may be acceptable as an addition — but it does not discharge the requirement to provide
`generated/api_manifest/`.

### G11 — §32 script set diverges from RFDS-005 §6

RFDS-005 mandates a specific script set. The plan's §32 renames some and omits others:

- `setup_env.{ps1,sh}` → RFDS-005 requires `setup_venv.{bat,ps1,sh}`;
- missing entirely: `run_example.*`, `run_all_examples.*`, `run_hil_tests.*`,
  `run_call_protocol_conformance.*`, `generate_libdoc.*`, `validate_structure.py`,
  `compare_public_api.py`, `build_release.py`;
- RFDS-005 requires `.bat` variants alongside `.ps1`/`.sh` for the runner scripts; §32 provides only
  two variants.

My v1.2 M2 edit added `validate_ai_contract.*`, which **is** in RFDS-005's list — that addition was
correct, but it was reached by inference rather than citation, and the rest of the mandated set was
not added with it.

### G12 — §36 review artifacts diverge from RFDS-005 §6

RFDS-005 mandates `review/README.md`, `requirement_traceability.md`, `known_risks.md`,
`evidence/v<version>/`, and version-prefixed review files
(`v<version>_code_review.md`, `_architecture_review.md`, `_robot_api_review.md`,
`_documentation_review.md`, `_conformance_review.md`, `_security_review.md`,
`_compatibility_review.md`, `_release_readiness.md`).

§36 uses gate-prefixed names (`g1_architecture_review.md`) and omits `README.md`,
`requirement_traceability.md`, `known_risks.md`, and `evidence/`.

### G13 — §33 documentation set omits five mandatory pages

RFDS-005 §6 mandates `docs/quick_start.md`, `compatibility.md`, `migration.md`, `support_policy.md`,
and `examples.md`. None appears in §33.

### G14 — §35 history naming diverges

RFDS-005 requires `history/README.md` and `history/v<version>.md`. §35 omits the README and uses the
non-conformant `v26.01.00-g1.md` form (see G2).

### G15 — AI contract identity binding unstated

RFDS-017 §4 requires `ai_contract.yaml` to declare a root `identity` section whose `plugin_id`
**shall equal** the RFDS-015 plugin manifest `plugin_id`. §25's field list is per-keyword only and
never mentions the identity section or that binding, so the plan does not require the two artifacts
to agree.

RFDS-017 also states it is "the sole normative source for the structure and required fields of
`ai_contract.yaml`" — §25's hand-written field list should therefore defer to RFDS-017 rather than
enumerate independently, or it will drift from the standard.

---

## 4. Scoring

| Area | Weight | Score | Note |
|---|---:|---:|---|
| Authoritative baseline correctness | 20% | 3.0 | G1, G3, G4, G5, G6 — four phantom versions, two mandatory standards omitted |
| Release identity conformance | 15% | 2.0 | G2 — non-conformant in every artifact name |
| Package layout conformance | 15% | 5.0 | G10, G11, G12, G13, G14 |
| Public API conformance | 20% | 6.0 | §7 correct; G3 (5 keywords missing), G7, G8, G9 |
| Capability model conformance | 10% | 2.0 | G3 — mandatory standard absent |
| Evidence conformance | 10% | 6.0 | G6 — right intent, unverified derivation |
| Internal quality (carried from v1.2) | 10% | 9.0 | deep-review findings all resolved |

**Overall: 4.75 / 10** against the guide set.

The earlier scores (8.96, 8.16) measured internal coherence and device-technical soundness, and
remain valid on those axes. This axis was never measured before. A plan can be internally excellent
and still non-conformant, which is what these numbers together say.

---

## 5. Required actions

**Before any further specification work:**

1. **G1** — correct the four phantom version citations against `AI_Guides/`.
2. **G3** — adopt RFDS-013: six mandatory keywords, `capability/` tree, `tests/capability/`.
3. **G4** — adopt RFDS-011 and align §50–§53.
4. **G2** — replace the release-identity scheme everywhere with `vYY.RR` / `vYY.PP.GG`.

**Then:**

5. **G5, G6** — correct the RFDS-016 disposition and the RFDS-008 title; re-derive §2.1.1 from the
   actual standard.
6. **G7, G8, G9** — realign my v1.2 raw-I/O names, reset gate, and error-queue bound to RFDS-002.
7. **G10–G14** — align layout, scripts, reviews, docs, and history with RFDS-005 §6.
8. **G15** — bind the AI contract identity to the plugin manifest and defer §25 to RFDS-017.

**Process note.** Every finding in this review was available from the start — the guides are in the
repository. The first two reviews did not open them, and the v1.2 edits I made in response invented
three mechanisms the standards already specified. The plan's own §55 principle is source-first;
that discipline applies to reviewing it as much as to writing it.

---

## 6. Status

```text
Reviewed:              RF_Keysight349xx_Driver_Implementation_Plan_v1.2.md
Checked against:       19 RFDS specifications in AI_Guides/ (28,501 lines)
Implementation:        NOT STARTED — no code written
Critical findings:     4  (G1-G4)
Major findings:        11 (G5-G15)
Of which introduced
  by my own v1.2 edits: 3 (G7, G8, G9) plus G5/G6 from v1.1
Conformance verdict:   NOT CONFORMANT — do not enter Phase 1 Gate 1
Recommended next step: spec v1.3 applying items 1-8
```
