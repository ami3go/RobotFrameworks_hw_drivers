# RFDS-017 — AI Driver Contract Specification

**Version:** 3.0 (Draft)
**Document ID:** RFDS-017
**Status:** Draft project requirement
**Applies to:** all discoverable RFDS driver packages, AI planners and code-generation agents, RFDS-015 plugin managers, RFDS-018 bench managers, and any tool that consumes `ai_contract.yaml`

---

## 1. Purpose

This specification defines the canonical, machine-readable AI contract that describes one Robot Framework driver so that an AI agent can understand, safely select, and generate Robot Framework tests for that driver without reading its source code.

RFDS-017 is the sole normative source for the structure and required fields of `ai_contract.yaml` and its integrity companion `ai_contract.lock`. Other specifications (RFDS-013, RFDS-014, RFDS-015, RFDS-018) reference these files but shall not redefine their schema.

## 2. Scope Boundary

### 2.1 In scope

- the required files, sections, and fields of one driver's AI contract;
- the mapping between contract fields and the canonical vocabularies owned by other RFDS specifications;
- contract identity, versioning, and integrity (`ai_contract.lock`);
- conformance rules for a valid contract.

### 2.2 Out of scope

RFDS-017 does not define:

- the capability taxonomy itself (owned by RFDS-013);
- the exception hierarchy or error-message format (owned by RFDS-007);
- the connection/session state enum (owned by RFDS-003);
- device configuration schema (owned by RFDS-014);
- plugin discovery, loading, or the plugin manifest (owned by RFDS-015);
- bench topology or multi-driver system contracts (owned by RFDS-018);
- protocol-level conformance vectors (owned by RFDS-019).

RFDS-017 references these authorities rather than duplicating them; a field in `ai_contract.yaml` that expresses a value governed by another RFDS specification shall use that specification's canonical vocabulary and shall fail contract validation if it diverges.

## 3. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviations require documented justification;
- **may** — permitted implementation choice;
- **AI contract** — the `ai_contract.yaml` document described by this specification;
- **contract lock** — the `ai_contract.lock` integrity artifact described in §6;
- **capability entry** — one contract record describing a single Robot keyword, per §8;
- **oracle** — a machine-checkable pass/fail condition used to verify a capability's postcondition.

## 4. Normative References

- RFDS-001 — Platform Requirements
- RFDS-002 — Mandatory Public API and Robot Framework Keyword Standard
- RFDS-003 — BaseInstrumentLibrary: Common Base Class Design
- RFDS-005 — Driver Package Specification
- RFDS-007 — Error and Exception Standard
- RFDS-013 — Capability Model
- RFDS-014 — Driver Configuration Model Specification
- RFDS-015 — Plugin Architecture

## 5. Required Files

```text
ai/
├── ai_contract.yaml
└── ai_contract.lock
```

Both files shall be packaged inside the driver's RFDS-005 repository tree and shall be reachable at release time either as a `repository_path` or, when runtime access is required, as a `package_resource` per RFDS-015 §9.2.1.

## 6. Contract Identity and Integrity

### 6.1 Identity fields

`ai_contract.yaml` shall declare, at its root, an `identity` section containing at least:

- `contract_schema_version` — the RFDS-017 schema version this file conforms to;
- `plugin_id` — shall equal the RFDS-015 plugin manifest `plugin_id`;
- `driver_name` — shall equal the RFDS-015 plugin manifest `driver_name`;
- `distribution_name` — shall equal the RFDS-015 plugin manifest `distribution_name`;
- `distribution_version` — shall equal the installed distribution version;
- `robot_library_import` — shall equal the RFDS-015 plugin manifest `robot_library_import`;
- `robot_library_class` — shall equal the RFDS-015 plugin manifest `robot_library_class`;
- `supported_models` — shall be consistent with the RFDS-015 plugin manifest.

A mismatch between any identity field and its corresponding RFDS-015 manifest field shall fail plugin validation per RFDS-015 §21.1.

### 6.2 `ai_contract.lock`

`ai_contract.lock` shall contain:

- `contract_sha256` — the SHA-256 digest of the canonical `ai_contract.yaml` content;
- `generated_at` — an ISO-8601 timestamp;
- `generator` — the tool and version that produced the lock file.

A driver release shall fail validation when `ai_contract.lock` does not match the packaged `ai_contract.yaml`. This is the "contract-lock validity" check referenced by RFDS-015 §21.1.

## 7. Mandatory Sections

`ai_contract.yaml` shall contain the following top-level sections:

1. **Identity** — per §6.1;
2. **Mental model** — a short natural-language description of what the instrument does and how an agent should reason about it;
3. **State machine** — per §9;
4. **Resources consumed/provided** — physical or logical resources (channels, ports, exclusive locks) the driver manages;
5. **Dependencies** — required and optional runtime dependencies, consistent with the RFDS-015 manifest's dependency declarations;
6. **Capabilities** — one entry per Robot keyword, per §8;
7. **Error catalogue** — per §10;
8. **Safety rules** — natural-language and machine-checkable constraints an agent shall respect (e.g., voltage limits, interlocks);
9. **Verification objectives** — pass/fail oracles used to confirm a generated test achieved its intent;
10. **Setup/teardown contract** — required preconditions and cleanup obligations for generated tests;
11. **Limitations** — known gaps, unsupported models, or simulation-only behavior;
12. **Planning hints** — ordering constraints, timing guidance, and preferred keyword sequences;
13. **UNKNOWN handling** — how the driver reports and how an agent should treat values it cannot determine (see §11);
14. **Conformance rules** — per §12.

A contract missing any mandatory section shall fail RFDS-017 conformance.

## 8. Capability Entries

### 8.1 Required fields

Each capability entry shall correspond to exactly one mandatory Robot Framework keyword defined by RFDS-002 or RFDS-013, and shall declare:

- `keyword` — the exact Robot Framework keyword name;
- `capability_id` — the RFDS-013 §10.1 hierarchical identifier (`<domain>.<object>.<operation>`) this keyword implements, when one applies;
- `signature` — argument names, types, and defaults;
- `purpose` — a short natural-language description;
- `inputs` / `outputs` — machine-readable argument and return descriptions;
- `preconditions` — required driver state(s) using the RFDS-003 §13.1 canonical state enum;
- `postconditions` — resulting state(s) and observable effects;
- `side_effects` — any effect beyond the return value (e.g., device output enabled);
- `risk_level` — one of the RFDS-002 §16.1 canonical values (`none`, `low`, `medium`, `high`, `critical`);
- `timing` — expected typical execution duration;
- `stabilization_delay` — settling time an agent shall wait before relying on the effect, when applicable;
- `retry_policy` — whether and how a failed call may be retried;
- `errors` — the subset of the §10 error catalogue this keyword may raise;
- `exclusive_resources` — resources this keyword locks for the duration of the call.

### 8.2 Consistency with RFDS-002 and RFDS-013

A capability entry's `risk_level` shall use RFDS-002 §16.1's lowercase scale. Where the driver also exposes a richer RFDS-013 capability record for the same operation, `capability_id` shall match the RFDS-013 `Get Capability Model` result exactly; a mismatch shall fail RFDS-013 change-control review.

## 9. State Machine

The `state_machine` section shall reference the RFDS-003 §13.1 canonical connection/session state enum by name rather than defining a competing set of state names. It may add driver-specific sub-states only as documented extensions of a canonical state, and shall label them as such.

## 10. Error Catalogue

Each entry in the `error_catalogue` section shall declare:

- `error_code` — an `RFDS-<DOMAIN>-<NNN>` code per RFDS-007 §8–9;
- `exception_class` — the concrete RFDS-007-aligned exception (e.g., `DriverTimeoutError`);
- `condition` — when this error is raised;
- `retryable` — `yes` or `no`;
- `recovery` — the recommended recovery action or `none`.

These fields shall be sufficient to reconstruct an RFDS-007 §11 formatted message; the error catalogue shall not introduce a parallel message format.

## 11. UNKNOWN Handling

The contract shall state, for each capability where applicable, whether an indeterminate result is reported as an explicit `UNKNOWN` value, a `WARNING`-level diagnostic, or a raised exception. An AI agent shall treat `UNKNOWN` as "not verified" rather than as a pass or a fail, and shall not silently substitute a default value in place of an `UNKNOWN` result during test generation.

## 12. Conformance Rules

An `ai_contract.yaml` is RFDS-017 conformant only when:

1. all mandatory sections in §7 are present;
2. identity fields match the RFDS-015 plugin manifest exactly;
3. every mandatory RFDS-002/RFDS-013 keyword has exactly one capability entry;
4. every `risk_level` uses the RFDS-002 §16.1 scale;
5. every `capability_id` present matches the driver's RFDS-013 capability model;
6. every state name in `state_machine` and in capability pre/postconditions is a valid RFDS-003 §13.1 state or a documented sub-state of one;
7. every error catalogue entry maps to an RFDS-007-aligned exception and a valid `RFDS-<DOMAIN>-<NNN>` code;
8. `ai_contract.lock` validates against the packaged `ai_contract.yaml`;
9. no capability, safety rule, or oracle references hardware behavior that contradicts the driver's RFDS-013 capability model or RFDS-014 configuration schema.

A contract failing any rule above shall not be declared AI-planning ready, per RFDS-015 §21.1.

## 13. Review Checklist

1. Are all mandatory sections present?
2. Do identity fields match the RFDS-015 manifest?
3. Does every mandatory keyword have exactly one capability entry?
4. Do risk levels use the RFDS-002 canonical scale?
5. Do capability IDs match the RFDS-013 capability model?
6. Do state references match RFDS-003's canonical enum?
7. Does the error catalogue map cleanly to RFDS-007 exception classes and error codes?
8. Is `ai_contract.lock` valid against the packaged contract?
9. Are safety rules and oracles consistent with the capability model and configuration schema?
10. Are limitations and UNKNOWN-handling behavior documented?

## 14. Change Control

Whenever a driver's Robot keywords, capability model, exception usage, state model, or configuration schema changes, `ai_contract.yaml` shall be updated and `ai_contract.lock` regenerated in the same revision. A contract left out of sync with the driver's actual behavior shall fail release validation.

## 15. Goal

Provide a single, schema-defined, machine-verifiable description of one driver's behavior — reusing the canonical vocabularies owned by RFDS-002, RFDS-003, RFDS-007, and RFDS-013 — so that an AI agent can plan, select, and generate correct Robot Framework tests without reading source code or guessing at field meanings.
