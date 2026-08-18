# Deep Review — Spec v1.7

> **STATUS: CLOSED — all findings resolved.** D1–D4 applied in **v1.8**: `api/public_api.yaml` is
> now the sole authoritative inventory as the union of the device-facing map and the 34 mandatory
> driver-level keywords, the drift guard no longer punishes conformance, precedence is scoped to the
> command↔keyword binding, and `capability_group` is on every mapped command.
> **The current specification is `RF_Keysight349xx_Driver_Implementation_Plan_v1.8.md`.**
> Retained as the historical record — do not read the findings below as open.

**Reviewed:** `RF_Keysight349xx_Driver_Implementation_Plan_v1.7.md`, `protocol/vendor_command_coverage.yaml`
**Review date:** 2026-08-18
**Predecessors:** `SPEC_REVIEW.md` (v1.0), `DEEP_REVIEW_v1.1.md` (v1.1),
`GUIDE_CONFORMANCE_REVIEW_v1.2.md` (v1.2), `CYCLING_REVIEW_v1.3.md` (v1.3),
`ARTIFACT_REVIEW_v1.6.md` (v1.6)
**Axis:** whether the plan is *implementable* — does its declared public surface actually
constitute a driver?
**Scope:** specification only — no implementation exists.

---

## 1. Verdict

**One critical defect, and it is the largest found in seven passes.**

§9.2 — declared authoritative for the keyword inventory — **excludes 33 of the 34 mandatory RFDS
keywords.** Every RFDS-014 configuration keyword, every RFDS-013 capability keyword, nine of the ten
RFDS-002 §8 universal keywords, `Safe Shutdown`, `Recover Connection`, and all five raw-I/O keywords
are absent from it.

This is the same failure mode as `ARTIFACT_REVIEW_v1.6.md` R1 — generation silently removing a
declared capability — at **eleven times the scale**. I introduced it in v1.6 and v1.7 preserved it
while fixing R1 and R2 around it.

The rest of v1.7 holds up. The R1–R5 corrections are sound and independently re-verified below.

---

## 2. Critical finding

### D1 — The authoritative keyword inventory excludes the entire driver-level API

**Severity: CRITICAL** (RFDS-010 §9.1 — a declared mandatory capability removed; the plan as written
does not describe a conformant driver)

v1.6 introduced §9.2 and declared:

> `protocol/vendor_command_coverage.yaml` is the **authoritative** binding … Where a narrative list
> and this table disagree, **this table governs**.

§9.2 is generated from the vendor command map. **Driver-level keywords have no vendor command** —
`Connect` opens a transport, `Import Driver Configuration` manipulates a JSON document,
`Get Capability Model` reads a YAML file. None of them emits SCPI. A command-derived inventory can
therefore only ever contain *device-facing* keywords, and declaring it authoritative for the whole
public API excluded everything else.

Measured against the guides:

| Mandatory group | Absent from §9.2 |
|---|---|
| RFDS-002 §8 universal API | **9 of 10** |
| RFDS-013 §7.1 capability discovery | **6 of 6** |
| RFDS-014 configuration API | **11 of 11** |
| `Safe Shutdown`, `Recover Connection`, raw I/O | **7 of 7** |
| **Total** | **33 of 34** |

`Get Identity` is the sole survivor, and only because it happens to map to `*IDN?`.

**The information is not lost** — §7, §7.2, §8.1, §8.2, §21, and §23 all still list these keywords in
prose. What is wrong is the *authority claim*: v1.7 states the table governs where they disagree, so
as written the plan says a conformant driver needs none of them. Anyone building `api/public_api.yaml`
from the authoritative artifact would ship a driver with no `Connect`.

**The v1.7 drift guard makes this worse, not better.** §9.2 requires
`validate_structure.py` to fail when "a keyword appears in `api/public_api.yaml` but not in
`vendor_command_coverage.yaml`". Since all 33 would appear in `public_api.yaml` and none in the map,
**the guard would fail the build for correctly implementing the mandatory API** — and the obvious way
to make it pass is to delete the keywords.

**Fix.** The keyword inventory has two disjoint sources and needs both:

```yaml
device_facing:      vendor_command_coverage.yaml   # 121 keywords, SCPI-bound
driver_level:       RFDS-002 §8/§9, RFDS-013 §7.1, RFDS-014   # 34 keywords, no SCPI
public_api.yaml:    the union, and the only authoritative inventory
```

§9.2 should present the device-facing table as *one input* to `api/public_api.yaml`, not as the
inventory. The drift guard must then check:

- every `PUBLIC` command binds to a keyword in `public_api.yaml`;
- every *device-facing* keyword in `public_api.yaml` binds to a command;
- every mandatory RFDS keyword is present in `public_api.yaml` **and is exempt from the
  command-binding requirement**.

Total public surface is therefore ~**155 keywords**, not 121 — which sharpens the §9.2 scope warning
rather than softening it.

---

## 3. Major findings

### D2 — "Where the table governs" is too broad a rule

Even once D1 is fixed, "this table governs" is the wrong precedence rule. The table can only be
authoritative about *which vendor command backs a device-facing keyword*. It cannot be authoritative
about whether a keyword should exist, what it returns, or whether it is mandatory — those are owned
by RFDS-002, RFDS-013, and RFDS-014 respectively, per RFDS-001 §7.2's subject-ownership table.

v1.7 granted a generated artifact precedence over normative specifications. That inverts
RFDS-001 §7.1's hierarchy, which places subordinate RFDS specifications above "approved
device-specific implementation specification or task".

**Fix:** scope the precedence claim explicitly to the command↔keyword binding.

### D3 — §9.2's scope note understates the surface

§9.2 records "121 keywords / 347 commands … roughly double the keyword surface of the largest
existing driver". With the driver-level keywords included the real figure is ~155 — roughly **two
and a half times** `rf_ngi_n83624`'s 62. The scope re-assessment at Phase 1 Gate 5 should be against
that number.

### D4 — No keyword-to-capability-group traceability

RFDS-013 §7.1 requires the AI contract to "map each RFDS-002 group name to its corresponding
RFDS-013 `capability_id` entries", and RFDS-002 §9 makes a group mandatory once its capability is
declared. Nothing in the plan maps the 121 device-facing keywords onto RFDS-002 capability groups,
so there is no way to check that a declared group is *completely* implemented — which §8 explicitly
requires ("Partial implementation of a declared RFDS capability group shall not be accepted").

**Fix:** add a `capability_group` field per keyword and a completeness check per declared group.

---

## 4. Re-verified from `ARTIFACT_REVIEW_v1.6.md`

Checked independently rather than trusted:

| Finding | State in v1.7 |
|---|---|
| R1 — three statistics commands missing | **Fixed.** `CALCulate:AVERage:MINimum?`, `:AVERage?`, `:MINimum:TIME?` present; `Get Channel Minimum`/`Average`/`Minimum Timestamp` restored |
| R2 — false coverage claim | **Fixed.** 347 commands from Syntax sections; claim restated with the method named |
| R2a — 2-wire RTD unbound | **Fixed.** `TRANsducer:RTD:*` bound to `Configure RTD` |
| R3 — family notes as coverage | **Fixed.** Families expanded to explicit rows |
| R4 — guard on the wrong edge | **Partly fixed.** The reference↔map check is correct and the non-circularity requirement is well stated — but the map↔`public_api` check is now actively harmful (see D1) |
| R5 — verification scope | **Fixed.** Scope restated against the 347-command inventory |

Also verified clean: no keyword is bound exclusively to `EXCLUDED` or `INTERNAL` commands, and all
121 map keywords appear in v1.7.

---

## 5. Pattern

Fourth consecutive pass in which the defect was in something I generated, and the fourth found by
changing method rather than looking harder:

| Pass | Method that found it |
|---|---|
| Guide conformance | Read the standards instead of inferring from precedent |
| v1.6 self-check | Programmatic diff instead of sampling (11 → 40) |
| Artifact review | Checked the map against the reference instead of itself |
| **This pass** | **Checked the inventory against the *guides* instead of against the reference** |

Each generated artifact was complete with respect to the source its generator knew about, and
incomplete with respect to a source its generator never consulted. R1/R2 came from an extractor that
only knew block titles; D1 comes from a generator that only knew SCPI commands. The recurring defect
is not carelessness — it is **treating a single-source derivation as a complete inventory**.

The generalisable rule, which v1.8 should state in §9.2: *an inventory assembled from one source is
authoritative only over that source's domain.*

---

## 6. Required actions

1. **D1** — make `api/public_api.yaml` the sole authoritative inventory, as the union of the
   device-facing table and the mandatory driver-level keywords; rewrite the drift guard so it cannot
   fail a correct implementation.
2. **D2** — scope §9.2's precedence claim to the command↔keyword binding only.
3. **D3** — restate the surface as ~155 keywords.
4. **D4** — add capability-group traceability and a per-group completeness check.

None needs new information. All are corrections to v1.6/v1.7.

---

## 7. Status

```text
Reviewed:              v1.7 + vendor_command_coverage.yaml
Implementation:        NOT STARTED — no code written
Critical findings:     1  (D1 — 33 of 34 mandatory keywords excluded)
Major findings:        3  (D2, D3, D4)
Prior findings:        R1-R5 re-verified; R4 only partly resolved
Defect origin:         v1.6 §9.2 authority claim, preserved through v1.7
Recommended next step: v1.8 applying items 1-4 before Phase 1 Gate 1
```
