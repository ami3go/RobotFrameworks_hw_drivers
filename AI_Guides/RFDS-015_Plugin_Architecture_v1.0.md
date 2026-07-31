# RFDS-015 — Plugin Architecture

## Dynamic Driver Loading and Discovery

**Version:** 1.0  
**Document ID:** RFDS-015  
**Status:** Draft project requirement  
**Applies to:** RFDS platform services, all discoverable RFDS driver packages, generic GUIs, Robot Framework orchestration libraries, AI planners, bench managers, validation tools, and release packages

---

## 1. Purpose

This specification defines the RFDS plugin architecture used to discover, identify, validate, select, load, instantiate, and unload installed Robot Framework driver packages without hard-coded driver imports.

The architecture shall allow a generic application to:

1. enumerate installed RFDS drivers;
2. identify each driver by a stable plugin identifier;
3. inspect driver metadata without connecting to hardware;
4. determine whether the driver is compatible with the current RFDS platform and runtime;
5. select a driver by explicit identity, supported model, transport, or declared capabilities;
6. load only the selected driver provider;
7. instantiate a Robot Framework library without performing implicit hardware I/O;
8. keep multiple drivers isolated by stable aliases;
9. report discovery, compatibility, conflict, load, and unload failures consistently;
10. produce machine-readable discovery and loading evidence.

RFDS-015 shall provide dynamic extensibility without weakening RFDS requirements for explicit APIs, configuration validation, capability discovery, AI contracts, safety, protocol conformance, traceability, or release control.

---

## 2. Scope Boundary

### 2.1 In scope

RFDS-015 covers:

- discovery of installed Python distribution packages that advertise RFDS drivers;
- the canonical Python entry-point group used by RFDS drivers;
- stable plugin identifiers and naming rules;
- plugin provider and descriptor contracts;
- a machine-readable plugin manifest;
- metadata-only candidate enumeration;
- isolated provider probing and validation;
- plugin registry construction and refresh;
- compatibility and dependency evaluation;
- deterministic driver resolution;
- explicit loading and instantiation;
- Robot Framework runtime import integration;
- application and GUI integration;
- capability-based selection integration;
- configuration handoff integration;
- AI contract and test-bench contract integration;
- duplicate plugin and version-conflict handling;
- plugin enable, disable, allow-list, block-list, and quarantine behavior;
- unload and cleanup behavior;
- diagnostics, evidence, tests, reviews, and release requirements;
- security boundaries for executable plugin code.

### 2.2 Out of scope

RFDS-015 does not define:

- public device keyword semantics;
- detailed capability taxonomy;
- configuration-field semantics for a specific driver;
- device protocol commands or response parsing;
- transport implementation;
- physical device discovery algorithms for a specific protocol;
- automatic installation of packages from the internet;
- package repository selection or dependency resolution by `pip`;
- remote code download;
- cryptographic signing infrastructure beyond integration with RFDS release evidence;
- complete operating-system process sandboxing;
- physical safety certification;
- bench wiring or resource topology;
- protocol-call conformance testing;
- hot replacement of Python code inside an active process.

These subjects remain governed by the applicable RFDS specifications, device requirements, Python packaging tools, and deployment policy.

---

## 3. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviations require documented justification;
- **may** — permitted implementation choice;
- **plugin** — an installed RFDS driver distribution advertised through the RFDS entry-point group;
- **plugin provider** — the side-effect-free Python object loaded from an entry point and used to return metadata and create driver-library instances;
- **plugin descriptor** — validated machine-readable metadata describing one driver plugin;
- **plugin manifest** — packaged JSON representation of the plugin descriptor;
- **candidate** — an installed entry point found before provider validation;
- **registry** — the current validated collection of discovered plugin records;
- **resolver** — component that selects one plugin from explicit requirements;
- **loader** — component that imports the selected provider and requests an instance;
- **instance** — one created Robot Framework library object or equivalent driver service object;
- **hardware discovery** — active or passive search for connected physical devices; this is separate from installed-plugin discovery;
- **distribution name** — the Python package-distribution name recorded in installed package metadata;
- **import package** — the Python package imported by the runtime;
- **plugin ID** — the stable RFDS identifier used to select a plugin independently of its installed version;
- **plugin API version** — the version of the provider/descriptor contract implemented by the plugin;
- **host** — the RFDS platform, GUI, Robot manager, AI planner, or other application consuming plugins.

---

## 4. Architectural Principles

### 4.1 Discovery is not loading

Enumerating installed plugin entry points shall not instantiate a driver, open a transport, scan the network, enumerate VISA resources, open a serial port, call a vendor SDK, or connect to hardware.

### 4.2 Loading is not connecting

Loading a provider or creating a library instance shall not implicitly connect to a physical device unless a separately approved device-specific architecture requires constructor-time connection and documents the exception. New RFDS drivers shall not use such an exception.

### 4.3 Installed plugins are executable code

A plugin loaded into the host process has the privileges of that process. Entry-point discovery and quarantine are not security sandboxes. Only trusted, reviewed distributions shall be loaded in-process.

### 4.4 Metadata before behavior

The host shall inspect and validate plugin identity, version, compatibility, dependencies, manifest schema, and declared resources before creating a driver instance.

### 4.5 Explicit selection before state-changing use

A state-changing test, GUI workflow, or AI-generated plan shall not select a driver through fuzzy name matching or an unresolved tie. It shall use an explicit plugin ID or an unambiguous, evidence-based resolution result.

### 4.6 Deterministic conflict handling

Duplicate identifiers, incompatible versions, ambiguous candidates, invalid manifests, and missing dependencies shall produce visible registry states. The host shall not silently select whichever plugin is returned first by the operating system or Python runtime.

### 4.7 Import safety

Provider modules, Robot library modules, Libdoc generation, capability inspection, and plugin validation shall be possible without connected hardware.

### 4.8 Source-of-truth separation

The plugin descriptor shall reference authoritative RFDS artifacts rather than duplicating their complete content. Public keywords, capabilities, configuration, AI semantics, bench topology, and protocol vectors retain their own authoritative sources.

### 4.9 Failure isolation

One broken or incompatible plugin shall not prevent other valid plugins from being discovered and used.

### 4.10 Observable lifecycle

Discovery, validation, selection, loading, instantiation, unload, and failure states shall be queryable and recorded in diagnostics.

---

## 5. Logical Architecture

```text
Installed Python distributions
            ↓
importlib.metadata entry-point enumeration
            ↓
Candidate records — no provider import
            ↓
Policy filter — enabled, allow-list, block-list
            ↓
Isolated provider probe with finite timeout
            ↓
Manifest and compatibility validation
            ↓
Validated RFDS plugin registry
            ↓
Explicit ID or deterministic requirements resolver
            ↓
Selected plugin provider
            ↓
Configuration validation and instance request
            ↓
Robot library / Python driver-service instance
            ↓
Explicit Connect keyword or application action
            ↓
Physical device or approved simulator
```

The hardware connection boundary shall remain below plugin discovery, provider validation, and normal library instantiation.

---

## 6. Canonical Discovery Mechanism

### 6.1 Python entry-point group

Every discoverable RFDS driver distribution shall register exactly one entry point per driver provider in this group:

```text
rfds.drivers
```

The group name is owned by the RFDS platform and identifies objects implementing the RFDS driver-plugin provider contract.

### 6.2 Entry-point declaration

A driver shall declare its provider in `pyproject.toml` using equivalent metadata to:

```toml
[project.entry-points."rfds.drivers"]
"keysight.n6700" = "rf_keysight_n6700.plugin:KeysightN6700Plugin"
```

The entry-point name shall equal the plugin ID.

The entry-point value shall reference one provider class or provider factory using the standard Python `module:attribute` form.

### 6.3 Primary discovery API

The platform shall enumerate entry points using the standard-library `importlib.metadata` API or a compatible implementation.

Equivalent behavior:

```python
from importlib.metadata import entry_points

candidates = entry_points(group="rfds.drivers")
```

Legacy `pkg_resources` discovery shall not be the primary implementation for new RFDS platform code.

### 6.4 No arbitrary filesystem scanning by default

The platform shall not recursively import Python files, scan project directories for `library.py`, or execute packages merely because their names start with `rf_`.

An explicitly configured development-directory source may be supported for local engineering use, but it shall:

- be disabled by default in production;
- use an explicit path allow-list;
- produce a source type of `development_path`;
- never outrank an explicitly selected installed plugin;
- apply the same provider, manifest, validation, timeout, and conflict rules;
- be visible in evidence.

### 6.5 No automatic installation

Discovery shall inspect the current Python environment only. A missing driver may be reported with installation guidance, but the plugin manager shall not automatically run `pip`, download packages, modify the environment, or install vendor software.

---

## 7. Plugin Identifier Rules

### 7.1 Format

Each plugin shall have one stable identifier:

```text
<vendor>.<device_family>
```

Rules:

- lowercase ASCII;
- two or more dot-separated segments;
- each segment contains only `a-z`, `0-9`, and `_`;
- no spaces or hyphens;
- no version number;
- no transport name unless the transport defines a genuinely separate driver implementation;
- stable across compatible releases;
- globally unique within the deployed RFDS environment.

Examples:

```text
keysight.n6700
keysight.hp34401a
bk_precision.8500b
openbench.eresistor_matrix
phidgets.interfacekit_relay
votsch.climate_chamber
```

### 7.2 Relationship to project naming

A plugin ID is not required to equal the project folder, Python distribution, import package, or Robot library class.

Example:

| Identity type | Example |
|---|---|
| Plugin ID | `keysight.n6700` |
| Stable ZIP root | `rf_keysight_n6700/` |
| Python distribution | `rf-keysight-n6700` |
| Python import package | `rf_keysight_n6700` |
| Robot library class | `KeysightN6700Library` |

All forms shall be declared in the plugin manifest and checked for consistency.

### 7.3 Identifier ownership

A plugin ID shall not be reused for an unrelated driver or incompatible device family. A replacement implementation for the same declared driver may retain the ID only when compatibility, migration, and ownership are explicitly reviewed.

---

## 8. Required Driver Artifacts

Every discoverable driver package shall add these artifacts to the RFDS-005 structure:

```text
rf_<driver_name>/
├── rf_<driver_name>/
│   ├── plugin.py
│   └── resources/
│       └── plugin_manifest.json
├── tests/
│   └── plugin/
│       ├── test_entry_point.py
│       ├── test_manifest.py
│       ├── test_import_safety.py
│       └── test_provider_lifecycle.py
└── docs/
    └── plugin_integration.md
```

The package shall also contain the `rfds.drivers` entry-point declaration in `pyproject.toml`.

`plugin.py` shall remain small. It shall adapt the driver package to the RFDS plugin-provider contract and shall not duplicate device protocol or Robot keyword logic.

---

## 9. Plugin Manifest

### 9.1 Location and format

The canonical packaged manifest shall be:

```text
rf_<driver_name>/resources/plugin_manifest.json
```

It shall be UTF-8 JSON and shall validate against the RFDS plugin-manifest schema for the declared schema version.

### 9.2 Mandatory fields

The manifest shall contain at least:

- `schema_version`;
- `plugin_api_version`;
- `plugin_id`;
- `driver_name`;
- `display_name`;
- `description`;
- `distribution_name`;
- `distribution_version`;
- `provider`;
- `robot_library_import`;
- `robot_library_class`;
- `supported_device_families`;
- `supported_models`;
- `supported_transports`;
- `capability_descriptor` reference;
- `configuration_schema` reference;
- `ai_contract` reference;
- `documentation` reference;
- `minimum_python`;
- `robot_framework_version` requirement;
- `rfds_platform_version` requirement;
- `optional_dependency_groups`;
- `multi_instance`;
- `thread_safe` declaration;
- `simulation_supported`;
- `hardware_discovery_supported`;
- `load_policy`;
- `deprecation` object;
- `manifest_hash_algorithm`.

### 9.2.1 Resource-reference forms

Descriptor references shall use explicit, machine-readable forms rather than ambiguous relative strings. Permitted reference kinds are:

- `python_object` — a Python `module:attribute` that can be imported without hardware access;
- `package_resource` — a file installed inside an import package and readable through `importlib.resources`;
- `distribution_project_url` — a named project URL from installed distribution metadata;
- `repository_path` — a path available in the full RFDS ZIP or source repository but not guaranteed to exist in a wheel.

Runtime-required schemas and contracts shall use `package_resource`. When RFDS-005 keeps the canonical authored file outside the import package, the release build shall generate a runtime package-resource copy and prove by SHA-256 that it matches the canonical source. Generated copies shall not be edited independently.

A reference object shall contain the fields needed for its kind and should contain a SHA-256 value when it identifies file content.

### 9.3 Example manifest

```json
{
  "schema_version": "1.0",
  "plugin_api_version": "1.0",
  "plugin_id": "keysight.n6700",
  "driver_name": "keysight_n6700",
  "display_name": "Keysight N6700 Power System Driver",
  "description": "RFDS Robot Framework driver for supported Keysight N6700-family mainframes and modules.",
  "distribution_name": "rf-keysight-n6700",
  "distribution_version": "26.3",
  "provider": "rf_keysight_n6700.plugin:KeysightN6700Plugin",
  "robot_library_import": "rf_keysight_n6700.library",
  "robot_library_class": "KeysightN6700Library",
  "supported_device_families": ["keysight_n6700"],
  "supported_models": ["N6700A", "N6700B", "N6705A", "N6705B", "N6705C"],
  "supported_transports": ["visa", "tcpip", "usb", "simulator"],
  "capability_descriptor": {
    "kind": "python_object",
    "value": "rf_keysight_n6700.capabilities:get_capabilities"
  },
  "configuration_schema": {
    "kind": "package_resource",
    "package": "rf_keysight_n6700",
    "path": "resources/config.schema.json",
    "canonical_source": "config/schema.json",
    "sha256": "<digest>"
  },
  "ai_contract": {
    "kind": "package_resource",
    "package": "rf_keysight_n6700",
    "path": "resources/ai_contract.yaml",
    "canonical_source": "ai/ai_contract.yaml",
    "sha256": "<digest>"
  },
  "documentation": {
    "kind": "distribution_project_url",
    "name": "Documentation"
  },
  "minimum_python": ">=3.11",
  "robot_framework_version": ">=7,<9",
  "rfds_platform_version": ">=1,<2",
  "optional_dependency_groups": ["visa", "usb"],
  "multi_instance": true,
  "thread_safe": false,
  "simulation_supported": true,
  "hardware_discovery_supported": true,
  "load_policy": "explicit",
  "deprecation": {
    "deprecated": false,
    "replacement_plugin_id": null,
    "removal_version": null
  },
  "manifest_hash_algorithm": "sha256"
}
```

The example values are illustrative. Device support shall be based on the driver’s reviewed compatibility evidence.

### 9.4 Manifest synchronization

The provider shall return descriptor data equivalent to the packaged manifest. The release build shall fail when the entry point, provider, manifest, installed distribution metadata, capability source, configuration schema, AI contract, documentation, or version files conflict.

### 9.5 No secrets

The manifest shall not contain:

- passwords or tokens;
- private keys;
- personal paths;
- real bench addresses;
- private COM-port assignments;
- customer identifiers;
- device serial numbers from a deployed bench.

---

## 10. Plugin Provider Contract

### 10.1 Required provider operations

A provider shall implement behavior equivalent to:

```python
class DriverPluginProvider:
    @classmethod
    def get_descriptor(cls) -> dict:
        """Return the validated plugin descriptor without hardware I/O."""

    @classmethod
    def validate_environment(cls) -> dict:
        """Return dependency and runtime compatibility information."""

    @classmethod
    def create_library(cls, *, config: dict | None = None) -> object:
        """Create one unconnected Robot Framework library instance."""
```

A provider may additionally implement:

```python
    @classmethod
    def discover_hardware(cls, *, profile: dict) -> list[dict]:
        """Perform an explicit, read-only, bounded hardware search."""

    @classmethod
    def shutdown_provider(cls) -> None:
        """Release provider-level resources when such resources exist."""
```

### 10.2 Provider requirements

`get_descriptor()` shall:

- perform no device I/O;
- open no transport;
- require no credentials;
- return JSON-serializable data;
- complete within the configured provider-probe timeout;
- identify the manifest hash;
- not mutate global application state.

`validate_environment()` shall:

- inspect only local runtime and dependency availability;
- not connect to hardware;
- return explicit `PASS`, `FAIL`, or `WARNING` checks;
- identify missing optional dependencies separately from mandatory dependencies;
- redact sensitive environment values.

`create_library()` shall:

- validate or delegate validation of provided configuration;
- create an unconnected instance;
- avoid global singleton state unless the manifest explicitly declares a singleton and the architecture review approves it;
- preserve causal exceptions;
- return the public Robot library object or an approved service object;
- not silently fall back from requested hardware mode to simulation.

### 10.3 Provider constructor

The provider class constructor shall not require device configuration. The platform should use class methods so descriptor inspection does not require provider instantiation.

### 10.4 Factory return types

The created object shall be one of:

- the canonical Robot Framework library class;
- an approved adapter object containing that library class;
- a remote-library import specification when the plugin explicitly implements an approved remote architecture.

Opaque vendor SDK objects shall not be returned as the public plugin instance.

---

## 11. Source-of-Truth Rules

| Information | Authoritative source | RFDS-015 use |
|---|---|---|
| Plugin ID and provider contract | `plugin_manifest.json` plus `pyproject.toml` entry point | Discovery and loading |
| Installed distribution version | Python distribution metadata | Compatibility and evidence |
| Driver display version | `version.py` under RFDS release rules | Consistency validation |
| Public Robot keywords | `library.py` and generated Libdoc/API manifest | Import and Robot usage |
| Capability truth | RFDS-013 authoritative capability model | Static filtering and runtime confirmation |
| Configuration semantics | RFDS-014 schema and configuration model | Validation and handoff |
| AI operational semantics | RFDS-017 `ai_contract.yaml` | AI planning and safe selection |
| Bench resources and selected drivers | RFDS-018 deployed `system_ai_contract.yaml` | Explicit bench resolution |
| Device protocol behavior | RFDS-019 protocol vectors and driver implementation | Not duplicated in plugin metadata |
| Supported compatibility | `docs/compatibility.md` plus CI/HIL evidence | Manifest validation |
| Release identity and integrity | RFDS release manifest, SBOM, checksums, provenance | Trust and audit |

A conflict between authoritative and derived information shall fail plugin validation or release validation as applicable.

---

## 12. Discovery Levels

### 12.1 Level D0 — Candidate enumeration

The host shall enumerate `rfds.drivers` entry points without calling `EntryPoint.load()`.

For each candidate, it shall record:

- entry-point name;
- entry-point value;
- entry-point group;
- distribution name;
- installed distribution version;
- source location where safely available;
- discovery timestamp.

D0 shall not import the provider module.

### 12.2 Level D1 — Distribution screening

The host shall evaluate available package metadata before provider loading, including:

- distribution version;
- Python-version requirement;
- declared dependencies;
- enabled/disabled policy;
- allow-list or block-list;
- duplicate entry-point names;
- known revoked or quarantined package versions when deployment policy provides such data.

### 12.3 Level D2 — Isolated provider probe

The host shall load and inspect the provider using a finite, isolated probe process or an equivalent reviewed isolation mechanism.

The probe shall:

- import only the selected provider;
- call `get_descriptor()`;
- call `validate_environment()` when configured;
- serialize the result back to the host;
- terminate on timeout;
- capture standard output, standard error, warnings, exception class, exception message, and traceback;
- avoid exposing credentials;
- not inherit active driver sessions;
- not connect to hardware.

A provider-probe failure shall mark only that plugin as unavailable.

### 12.4 Level D3 — Registry validation

The host shall validate:

- manifest schema;
- plugin ID equality with the entry-point name;
- provider path equality with the entry-point value;
- distribution name and version consistency;
- plugin API compatibility;
- RFDS platform compatibility;
- Python and Robot Framework compatibility;
- mandatory dependency availability;
- referenced package resources;
- capability, configuration, and AI-contract references;
- deprecation information;
- duplicate and conflict state.

### 12.5 Level D4 — Optional hardware discovery

Hardware discovery is not part of installed-plugin discovery.

Where supported, it shall be invoked explicitly after D3 and shall:

- be read-only unless a stricter device-specific requirement permits otherwise;
- have a finite timeout;
- use an explicitly supplied search scope;
- avoid changing persistent device configuration;
- record the transport and search profile;
- identify whether each result is verified, probable, or unverified;
- return zero or more candidate device descriptors;
- never connect a driver session automatically;
- never silently choose the first detected device when multiple matches exist.

---

## 13. Registry Model

### 13.1 Registry record

Each registry record shall contain at least:

- plugin ID;
- display name;
- entry-point group, name, and value;
- distribution name and installed version;
- plugin API version;
- manifest schema version;
- manifest hash;
- availability status;
- availability reason;
- compatibility report;
- dependency report;
- supported device families, models, and transports;
- static capability summary or reference;
- configuration-schema reference;
- AI-contract reference;
- deprecation state;
- source type;
- provider-probe duration;
- provider-probe timestamp;
- last validation error;
- runtime load state;
- loaded instance aliases;
- loaded instance count.

### 13.2 Availability statuses

Only these availability statuses are permitted:

- `AVAILABLE` — descriptor and compatibility validation passed;
- `DISABLED` — disabled by explicit configuration or policy;
- `INCOMPATIBLE` — plugin or runtime version requirements are not satisfied;
- `DEPENDENCY_MISSING` — one or more mandatory dependencies are unavailable;
- `CONFLICT` — duplicate or contradictory plugin registrations exist;
- `BROKEN` — import, provider, manifest, or validation failed;
- `QUARANTINED` — blocked because of trust, integrity, security, or administrative policy;
- `DEPRECATED` — usable only under the declared support policy;
- `UNKNOWN` — discovery did not produce sufficient verified information; not loadable by default.

### 13.3 Runtime states

Availability and runtime state shall be separate.

Permitted runtime states:

- `NOT_LOADED`;
- `PROVIDER_LOADED`;
- `INSTANCE_CREATED`;
- `UNLOAD_IN_PROGRESS`;
- `UNLOADED`;
- `LOAD_FAILED`;
- `UNLOAD_FAILED`.

A device connection state such as `CONNECTED` is owned by the driver and shall not be represented as the plugin runtime state.

### 13.4 Registry refresh

Registry refresh shall:

- re-enumerate installed entry points;
- preserve active instance records;
- not unload active instances;
- identify added, removed, updated, and unchanged candidates;
- invalidate cached descriptor data for changed distributions;
- report that process restart is required when active code has changed;
- be deterministic for an unchanged environment.

---

## 14. Compatibility Model

### 14.1 Plugin API version

The RFDS provider contract shall use a `MAJOR.MINOR` plugin API version.

Compatibility rules:

- different major versions are incompatible unless the host explicitly implements an adapter;
- a host shall declare the exact plugin API range it supports;
- a provider outside that range shall be marked `INCOMPATIBLE` before instantiation;
- compatibility shall not be inferred merely because import succeeds.

### 14.2 Runtime requirements

The descriptor shall declare requirements for:

- Python;
- Robot Framework;
- RFDS platform;
- mandatory third-party dependencies;
- optional transport or vendor-SDK dependencies;
- supported operating systems when constrained;
- native architecture when constrained.

### 14.3 Optional dependencies

Missing optional dependencies shall disable only the affected transport or feature where the driver can remain valid without them.

The capability and compatibility result shall show the reduced feature set. A plugin shall not claim a transport or capability whose required dependency is missing.

### 14.4 Unsupported hardware does not make the plugin incompatible

A valid installed plugin may be `AVAILABLE` when no physical device is attached. Hardware availability is a deployment state, not plugin compatibility.

### 14.5 Version selection

The RFDS platform should use one installed version of a distribution per Python environment. Where multiple environments or isolated providers expose more than one version of the same plugin ID, the resolver shall not merge them.

The selected version shall satisfy all declared constraints and shall be visible in the registry and evidence.

---

## 15. Deterministic Plugin Resolution

### 15.1 Resolution inputs

The resolver may accept:

- explicit plugin ID;
- required driver/device family;
- exact model or model pattern;
- required transport;
- required capabilities;
- required simulation support;
- required multi-instance behavior;
- required compatibility range;
- preferred or prohibited vendor;
- deployed bench contract reference;
- configuration profile reference;
- allow-list and block-list policy.

### 15.2 Resolution order

The resolver shall apply this order:

1. exact plugin ID from an explicit request or deployed RFDS-018 bench contract;
2. policy filtering and availability validation;
3. exact device-family and model compatibility;
4. required transport compatibility;
5. required capability compatibility;
6. required runtime and instance behavior;
7. explicit preference order from configuration;
8. version compatibility within the already selected plugin ID.

### 15.3 Ambiguity

When more than one candidate remains equally valid, resolution shall fail with `PluginResolutionAmbiguousError` and return the candidates and unmet tie-break information.

The resolver shall not select by:

- filesystem order;
- entry-point iteration order;
- package installation time;
- lexicographic order alone;
- fuzzy similarity alone;
- highest version across different plugin IDs;
- vendor preference not declared by the user, bench, or policy.

### 15.4 Capability confirmation

Static capability metadata may be used for pre-load filtering. After instance creation, the driver’s runtime RFDS-013 capability result shall be treated as authoritative for the actual installed configuration and optional dependencies.

A mismatch shall fail validation or mark the instance degraded according to the applicable capability specification.

### 15.5 AI selection

An AI agent shall prefer the exact plugin ID declared by the RFDS-018 bench contract. It shall not invent a plugin ID, assume wiring, or substitute a different driver merely because the substitute exposes similar keywords.

---

## 16. Loading and Instantiation

### 16.1 Preconditions

A plugin may be loaded only when:

- its availability status permits loading;
- its plugin API is compatible;
- mandatory dependencies are present;
- no unresolved conflict exists;
- trust and policy checks pass;
- supplied configuration passes schema validation or is empty where permitted;
- requested alias is valid and unused;
- requested instance count complies with the manifest.

### 16.2 Load sequence

The loader shall:

1. obtain the current validated registry record;
2. re-check that installed distribution identity has not changed since validation;
3. load the provider;
4. verify the provider descriptor again in the host context;
5. validate effective configuration through RFDS-014 rules;
6. request one unconnected library instance;
7. verify the returned object type and required metadata;
8. assign the explicit instance alias;
9. register the instance;
10. return an instance descriptor without connecting to hardware.

### 16.3 No silent simulation fallback

When a caller requests hardware mode and creation or connection fails, the loader or driver shall not silently create or connect a simulator. Simulation shall require an explicit configuration profile or explicit plugin/transport choice.

### 16.4 Instance aliases

Each loaded instance shall have a stable alias.

Alias rules:

- unique within the host process or Robot suite scope;
- explicit when more than one instance or plugin is loaded;
- not equal to a reserved manager keyword namespace;
- preserved in evidence;
- used to avoid Robot keyword collisions.

### 16.5 Multi-instance behavior

When `multi_instance` is false, a second instance request shall fail visibly unless the caller explicitly requests the existing instance by alias.

When `multi_instance` is true, every instance shall own independent session state unless the driver documents shared vendor-SDK or process-global resources.

### 16.6 Thread safety

A plugin shall not be treated as thread-safe merely because it supports multiple instances. Thread-safety and concurrency rules shall be explicit in the descriptor, driver capability model, and AI contract.

---

## 17. Robot Framework Integration

### 17.1 Import model

The selected driver shall remain a normal Robot Framework library. RFDS-015 does not require all plugin keywords to be merged into one dynamic mega-library.

A shared RFDS plugin-manager library may expose management keywords such as:

- `Refresh Driver Registry`;
- `List Driver Plugins`;
- `Get Driver Plugin Information`;
- `Validate Driver Plugin`;
- `Resolve Driver Plugin`;
- `Load Driver Plugin`;
- `Unload Driver Plugin`;
- `Get Loaded Driver Plugins`;
- `Export Driver Registry`.

### 17.2 Runtime library import

A Robot-facing plugin manager that loads a driver shall import the selected canonical Robot library using Robot Framework’s supported runtime library-import mechanism or an equivalent reviewed API.

The imported driver shall be registered as a separate Robot library using the requested alias.

Illustrative workflow:

```robot
*** Settings ***
Library    rfds_platform.robot.PluginManagerLibrary

*** Test Cases ***
Load Explicit Power Supply Driver
    Refresh Driver Registry
    ${plugin}=    Resolve Driver Plugin    plugin_id=keysight.n6700
    Load Driver Plugin    ${plugin}[plugin_id]    alias=PSU    config=${PSU_CONFIG}
    PSU.Connect    ${PSU_RESOURCE}
    [Teardown]    Unload Driver Plugin    PSU
```

The exact manager API is governed by its implementation specification. The required behavior in this section is normative.

### 17.3 Keyword collisions

The manager shall not silently merge identically named keywords from multiple drivers.

When multiple driver libraries are present:

- each shall use a distinct Robot library alias;
- the caller should use qualified keyword names such as `PSU.Connect` and `DMM.Connect`;
- alias conflicts shall fail before import;
- no plugin shall overwrite another library registration silently.

### 17.4 Static Robot suites remain supported

RFDS-015 shall not prevent normal static imports in Robot Framework suites. A test may continue to use:

```robot
Library    rf_keysight_n6700.library.KeysightN6700Library
```

Dynamic loading is an additional platform capability, not a mandatory replacement for explicit static imports.

---

## 18. GUI and Application Integration

A generic GUI or application shall use the registry rather than a hard-coded list of driver classes.

The GUI should present:

- plugin display name;
- plugin ID;
- installed version;
- availability status and reason;
- supported device families and transports;
- compatibility state;
- simulation availability;
- deprecation state;
- documentation link;
- explicit validation and load action.

The GUI shall not:

- connect to hardware while merely opening the driver-selection page;
- hide broken, incompatible, or quarantined states;
- show unavailable transports as usable;
- auto-select an ambiguous plugin for a state-changing workflow;
- suppress manifest or dependency validation failures.

A GUI may remember a user’s selected plugin ID in configuration under RFDS-014. It shall revalidate the selection at the next load.

---

## 19. Configuration Integration

### 19.1 Configuration ownership

RFDS-015 shall not redefine driver configuration fields. The plugin manifest shall reference the RFDS-014 configuration schema.

### 19.2 Validation before instance creation

The loader shall validate the plugin-selection and instance-creation portion of configuration before calling `create_library()`.

Device connection settings may be validated by the driver at instance creation or explicit connection, according to RFDS-014 and the driver contract.

### 19.3 Configuration precedence

The effective configuration shall follow the RFDS-014 precedence model. The plugin manager shall not introduce hidden precedence rules.

### 19.4 Secrets

Secrets shall be passed through approved secret sources. They shall not be stored in registry exports, manifests, discovery logs, exception messages, or plugin-selection history.

### 19.5 Effective configuration evidence

Evidence may include a redacted effective configuration hash and non-secret selection fields such as plugin ID, alias, transport profile, and simulator/hardware mode.

---

## 20. Capability Integration

The plugin manifest shall provide only the static capability information needed for discovery and filtering, or a reference to the authoritative RFDS-013 capability source.

After loading:

- the manager shall be able to request runtime driver capabilities;
- runtime capabilities shall reflect installed optional dependencies and active driver mode;
- simulation-only capabilities shall be distinguishable from hardware-qualified capabilities;
- unsupported capabilities shall remain explicit;
- generic applications shall query capabilities instead of branching on Python class names.

Capability metadata changes shall trigger plugin-manifest, AI-contract, documentation, compatibility, and release review as applicable.

---

## 21. RFDS-017 and RFDS-018 Integration

### 21.1 AI Driver Contract

The plugin descriptor shall reference the driver’s RFDS-017 `ai_contract.yaml`.

The plugin manager or AI planner shall verify:

- plugin ID and driver identity agreement;
- driver version agreement;
- public library import agreement;
- capability-source agreement;
- contract-lock validity where available.

A stale or invalid AI contract shall not necessarily prevent manual diagnostic loading, but it shall prevent the plugin from being declared AI-planning ready.

### 21.2 AI Test Bench Contract

A deployed RFDS-018 bench contract should identify required drivers by exact plugin ID and approved version range.

The plugin manager shall provide enough registry data to determine:

- whether every bench-required plugin is installed;
- whether its version is compatible;
- whether required transports and capabilities are available;
- whether the plugin is disabled, broken, conflicting, or quarantined;
- whether an explicit simulator profile is being used.

The plugin manager shall not infer physical wiring or bench ownership from installed packages.

---

## 22. Hardware Discovery Extension

### 22.1 Optional extension

A provider may expose `discover_hardware()` only when the device transport permits a bounded and safe discovery operation.

### 22.2 Required search profile

The caller shall provide a profile defining applicable scope, such as:

- VISA backend and resource pattern;
- serial VID/PID and permitted ports;
- LAN subnet and permitted ports;
- USB VID/PID;
- vendor SDK enumeration mode;
- simulator registry.

The provider shall not scan unrestricted networks or all local interfaces without explicit approval.

### 22.3 Discovery result

Each result shall contain:

- plugin ID;
- transport type;
- resource identifier;
- confidence: `VERIFIED`, `PROBABLE`, or `UNVERIFIED`;
- identity response when safely obtained;
- model and serial number when available;
- firmware when available;
- discovery duration;
- warnings;
- evidence reference.

Sensitive or private resource details shall be redacted in shared reports according to deployment policy.

### 22.4 No implicit connection retention

A hardware-discovery operation shall close all temporary resources before returning. It shall not leave a normal driver session active.

---

## 23. Unload and Cleanup

### 23.1 Unload sequence

The manager shall:

1. locate the instance by alias;
2. block new operations through that manager reference;
3. request driver cleanup using the canonical close-all, disconnect-all, or provider-defined lifecycle operation;
4. preserve cleanup failures;
5. remove the Robot library registration where the integration API safely supports it;
6. remove the instance from the active registry;
7. update runtime state and evidence.

### 23.2 Safety responsibility

The plugin manager shall request cleanup, but the driver remains responsible for device-specific safe teardown and for reporting when safe state could not be confirmed.

### 23.3 Idempotency

Unloading an already unloaded alias should be idempotent when no safety ambiguity exists. An unknown alias shall produce a clear validation failure.

### 23.4 Module unloading

Python module unloading is not guaranteed. RFDS-015 does not require removal of provider or driver modules from `sys.modules`.

### 23.5 Package update while loaded

Installing, removing, or updating a plugin distribution while an instance is active shall require explicit unload and should require host-process restart before the new code is treated as production-valid.

In-process hot code reload shall be disabled by default.

---

## 24. Conflict Handling

### 24.1 Duplicate plugin ID

If two installed entry points advertise the same plugin ID, both shall be marked `CONFLICT` unless deployment policy explicitly pins one exact distribution and version.

### 24.2 Entry-point and manifest mismatch

A mismatch between entry-point name and manifest plugin ID shall mark the candidate `BROKEN`.

### 24.3 Entry-point provider mismatch

A mismatch between entry-point value and manifest provider shall mark the candidate `BROKEN`.

### 24.4 Distribution mismatch

A manifest claiming a different distribution name or version from installed metadata shall fail validation.

### 24.5 Capability conflict

A static descriptor claiming capabilities not present in the authoritative capability model shall fail validation.

### 24.6 Configuration conflict

A missing, invalid, or stale configuration schema reference shall fail plugin validation for configurable drivers.

### 24.7 Active alias conflict

A request to load a second instance using an existing alias shall fail before provider or driver construction.

---

## 25. Error Model

RFDS-015 errors shall integrate with RFDS-007 and distinguish at least:

- `PluginDiscoveryError` — candidate enumeration failed;
- `PluginManifestError` — manifest missing, malformed, or schema-invalid;
- `PluginValidationError` — cross-artifact validation failed;
- `PluginCompatibilityError` — host or runtime requirement is not satisfied;
- `PluginDependencyError` — mandatory dependency is unavailable;
- `PluginConflictError` — duplicate or contradictory registration exists;
- `PluginResolutionError` — no matching plugin exists;
- `PluginResolutionAmbiguousError` — more than one equally valid plugin remains;
- `PluginLoadError` — provider import or load failed;
- `PluginInstantiationError` — library creation failed;
- `PluginConfigurationError` — supplied configuration is invalid;
- `PluginSecurityError` — policy, integrity, or trust check failed;
- `PluginTimeoutError` — probe, validation, discovery, load, or unload exceeded its finite timeout;
- `PluginUnloadError` — cleanup or unload failed;
- `PluginNotFoundError` — requested plugin ID or alias does not exist;
- `PluginStateError` — operation is invalid for the current lifecycle state.

Each RFDS-015 error type listed above shall be implemented as a subclass of the applicable RFDS-007 `DriverError` category rather than as an independent root hierarchy — for example, `PluginConfigurationError` extends `DriverConfigurationError`, `PluginDependencyError` extends `DriverDependencyError`, `PluginTimeoutError` extends `DriverTransportError`, and `PluginStateError` extends `DriverStateError`. RFDS-007 remains the sole normative source for the root exception hierarchy and the mandatory error-message format; RFDS-015 defines only the additional plugin-specific leaf categories and their required fields.

Errors shall include:

- operation;
- plugin ID when known;
- distribution name and version when known;
- current status/state;
- actionable reason;
- underlying exception class where safe;
- evidence or diagnostic reference;
- no secrets;

and shall be formatted per RFDS-007 §11.

One plugin failure shall not be reported as a successful registry refresh.

---

## 26. Security and Trust Requirements

### 26.1 Trust boundary

Plugin distributions shall be treated as executable dependencies, not passive data.

### 26.2 Allow-list and block-list

Production deployments should support:

- allowed plugin IDs;
- allowed distributions;
- allowed versions or version ranges;
- prohibited plugin IDs or versions;
- quarantined release hashes;
- approved source repositories or internal package indexes.

### 26.3 Integrity evidence

Where release integrity data is available, validation should compare the installed distribution or deployment artifact against:

- RFDS release manifest;
- SHA-256 checksums;
- SBOM;
- provenance or attestation;
- approved dependency lock.

A failed required integrity check shall result in `QUARANTINED` or `BROKEN`, not a warning-only load.

### 26.4 Isolated probe

Provider probing shall use a separate process by default in production-capable platform implementations so that import failures, `sys.exit`, deadlocks, or crashes do not terminate the host.

### 26.5 Finite resource use

The probe shall enforce configurable limits for:

- wall-clock duration;
- output size;
- returned descriptor size;
- child-process count where enforceable;
- memory where the deployment supports limits.

### 26.6 No security claim from quarantine alone

Marking a plugin `QUARANTINED` prevents normal loading but does not remove malicious code from the environment. Package removal and host remediation remain deployment responsibilities.

### 26.7 Path loading

Arbitrary user-supplied Python paths shall not be loadable in production mode unless an approved development or laboratory policy explicitly permits them.

---

## 27. Performance and Caching

### 27.1 Discovery cache

The host may cache validated registry records using an environment fingerprint containing at least:

- Python executable identity;
- Python version;
- environment path;
- distribution name and version set;
- entry-point group records;
- plugin manifest hash;
- host plugin API version;
- applicable allow/block policy hash.

### 27.2 Cache invalidation

The cache shall be invalidated when any fingerprint input changes or when the user requests a forced refresh.

### 27.3 Cache trust

Cached records shall not bypass current trust policy, distribution identity checks, or explicit quarantine rules.

### 27.4 Timeouts

All plugin operations shall have finite timeouts.

Recommended defaults:

- candidate enumeration: 10 seconds total;
- provider probe: 5 seconds per plugin;
- environment validation: 10 seconds per plugin;
- explicit hardware discovery: device-specific, finite, and shown to the caller;
- unload cleanup: driver-specific, finite, and interruptible where practical.

Different values may be configured, but unbounded waits are prohibited.

### 27.5 Large environments

Discovery should support lazy provider probing so a GUI can first show D0 candidates and validate selected or visible candidates without blocking on every installed plugin.

A release-validation workflow shall still perform full validation of the driver being released.

---

## 28. Diagnostics and Evidence

### 28.1 Registry export

The host shall support a machine-readable registry export containing validated non-secret metadata.

Plugin validation evidence shall follow the RFDS-008 evidence envelope, manifest, and redaction rules; the `results/plugin_validation/<timestamp>/` layout in §28.3 is a plugin-manager-specific view and should be reachable from, or nested under, the RFDS-008 §11 canonical result root for the same run.

### 28.2 Required evidence

A plugin validation run shall record at least:

- timestamp;
- operating system;
- Python executable and version;
- Robot Framework version when installed;
- RFDS platform version;
- entry-point group;
- discovered candidate count;
- validated plugin count;
- status counts;
- distribution names and versions;
- plugin IDs;
- manifest hashes;
- compatibility results;
- dependency results;
- conflicts;
- probe durations;
- failures and reasons;
- active instance aliases where applicable;
- redacted effective policy.

### 28.3 Recommended result layout

```text
results/plugin_validation/<timestamp>/
├── registry.json
├── discovery_candidates.json
├── compatibility_report.json
├── dependency_report.json
├── conflicts.json
├── probe_results.json
├── environment.json
├── plugin_validation_summary.md
└── plugin_manager.log
```

### 28.4 Trace correlation

Load, instance creation, hardware discovery, and unload records shall include a correlation ID so GUI logs, Robot reports, driver diagnostics, and plugin evidence can be related.

### 28.5 Secret redaction

Registry and evidence exports shall redact credentials, tokens, private keys, and sensitive connection information according to RFDS logging requirements.

---

## 29. Required Tests

### 29.1 Driver-package tests

Each driver shall test:

- `rfds.drivers` entry point exists;
- entry-point name equals plugin ID;
- entry-point value resolves to the intended provider;
- provider imports without hardware access;
- Robot library imports without hardware access;
- manifest exists and validates;
- provider descriptor equals manifest data;
- installed/distribution version consistency;
- provider API version compatibility;
- referenced capability, configuration, AI-contract, and documentation resources exist;
- `get_descriptor()` returns JSON-serializable data;
- `validate_environment()` reports mandatory and optional dependencies correctly;
- `create_library()` returns the canonical unconnected library type;
- no silent simulation fallback occurs;
- multiple instances follow the declared policy;
- cleanup is deterministic and finite;
- provider and library import do not enumerate or open hardware;
- broken optional dependencies reduce only the affected capabilities;
- manifest drift causes test failure.

### 29.2 Platform-manager tests

The RFDS platform plugin manager shall test:

- empty environment;
- one valid plugin;
- multiple valid plugins;
- duplicate plugin ID;
- malformed entry point;
- missing distribution metadata;
- provider import exception;
- provider timeout;
- provider process crash;
- malformed descriptor;
- manifest mismatch;
- unsupported plugin API major version;
- incompatible Python or Robot version;
- missing mandatory dependency;
- missing optional dependency;
- disabled plugin;
- quarantined plugin;
- explicit resolution;
- capability/model/transport resolution;
- ambiguous resolution;
- alias conflict;
- single-instance enforcement;
- multi-instance behavior;
- load failure isolation;
- unload cleanup failure;
- cache invalidation;
- refresh after install/remove/update simulation;
- redaction of secrets;
- deterministic registry export.

### 29.3 Robot acceptance tests

Robot tests shall verify, using deterministic fake plugins:

- registry refresh;
- plugin listing;
- explicit plugin resolution;
- dynamic library import;
- qualified keyword call through an alias;
- two plugins with common keyword names remain isolated;
- unload behavior;
- clear failure for an unavailable or ambiguous plugin.

### 29.4 Import-safety test environment

Import-safety tests should block or instrument common hardware-access mechanisms, including applicable socket, serial, VISA, USB, vendor-SDK, and subprocess calls, and fail when provider or library import attempts prohibited access.

### 29.5 Real-driver validation

A released driver shall pass plugin discovery and load validation from its built wheel in a clean environment. Validation against only the source checkout is insufficient.

---

## 30. Conformance Levels

### Level P0 — Entry-point registration

- distribution installs;
- entry point is present;
- entry-point identity is correct.

### Level P1 — Manifest and provider validation

- provider imports safely;
- descriptor and manifest validate;
- cross-artifact identity and version checks pass.

### Level P2 — Compatibility and registry integration

- host compatibility passes;
- dependencies are classified correctly;
- plugin appears in the registry with the expected status.

### Level P3 — Load and instance creation

- selected provider loads;
- valid configuration is accepted;
- canonical unconnected library instance is created;
- alias registration succeeds.

### Level P4 — Robot and application integration

- runtime Robot import succeeds;
- qualified keyword access works;
- GUI/application metadata is complete;
- capability and configuration references resolve.

### Level P5 — Cleanup, conflict, and failure isolation

- unload is finite;
- cleanup evidence is produced;
- conflicts are deterministic;
- a broken plugin does not break other plugins;
- security and quarantine policy is enforced.

---

## 31. Acceptance Criteria

An RFDS driver passes RFDS-015 only when:

1. its built distribution advertises exactly the intended `rfds.drivers` entry point;
2. the plugin ID follows the required stable naming rules;
3. the entry-point name, provider path, manifest, distribution metadata, and version sources agree;
4. provider and Robot library imports perform no hardware access;
5. the provider probe completes within the finite timeout;
6. the manifest validates against the approved schema;
7. plugin API, Python, Robot Framework, RFDS platform, and dependency compatibility are evaluated before instance creation;
8. the plugin appears in the registry with a deterministic status;
9. invalid or conflicting plugins cannot be selected silently;
10. explicit resolution by plugin ID works;
11. model, transport, and capability filtering is deterministic;
12. ambiguous resolution fails visibly;
13. valid configuration is checked before library creation;
14. `create_library()` returns the canonical unconnected library instance;
15. requested hardware mode never silently falls back to simulation;
16. multiple instances and aliases follow the descriptor policy;
17. Robot Framework runtime import works using an explicit alias;
18. common keyword names from multiple drivers remain isolated;
19. unload requests deterministic driver cleanup and reports incomplete cleanup;
20. one plugin’s failure does not prevent other valid plugins from being used;
21. registry and validation evidence is generated without secrets;
22. capability, configuration, RFDS-017, RFDS-018, and RFDS-019 references remain consistent with their authoritative sources;
23. clean-wheel plugin tests pass;
24. documentation, history, review, traceability, and release metadata are updated for plugin changes;
25. no Critical or unresolved Major RFDS-015 finding remains.

---

## 32. Failure Conditions

RFDS-015 shall fail for a driver or platform implementation when:

- no canonical entry point is packaged;
- discovery depends on hard-coded imports or uncontrolled filesystem scanning;
- plugin ID is unstable, versioned, invalid, or duplicated;
- provider import performs hardware I/O;
- library import performs hardware I/O;
- provider probe can block indefinitely;
- manifest is missing, invalid, or stale;
- manifest identity contradicts installed metadata;
- a provider claims a different plugin ID than its entry point;
- required compatibility is not evaluated;
- missing mandatory dependencies are ignored;
- a broken plugin crashes the registry refresh;
- conflict resolution depends on discovery order;
- an ambiguous selection is silently resolved;
- loading implicitly connects to hardware;
- requested hardware mode silently becomes simulation;
- aliases collide or keywords are merged without explicit namespacing;
- single-instance policy is bypassed;
- unload hides cleanup failure;
- active code is hot-reloaded without approved behavior;
- untrusted arbitrary paths are loaded in production mode;
- secrets appear in manifests, registry exports, logs, or errors;
- registry evidence is missing;
- clean-installed wheel behavior differs from source-checkout validation;
- a plugin change is released without corresponding tests, documentation, history, and review.

---

## 33. Change Control

Whenever any of the following changes, the same driver revision shall update and validate all affected artifacts:

- plugin ID;
- entry-point name or value;
- provider class;
- plugin API version;
- manifest schema version;
- distribution name;
- Robot import package or class;
- supported models or transports;
- capability reference or static summary;
- configuration-schema reference;
- AI-contract reference;
- multi-instance or thread-safety declaration;
- hardware-discovery support;
- dependency or compatibility requirements;
- deprecation state;
- load or unload behavior;
- simulation policy;
- security or trust policy.

A plugin ID change is a breaking integration change and requires a migration path, compatibility review, history entry, and RFDS-018 bench-contract update where used.

A provider or entry-point change without RFDS-015 test and manifest updates shall fail release validation.

---

## 34. Integration with the RFDS Lifecycle

### Gate 1 — Architecture and skeleton

Deliver:

- plugin ID decision;
- `plugin.py` skeleton;
- manifest skeleton;
- entry-point declaration;
- plugin architecture documentation;
- unit-test skeleton;
- no-hardware import proof.

### Gate 2 — Core implementation

Deliver:

- complete descriptor;
- provider environment validation;
- library factory;
- explicit configuration handoff;
- registry integration tests;
- initial dynamic Robot import example.

### Gate 3 — Extended features

Deliver as applicable:

- capability-based resolution;
- optional hardware discovery;
- multi-instance support;
- optional dependency degradation;
- GUI metadata integration;
- AI and bench-contract validation.

### Gate 4 — Tests and documentation

Deliver:

- full RFDS-015 test matrix;
- clean-wheel validation;
- Robot acceptance tests;
- plugin integration guide;
- GitHub Pages content;
- compatibility and security reviews;
- generated registry evidence.

### Gate 5 — Review and release

Deliver:

- final plugin manifest;
- final entry-point and wheel validation;
- code, architecture, API, documentation, security, compatibility, and release reviews;
- updated history and traceability;
- release manifest, SBOM, checksums, and provenance where required;
- correctly named RFDS ZIP package.

---

## 35. Review Checklist

1. Is the plugin ID valid, stable, and unversioned?
2. Does `pyproject.toml` register the provider in `rfds.drivers`?
3. Does the entry-point name equal the manifest plugin ID?
4. Does the entry-point value equal the manifest provider path?
5. Does installed distribution metadata match the manifest?
6. Does provider import avoid hardware and network access?
7. Does Robot library import avoid hardware and network access?
8. Is provider probing isolated and time-bounded?
9. Does the manifest validate against the approved schema?
10. Are capability, configuration, AI-contract, and documentation references valid?
11. Are Python, Robot Framework, RFDS platform, and dependency requirements explicit?
12. Are missing optional dependencies reflected in capabilities?
13. Are duplicate IDs and ambiguous resolution handled deterministically?
14. Is explicit plugin-ID resolution supported?
15. Does library creation remain unconnected?
16. Is hardware-to-simulator fallback always explicit?
17. Are instance aliases unique and used for Robot keyword qualification?
18. Does multi-instance behavior match the descriptor?
19. Are thread-safety limitations explicit?
20. Is hardware discovery separate, explicit, read-only, scoped, and finite?
21. Does unload request safe driver cleanup and preserve failures?
22. Are arbitrary-path and untrusted-plugin policies explicit?
23. Are manifests, logs, registry exports, and errors free of secrets?
24. Does one broken plugin leave other plugins usable?
25. Do clean-wheel tests pass?
26. Are registry and validation reports generated?
27. Are README, GitHub Pages, guide, history, review, and traceability current?
28. Are plugin changes represented in release integrity evidence?
29. Are RFDS-013, RFDS-014, RFDS-017, RFDS-018, and RFDS-019 integrations consistent?
30. Are all acceptance criteria satisfied?

---

## 36. Minimum Definition of Done

RFDS-015 implementation is complete for a driver when:

- the driver is discoverable from its installed wheel through `rfds.drivers`;
- the candidate can be enumerated without provider import;
- the provider can be probed safely in isolation;
- the plugin manifest and all identity/version checks pass;
- runtime and dependency compatibility are reported correctly;
- the driver appears in the registry with deterministic metadata and status;
- explicit and capability-based resolution tests pass;
- an unconnected Robot library instance can be created with validated configuration;
- Robot runtime import with an explicit alias passes;
- conflict, ambiguity, dependency, timeout, broken-provider, and unload tests pass;
- registry and evidence exports are generated;
- no mandatory behavior remains `NOT TESTED`;
- documentation, history, review, and traceability are current;
- the release package passes all applicable RFDS gates.

---

## 37. Goal

Provide a deterministic and production-oriented mechanism by which RFDS applications, Robot Framework suites, GUIs, and AI planners can discover installed drivers, validate what they are, select the correct implementation, load it without hidden hardware activity, and preserve safety, compatibility, isolation, and traceable evidence throughout the plugin lifecycle.

---

## Appendix A — Platform Provider Interface Example

```python
from __future__ import annotations

from typing import Any, ClassVar


class KeysightN6700Plugin:
    """RFDS plugin provider. Importing this class must not access hardware."""

    PLUGIN_ID: ClassVar[str] = "keysight.n6700"

    @classmethod
    def get_descriptor(cls) -> dict[str, Any]:
        from .manifest import load_plugin_manifest

        descriptor = load_plugin_manifest()
        if descriptor["plugin_id"] != cls.PLUGIN_ID:
            raise ValueError("Plugin ID does not match provider identity")
        return descriptor

    @classmethod
    def validate_environment(cls) -> dict[str, Any]:
        return {
            "status": "PASS",
            "checks": [
                {"name": "python", "status": "PASS"},
                {"name": "robotframework", "status": "PASS"},
                {"name": "visa", "status": "WARNING", "optional": True},
            ],
        }

    @classmethod
    def create_library(cls, *, config: dict[str, Any] | None = None) -> object:
        from .library import KeysightN6700Library

        return KeysightN6700Library(config=config)
```

This appendix is illustrative. The approved platform package shall provide the shared types, schemas, validators, exceptions, and lifecycle utilities.

---

## Appendix B — Registry Record Example

```json
{
  "plugin_id": "keysight.n6700",
  "display_name": "Keysight N6700 Power System Driver",
  "distribution": {
    "name": "rf-keysight-n6700",
    "version": "26.3"
  },
  "entry_point": {
    "group": "rfds.drivers",
    "name": "keysight.n6700",
    "value": "rf_keysight_n6700.plugin:KeysightN6700Plugin"
  },
  "availability": {
    "status": "AVAILABLE",
    "reason": null
  },
  "runtime_state": "NOT_LOADED",
  "plugin_api_version": "1.0",
  "manifest_hash": "sha256:<digest>",
  "supported_transports": ["visa", "tcpip", "usb", "simulator"],
  "simulation_supported": true,
  "multi_instance": true,
  "loaded_aliases": [],
  "validation": {
    "probe_duration_ms": 84,
    "validated_at": "2026-07-26T12:00:00Z"
  }
}
```

---

## Appendix C — Technical Basis

This specification uses Python distribution entry points as the canonical installed-plugin advertisement mechanism and `importlib.metadata` as the standard runtime discovery API. It also preserves Robot Framework’s normal model of importing libraries by module/class and permits runtime library import for explicitly selected plugins.

Reference specifications and documentation:

- Python Packaging User Guide — Entry points specification: https://packaging.python.org/en/latest/specifications/entry-points/
- Python Standard Library — `importlib.metadata`: https://docs.python.org/3/library/importlib.metadata.html
- Robot Framework User Guide — using and creating test libraries: https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html

---

## Appendix D — Initial Version 1.0 Decisions

1. `rfds.drivers` is the sole canonical installed-driver entry-point group.
2. Entry-point enumeration is separated from provider import.
3. Provider probing is isolated and time-bounded.
4. Provider and Robot library imports shall not access hardware.
5. Driver creation shall produce an unconnected instance.
6. Hardware discovery is optional, explicit, scoped, read-only, and separate from plugin discovery.
7. Exact plugin IDs and explicit aliases are preferred for Robot and bench integration.
8. Ambiguous resolution fails rather than choosing by discovery order.
9. Dynamic loading does not replace normal static Robot Framework library imports.
10. In-process hot code reload is not required and is disabled by default.
