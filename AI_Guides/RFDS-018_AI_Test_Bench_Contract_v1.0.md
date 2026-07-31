# RFDS-018 — AI Test Bench Contract Specification

**Version:** 1.0 (Draft)
**Document ID:** RFDS-018
**Status:** Draft project requirement
**Applies to:** deployed multi-instrument test benches, AI planners, RFDS-015 plugin managers, and RFDS-019 protocol conformance tooling

---

## 1. Purpose

RFDS-018 defines the complete hardware test-environment contract for one deployed bench. It combines multiple RFDS-017 driver contracts into a single coherent laboratory model — physical topology, shared resources, and safety constraints — that an AI planner can use to generate end-to-end, multi-instrument Robot Framework validation plans.

RFDS-018 is the sole normative source for the structure and required fields of `system_ai_contract.yaml`.

## 2. Scope Boundary

### 2.1 In scope

- deployed-bench identification of required drivers by exact plugin ID and approved version range;
- physical topology, wiring, and shared-resource declarations;
- bench-wide safety zones, constraints, and scheduling rules;
- requirement-to-driver coverage mapping;
- reusable multi-driver test templates.

### 2.2 Out of scope

RFDS-018 does not define:

- single-driver capability, error, or state semantics (owned by RFDS-013, RFDS-007, RFDS-003, and expressed per-driver in RFDS-017);
- plugin discovery, loading, or the plugin manifest (owned by RFDS-015);
- device configuration schema (owned by RFDS-014);
- protocol-level conformance vectors (owned by RFDS-019).

A `system_ai_contract.yaml` shall reference driver identity and capability information rather than duplicating it.

## 3. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviations require documented justification;
- **may** — permitted implementation choice;
- **bench contract** — the `system_ai_contract.yaml` document described by this specification;
- **deployed driver** — a plugin instance the bench contract declares as installed and wired, identified by exact RFDS-015 plugin ID.

## 4. Normative References

- RFDS-003 — BaseInstrumentLibrary: Common Base Class Design
- RFDS-007 — Error and Exception Standard
- RFDS-013 — Capability Model
- RFDS-014 — Driver Configuration Model Specification
- RFDS-015 — Plugin Architecture
- RFDS-017 — AI Driver Contract Specification
- RFDS-019 — Robot Framework Driver Call and Protocol Conformance Test Specification

## 5. Required File

```text
system_ai_contract.yaml
```

The bench contract shall live at the deployment/bench level, outside any single driver's package tree. A bench deployment may additionally provide `config/hil_resources.example.yaml` (per RFDS-005 §17 and RFDS-014 §6.1) as a starting template for the resource values referenced by this contract; that file remains YAML by design and is a distinct RFDS-018 artifact, not part of the RFDS-014 configuration schema.

## 6. Mandatory Sections

### 6.1 Available Drivers

Shall list each deployed driver by:

- `plugin_id` — the exact RFDS-015 plugin identifier (no fuzzy matching);
- `approved_version_range` — the compatible distribution version range;
- `alias` — the stable Robot Framework instance alias per RFDS-015 §16.4;
- `ai_contract_reference` — a pointer to that driver's RFDS-017 `ai_contract.yaml`.

Per RFDS-015 §21.2 and §15.5, an AI planner shall prefer this exact plugin ID and shall not invent a plugin ID or substitute a different driver merely because it exposes similar keywords.

### 6.2 Physical Topology

Shall describe wiring between instruments, relay matrices, DUT interfaces, and measurement points, sufficient for a planner to determine which physical path connects a given source to a given measurement.

### 6.3 Shared Resources

Shall declare USB, VISA, LAN, and serial ports, power rails, fixtures, and any other exclusive resources, using identifiers consistent with each driver's RFDS-014 configuration and RFDS-017 `exclusive_resources` declarations.

### 6.4 Signal Graph

Shall define producers and consumers of electrical, digital, and environmental signals so a planner can trace a signal from source to sink across multiple drivers.

### 6.5 Preferred Measurement Sources

Shall specify which instrument should be preferred for each measurable quantity when more than one deployed driver could measure it.

### 6.6 Requirement Coverage

Shall map system requirements to available drivers and to the RFDS-017 verification objectives that satisfy them.

### 6.7 Test Templates

Shall provide reusable multi-driver workflows (for example, PSU → Relay → DUT → DMM), expressed in terms of driver aliases and RFDS-013 capability IDs rather than hard-coded keyword sequences, so templates remain valid across compatible driver versions.

### 6.8 Bench Constraints

Shall declare:

- operator actions required before, during, or after automated sequences;
- safety zones and the drivers/resources each zone covers;
- maximum simultaneous operations;
- environmental limits (temperature, humidity, and similar).

### 6.9 Scheduling Rules

Shall declare:

- resource conflicts between drivers sharing a physical resource;
- required driver ordering;
- stabilization rules, consistent with each driver's RFDS-017 `stabilization_delay` values;
- parallel execution limits.

### 6.10 Global Safety

Shall declare bench-wide forbidden sequences and the emergency shutdown workflow, expressed in terms of driver aliases and keywords so it is directly executable.

## 7. Consistency Requirements

1. Every `plugin_id` in §6.1 shall exist and be `AVAILABLE` in the RFDS-015 registry at plan time; an unavailable, disabled, quarantined, or version-incompatible driver shall fail bench-contract validation rather than being silently skipped.
2. Every resource named in §6.3 and used by a test template in §6.7 shall be declared exactly once as owned by one or more explicitly listed drivers; unresolved resource references shall fail validation.
3. Risk levels, states, and error references used within bench constraints and safety rules shall use the canonical vocabularies of RFDS-002 §16.1, RFDS-003 §13.1, and RFDS-007 respectively, as already expressed in each referenced driver's RFDS-017 contract.
4. An AI-generated plan shall not violate a Global Safety forbidden sequence even when individual driver-level safety rules would otherwise permit the intermediate steps.

## 8. Review Checklist

1. Are all mandatory sections present?
2. Does every listed driver use an exact RFDS-015 plugin ID and version range?
3. Are shared resources declared without ambiguity or duplication?
4. Do test templates reference driver aliases and RFDS-013 capability IDs rather than hard-coded assumptions?
5. Are safety zones, constraints, and scheduling rules bench-wide and internally consistent?
6. Is the Global Safety section directly executable (aliases and keywords, not prose only)?
7. Does requirement coverage trace to real RFDS-017 verification objectives?

## 9. Change Control

Whenever a bench's wiring, deployed driver set, resource allocation, or safety constraints change, `system_ai_contract.yaml` shall be updated in the same change and revalidated against each deployed driver's current RFDS-015 registry status and RFDS-017 contract.

## 10. Goal

Enable an AI agent to automatically synthesize complete, multi-instrument Robot Framework test plans by combining RFDS-017 single-driver contracts with one authoritative, machine-readable laboratory description — without inventing drivers, resources, or safety exceptions not present in the deployed bench.
