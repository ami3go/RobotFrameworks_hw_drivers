# RFDS-014 — Driver Configuration Model Specification

**Document ID:** RFDS-014  
**Version:** 1.0  
**Status:** Draft Project Standard (Normative)  
**Applies to:** All RFDS Robot Framework driver packages, shared configuration components, generic operator applications, AI-assisted test generation, and release validation

---

## 1. Purpose

This specification defines the common configuration model for RFDS Robot Framework drivers.

It standardizes how a driver shall:

1. describe its configurable settings;
2. validate configuration using JSON Schema;
3. import and export configuration as JSON;
4. combine defaults, profiles, environment values, constructor arguments, and runtime overrides;
5. persist named user profiles safely;
6. migrate configuration between compatible schema revisions;
7. protect secrets and safety-critical settings;
8. report configuration state in a machine-readable form;
9. expose configuration operations consistently to Robot Framework, Python applications, generic GUIs, and AI agents;
10. preserve compatibility and traceability across driver releases.

The goal is to make driver configuration deterministic, portable, inspectable, safe, and independent of ad-hoc local files or undocumented constructor behaviour.

---

## 2. Scope Boundary

### 2.1 In scope

RFDS-014 covers host-side driver configuration, including:

- canonical JSON configuration documents;
- driver configuration JSON Schema;
- packaged safe defaults;
- example profiles;
- named user profiles;
- configuration discovery;
- validation and normalization;
- import and export;
- explicit load, apply, save, and reset operations;
- configuration precedence;
- deterministic merge rules;
- runtime and persistent scopes;
- schema and profile versioning;
- migration between configuration schema revisions;
- atomic file replacement;
- corruption recovery and last-known-good handling;
- concurrent access and file locking;
- secret references and redaction;
- safety-sensitive configuration controls;
- configuration diagnostics and evidence;
- standard Robot Framework configuration keywords;
- integration with RFDS capability, AI-contract, GUI, test, and release requirements.

### 2.2 Out of scope

RFDS-014 does not define:

- vendor protocol commands used to configure a physical device;
- device calibration data or calibration certificates;
- waveform, trace, image, measurement, or test-result storage;
- RFDS-018 bench topology, DUT wiring, relay routing, or shared-resource assignments;
- passwords, tokens, private keys, or credentials storage mechanisms;
- general application preferences unrelated to driver operation;
- operating-system credential vault implementation;
- database-backed fleet configuration;
- remote cloud configuration services;
- arbitrary code execution from configuration;
- automatic discovery of unsafe hardware limits;
- implicit persistence of device state across power cycles.

A setting that changes physical-device non-volatile memory remains a device-facing operation. It shall be declared in RFDS-017, safety-classified, and tested through the applicable RFDS-019 protocol vectors. RFDS-014 only governs the host-side representation and authorization of that operation.

---

## 3. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviations require reviewed justification;
- **may** — permitted implementation choice;
- **configuration document** — a complete RFDS-014 JSON object representing one driver profile;
- **schema** — the JSON Schema that defines valid configuration structure, types, constraints, defaults, and RFDS annotations;
- **profile** — a named configuration document intended for repeatable use;
- **effective configuration** — the fully resolved configuration after defaults and all approved override layers are applied;
- **runtime override** — a non-persistent value applied to the current library instance or named session;
- **persistent profile** — a profile explicitly saved to user or system configuration storage;
- **package default** — the read-only safe configuration distributed with the driver;
- **semantic configuration** — fields that affect driver behaviour;
- **metadata** — non-behavioural fields such as description, export time, and migration history;
- **sensitive value** — a credential, token, private identifier, or other value that shall not appear in normal logs or exports;
- **secret reference** — an indirect reference to a secret stored outside the configuration document;
- **cold setting** — a setting applied on the next connection or driver restart;
- **hot setting** — a setting that may be applied to an active driver session;
- **device-persistent setting** — a setting whose application writes non-volatile state to the physical device;
- **canonical JSON** — normalized JSON produced according to Section 10;
- **configuration fingerprint** — a digest of canonical semantic configuration used to identify the effective configuration.

---

## 4. Design Principles

### 4.1 JSON is the interchange format

Every RFDS driver shall support JSON configuration import and export without optional dependencies.

YAML, TOML, environment-variable files, Robot variable files, and GUI forms may be supported as authoring or integration conveniences, but they shall be converted into the RFDS-014 data model before validation or application.

JSON export shall be sufficient to reconstruct the same semantic configuration on a compatible installation.

### 4.2 Validation precedes application

A configuration shall be parsed, structurally validated, semantically validated, normalized, safety-checked, and compatibility-checked before any value is applied.

Validation failure shall not partially change the active configuration, persistent profile, transport session, or physical device.

### 4.3 Explicit persistence

Changing a runtime value shall not persist it automatically.

Persistence shall occur only through an explicit save operation or an explicitly documented application action whose user intent is unambiguous.

### 4.4 Safe defaults

Package defaults shall:

- contain no credentials;
- contain no private bench addresses;
- contain no personal COM-port assignments;
- contain no machine-specific absolute paths;
- select simulation or disconnected operation where appropriate;
- keep outputs, relays, loads, environmental actuators, and other energy-controlling functions disabled;
- use finite timeouts;
- avoid device resets, calibration writes, firmware writes, and non-volatile device changes.

### 4.5 Deterministic resolution

Given identical driver version, schema version, input documents, environment values, constructor arguments, and runtime overrides, the effective configuration and fingerprint shall be identical.

### 4.6 No silent fallback after invalid configuration

When an explicitly selected profile exists but is invalid, incompatible, unreadable, or corrupt, the driver shall fail configuration loading and remain disconnected or in its existing safe state.

It shall not silently substitute package defaults, another profile, simulation, another device address, or a previously used profile.

A missing optional profile may permit package defaults only when no explicit profile was requested.

### 4.7 Separation of configuration domains

Host-side driver configuration, physical-device persistent state, bench topology, calibration assets, and test evidence shall remain separate data domains.

### 4.8 Machine-readable outcomes

Configuration operations shall return structured Robot Framework-compatible dictionaries and lists. Success shall not be represented only by log text.

### 4.9 Portable profiles

Exported profiles should avoid host-specific paths and resource identifiers where practical. Machine-specific values shall be isolated, parameterized, or expressed as environment references.

### 4.10 Traceable change

Any change to configuration keys, defaults, validation rules, merge behaviour, persistence, or safety classification shall update schema, examples, tests, documentation, AI metadata, history, and review evidence in the same driver revision.

---

## 5. Configuration Domains

RFDS implementations shall classify configuration into the following domains.

| Domain | Owner | RFDS-014 treatment |
|---|---|---|
| Driver package defaults | Driver package | Read-only canonical baseline |
| Host transport settings | Driver instance or session | Importable, exportable, and persistable |
| Driver timing and retry policy | Driver instance or session | Importable, exportable, and persistable |
| Driver logging and diagnostics settings | Driver instance or session | Importable, exportable, and persistable |
| Simulation or replay settings | Driver instance or session | Importable, exportable, and explicit |
| Driver safety limits | Driver or approved bench profile | Importable with elevated validation and no unsafe default |
| Device model-specific settings | Driver instance or session | Importable when represented by schema |
| Physical-device volatile state | Physical device | Applied only through declared driver capabilities |
| Physical-device non-volatile state | Physical device | Never written merely because a profile was loaded |
| Bench wiring and resource assignments | RFDS-018 bench contract | Referenced, not duplicated as driver truth |
| Calibration data | Device-specific calibration subsystem | Separate schema and lifecycle |
| Credentials and secrets | External secret provider | Referenced, not stored as plaintext |
| Test variables and acceptance limits | Test suite or bench profile | Not silently persisted as driver configuration |
| Measurements, logs, and reports | Evidence subsystem | Not configuration |

A field shall not be placed in driver configuration merely because it is convenient for one test suite.

---

## 6. Mandatory Package Artifacts

Every RFDS-014-conformant driver shall provide:

```text
rf_<driver_name>/
├── rf_<driver_name>/
│   ├── configuration.py
│   └── resources/
│       └── configuration/
│           ├── schema.json
│           ├── schema.lock
│           └── default.json
├── config/
│   ├── schema.json
│   ├── schema.lock
│   ├── default.json
│   ├── example.json
│   ├── profiles/
│   │   └── simulator.json
│   └── migrations/
│       ├── README.md
│       └── ...
├── tests/
│   ├── unit/
│   ├── robot/
│   ├── compatibility/
│   └── data/
│       └── configuration/
├── docs/
│   └── configuration.md
└── guide/
    └── configuration_profiles.md
```

Rules:

1. `rf_<driver_name>/resources/configuration/` contains package data used at runtime.
2. The root `config/` files are reviewable source copies used by users, tests, documentation, and release validation.
3. Runtime and root copies shall be byte-identical or generated from one authoritative source during the build.
4. `schema.lock` shall contain the approved digest of canonical `schema.json`.
5. `default.json` shall validate against `schema.json`.
6. `example.json` shall demonstrate every public configurable section using placeholders or safe values.
7. `profiles/simulator.json` shall provide a deterministic offline profile when simulation or replay is supported.
8. Migration modules or declarative migration files shall be stored in `config/migrations/`.
9. No user-generated or machine-local profile shall be included in the release ZIP.
10. The installed driver shall not modify packaged files.

### 6.1 Relationship to RFDS-005

RFDS-005 §6 (v1.3 and later) lists `config/default.json`, `config/example.json`, `config/schema.json`, and `config/schema.lock` as the canonical package artifacts, aligned with RFDS-014. RFDS-014 establishes JSON as the canonical configuration interchange and persistence format; RFDS-005 is authoritative for exactly where these files live in the package tree.

A project migrating from a pre-alignment layout that still carries `config/default.yaml` or `config/example.yaml`:

- shall treat `default.json`, `example.json`, and `schema.json` as authoritative;
- may retain the YAML files only as generated compatibility mirrors during migration;
- shall have CI verify semantic equivalence between any retained YAML mirror and its JSON authority;
- shall not require YAML support in runtime code;
- shall make changes to the JSON authority and regenerate mirrors, not edit YAML directly;
- shall fail release validation when a YAML mirror differs from its JSON authority.

`config/hil_resources.example.yaml` remains YAML by design; it is a bench/HIL resource template governed by RFDS-018, not an RFDS-014 configuration document, and is unaffected by this section.

---

## 7. Canonical Configuration Document

A complete configuration document shall have the following top-level structure:

```json
{
  "rfds014_version": "1.0",
  "schema_id": "rf_<driver_name>.configuration",
  "schema_version": "1.0.0",
  "driver": {
    "driver_name": "rf_<driver_name>",
    "minimum_driver_version": "26.1",
    "maximum_driver_version_exclusive": "27.0"
  },
  "profile": {
    "name": "laboratory_default",
    "description": "Safe profile for the laboratory instrument.",
    "scope": "USER"
  },
  "settings": {
    "transport": {},
    "timeouts": {},
    "retry": {},
    "logging": {},
    "simulation": {},
    "safety": {},
    "device": {}
  },
  "extensions": {},
  "metadata": {
    "created_utc": "2026-07-26T00:00:00Z",
    "modified_utc": "2026-07-26T00:00:00Z",
    "exported_by_driver_version": "26.1",
    "migration_history": []
  }
}
```

### 7.1 Required top-level fields

The following fields shall be required:

- `rfds014_version`;
- `schema_id`;
- `schema_version`;
- `driver`;
- `profile`;
- `settings`.

`extensions` and `metadata` may be optional when the schema supplies equivalent defaults.

### 7.2 `driver`

The `driver` object shall identify the intended driver family and compatibility boundary.

Required fields:

- `driver_name`.

Recommended fields:

- `minimum_driver_version`;
- `maximum_driver_version_exclusive`;
- `supported_models`;
- `required_capabilities`.

A driver shall reject a profile whose `driver_name` does not match its own canonical driver identifier.

A driver shall reject an incompatible version range unless a tested migration produces a compatible document.

### 7.3 `profile`

The `profile` object shall contain:

- `name`;
- `description`;
- `scope`.

Permitted `scope` values:

- `PACKAGE`;
- `PROJECT`;
- `USER`;
- `SYSTEM`;
- `SESSION`;
- `EXPORTED`.

Profile names shall:

- contain 1 to 64 characters;
- use letters, digits, underscore, hyphen, or period;
- not contain path separators;
- not equal `.` or `..`;
- not begin with a period unless explicitly allowed by project policy;
- be treated as identifiers, not arbitrary paths.

### 7.4 `settings`

The `settings` object shall be the only normal location for behavioural configuration.

Standard sections are:

- `transport`;
- `timeouts`;
- `retry`;
- `logging`;
- `simulation`;
- `safety`;
- `device`.

A driver may omit a standard section only when its schema marks that section unsupported.

Driver-specific settings shall be placed under `settings.device`, not as new uncoordinated top-level keys.

### 7.5 `extensions`

`extensions` is reserved for namespaced, non-core additions.

Extension keys shall use a stable namespace, for example:

```json
{
  "extensions": {
    "com.example.fixture_adapter": {
      "mode": "A"
    }
  }
}
```

Unknown top-level keys and unknown keys outside approved extension namespaces shall be rejected in strict mode.

Extension data shall not bypass safety validation or activate undocumented driver behaviour.

### 7.6 `metadata`

Metadata shall not change driver behaviour.

Metadata may contain:

- creation and modification timestamps;
- source profile identifier;
- export tool and driver version;
- migration history;
- operator-independent description;
- provenance reference;
- semantic configuration fingerprint.

Metadata shall not contain:

- credentials;
- personal operator data unless explicitly required and separately governed;
- physical-device serial number as a connection selector unless the serial is also represented in validated settings;
- hidden behavioural flags.

---

## 8. JSON Schema Requirements

### 8.1 Schema dialect

Each driver configuration schema shall use JSON Schema Draft 2020-12 unless the RFDS project approves a later common dialect.

The root schema shall declare:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema"
}
```

### 8.2 Schema identity

The schema shall contain:

- `$id`;
- `title`;
- `description`;
- `type`;
- required-field declarations;
- `additionalProperties` policy;
- reusable `$defs` where applicable;
- semantic version information through `x-rfds-schema-version`.

### 8.3 Strictness

The schema shall use `additionalProperties: false` for core RFDS objects unless an approved extension point is explicitly defined.

Unknown keys shall fail validation by default.

A compatibility mode may preserve unknown keys only under the `extensions` object. Preserved unknown extension data shall not be applied to the driver unless its namespace is supported.

### 8.4 Defaults

Schema defaults shall be explicit and shall match `default.json`.

A schema default is documentation and normalization input; it shall not override a value explicitly supplied by a higher-precedence layer.

### 8.5 Types and constraints

Every behavioural field shall define applicable:

- JSON type;
- minimum and maximum;
- enum values;
- pattern;
- minimum and maximum length;
- array item schema;
- uniqueness;
- nullability;
- default;
- unit;
- application timing;
- sensitivity;
- safety classification.

### 8.6 RFDS schema annotations

The following custom annotations are defined:

| Annotation | Values | Purpose |
|---|---|---|
| `x-rfds-unit` | String | Physical or time unit |
| `x-rfds-apply-mode` | `HOT`, `NEXT_CONNECTION`, `DRIVER_RESTART`, `DEVICE_PERSISTENT` | When a validated change takes effect |
| `x-rfds-risk-level` | `NONE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | Safety classification |
| `x-rfds-sensitive` | Boolean | Redaction and export policy |
| `x-rfds-secret-reference` | Boolean | Value is a reference, not the secret itself |
| `x-rfds-merge` | `DEEP_MERGE`, `REPLACE`, `APPEND_UNIQUE` | Merge behaviour |
| `x-rfds-requires-disconnected` | Boolean | Active connection must be closed before apply |
| `x-rfds-requires-confirmation` | Boolean | Explicit authorization required |
| `x-rfds-device-write` | Boolean | Applying the value causes a protocol operation |
| `x-rfds-deprecated-since` | Version string | Deprecation start |
| `x-rfds-replacement` | JSON Pointer or setting name | Replacement field |
| `x-rfds-capability` | Capability identifier | RFDS-013/RFDS-017 relationship |
| `x-rfds-environment-variable` | String | Approved environment override |
| `x-rfds-portable` | Boolean | Whether the field is expected to transfer between hosts |

Custom annotations shall be treated as metadata by generic JSON Schema validators and as normative input by RFDS configuration tooling.

`x-rfds-risk-level` uses the same five-tier risk scale defined canonically by RFDS-002 §16.1 (`none`/`low`/`medium`/`high`/`critical`), serialized in upper case to match this schema's other annotation enums; tooling that compares risk levels across RFDS-002, RFDS-013, and RFDS-014 shall compare case-insensitively rather than treating the casing as a semantic difference.

### 8.7 Cross-field validation

Constraints that cannot be expressed completely in base JSON Schema shall be implemented by deterministic semantic validators.

Examples:

- `read_timeout_s` shall be greater than or equal to protocol response time limits;
- retry count shall be zero when the operation is not safe to retry;
- simulation and real-hardware modes shall be mutually exclusive;
- serial settings shall match selected serial transport;
- a configured channel shall exist for the selected model;
- a safety maximum shall not exceed an approved device or bench limit;
- a log path shall not resolve inside the installed package.

Semantic validation failures shall use the same structured error model as schema failures.

---

## 9. Standard Value Representation

### 9.1 Numbers

Physical and timing values shall be JSON numbers, not strings, unless the device protocol requires a symbolic value such as `AUTO`, `MIN`, or `MAX`.

Scientific notation is permitted.

NaN, positive infinity, and negative infinity are forbidden because they are not valid JSON numbers.

### 9.2 Units

A configuration value shall use one canonical unit defined by its schema.

Examples:

- seconds for timeout and delay;
- volts for voltage;
- amperes for current;
- ohms for resistance;
- hertz for frequency;
- degrees Celsius for temperature where the driver contract uses Celsius.

A profile shall not rely on a hidden display-unit preference to interpret a number.

### 9.3 Booleans

Booleans shall use JSON `true` and `false`, not strings such as `"yes"`, `"on"`, or `"1"`.

Robot-facing converters may accept documented equivalent inputs but shall normalize them before validation and export.

### 9.4 Enumerations

Enums shall use stable strings. Case normalization may be supported at the input boundary, but canonical export shall use the schema-defined form.

### 9.5 Null

`null` shall be accepted only where the schema explicitly permits it.

`null` shall not mean “delete this key” or “use default” unless a field-specific rule explicitly states that meaning.

### 9.6 Paths

Persisted paths should be relative to an approved base directory or use a portable token.

Environment variables and home-directory expansion shall be explicit and documented.

Path traversal outside the approved base directory shall be rejected for managed profile operations.

### 9.7 Resource identifiers

VISA, serial, TCP, USB, CAN, Modbus, and SDK resource identifiers shall be represented as strings in transport-specific fields.

Auto-discovery shall be represented by a separate Boolean or enum. An empty string shall not silently enable auto-discovery.

### 9.8 Durations

Durations shall be stored as seconds using JSON numbers.

Robot time strings may be accepted at the Robot API boundary, but canonical configuration shall contain normalized seconds.

### 9.9 Timestamps

Timestamps shall use UTC RFC 3339 form with a `Z` suffix.

Timestamps shall be metadata unless explicitly defined as behavioural schedule input.

---

## 10. Canonicalization and Fingerprints

### 10.1 Canonical JSON output

Canonical export shall:

1. use UTF-8;
2. use object keys sorted lexicographically;
3. use JSON primitive types only;
4. use normalized enum spelling;
5. use normalized numeric units;
6. omit insignificant whitespace for fingerprint calculation;
7. preserve array order where order is semantically meaningful;
8. sort arrays only when the schema marks them as unordered;
9. exclude metadata fields declared non-semantic;
10. redact or replace sensitive values before ordinary export.

Human-readable file export should use two-space indentation and end with one newline.

### 10.2 Semantic fingerprint

The configuration fingerprint shall be computed from canonical semantic configuration.

The fingerprint input shall exclude:

- `metadata.created_utc`;
- `metadata.modified_utc`;
- `metadata.migration_history`;
- export-tool information;
- existing fingerprint fields;
- plaintext secret values;
- non-semantic comments or descriptions where the schema marks them non-behavioural.

The recommended digest is SHA-256.

The exported representation may use:

```json
{
  "metadata": {
    "configuration_fingerprint": "sha256:<hex-digest>"
  }
}
```

### 10.3 Schema lock

`schema.lock` shall record at least:

```json
{
  "schema_id": "rf_<driver_name>.configuration",
  "schema_version": "1.0.0",
  "sha256": "<hex-digest>"
}
```

Release validation shall fail when the schema content and lock differ.

---

## 11. Configuration Scopes

The configuration manager shall distinguish these scopes:

| Scope | Persistence | Typical owner |
|---|---|---|
| `PACKAGE_DEFAULT` | Installed read-only package data | Driver project |
| `PROJECT_PROFILE` | Project repository or explicitly supplied directory | Test project |
| `USER_PROFILE` | Current operating-system user | User |
| `SYSTEM_PROFILE` | Machine-wide controlled location | Administrator |
| `SESSION_OVERRIDE` | Current named driver session only | Robot suite or application |
| `INSTANCE_OVERRIDE` | Current library instance | Constructor or embedding application |
| `EFFECTIVE` | Computed result, not independently stored | Configuration manager |

The active configuration report shall identify the source scope of each resolved field.

---

## 12. Precedence and Resolution

### 12.1 Precedence order

Unless a device-specific requirement defines a stricter approved rule, effective configuration shall resolve from lowest to highest precedence as follows:

```text
1. PACKAGE_DEFAULT
2. SYSTEM_PROFILE
3. USER_PROFILE
4. PROJECT_PROFILE
5. explicitly imported profile
6. approved environment-variable overrides
7. library constructor arguments
8. INSTANCE_OVERRIDE
9. SESSION_OVERRIDE
10. explicit keyword arguments for the current operation
```

An operation-specific keyword argument shall not be persisted merely because it has the highest runtime precedence.

### 12.2 Source visibility

The driver shall be able to report:

- effective value;
- source scope;
- source profile or environment variable;
- whether the value is defaulted;
- whether a restart or reconnect is required;
- whether the value is sensitive;
- whether the value differs from package default.

Sensitive values shall be redacted in this report.

### 12.3 Environment variables

Only environment variables explicitly declared by the schema or driver documentation may override configuration.

Generic conversion of all environment variables with a name prefix is prohibited unless every generated key is validated against the schema.

An unset environment variable shall not override a lower layer.

An empty environment variable shall be treated according to a field-specific rule and shall not silently mean auto-discovery, deletion, or null.

### 12.4 Constructor arguments

Constructor arguments that correspond to configuration keys shall be mapped deterministically and documented.

Constructor arguments shall not bypass schema, semantic, or safety validation.

### 12.5 Multi-session drivers

For multi-session drivers:

- transport address, timeout, retry, and model-specific values may be session-scoped;
- global logging or package behaviour may remain instance-scoped;
- the schema shall identify which fields are legal at each scope;
- importing one session profile shall not alter another active session;
- exporting a session shall not unintentionally include other sessions.

---

## 13. Merge and Replace Semantics

### 13.1 Modes

Configuration import shall support:

- `REPLACE`;
- `MERGE`;
- `VALIDATE_ONLY`.

`REPLACE` constructs a new effective profile from package defaults plus the supplied complete profile.

`MERGE` overlays supplied settings on the selected base profile.

`VALIDATE_ONLY` performs all parsing, migration, normalization, compatibility, and safety checks without applying or persisting changes.

### 13.2 Object merge

Objects shall deep-merge by key unless the schema annotation `x-rfds-merge` specifies `REPLACE`.

### 13.3 Arrays

Arrays shall be replaced by default.

`APPEND_UNIQUE` may be used only when the schema explicitly declares it and defines equality rules.

### 13.4 Missing fields

In `MERGE`, a missing field retains the lower-precedence value.

In `REPLACE`, a missing optional field receives its schema or package default. A missing required field fails validation.

### 13.5 Deletion

RFDS-014 does not use `null` as a generic deletion marker.

A field shall be reset by:

- resetting that field to package default through the configuration API; or
- importing a replacement profile that omits the optional field; or
- using a schema-defined explicit value such as `DISABLED`.

### 13.6 Unknown fields

Unknown fields shall fail strict validation.

A non-strict compatibility import may preserve namespaced extension data but shall not apply unsupported extension values.

---

## 14. Import Workflow

A configuration import shall execute these steps in order:

1. resolve the source;
2. enforce source-size limits;
3. read bytes with a finite timeout where applicable;
4. decode UTF-8;
5. parse JSON;
6. verify the RFDS-014 version;
7. verify driver identity;
8. determine source schema version;
9. migrate to the current schema when an approved path exists;
10. validate against JSON Schema;
11. run semantic validation;
12. resolve secret references for validation without exposing values;
13. classify changed fields;
14. evaluate safety and authorization requirements;
15. create a complete candidate effective configuration;
16. calculate the candidate fingerprint;
17. return a validation preview;
18. apply only when explicitly requested;
19. persist only when explicitly requested;
20. generate structured evidence.

No step after parsing may mutate active state before the candidate configuration has passed all required checks.

### 14.1 Accepted sources

Import may accept:

- a JSON file path;
- a JSON string;
- an already parsed Robot/Python dictionary;
- a named managed profile;
- an application-provided byte stream when explicitly supported.

Remote HTTP or cloud URLs shall not be accepted by the base configuration manager unless a separate approved security specification governs remote retrieval.

### 14.2 Size limit

The driver shall define a finite maximum configuration size.

The default maximum should not exceed 1 MiB unless the device-specific schema justifies a larger document.

Oversized input shall be rejected before full parsing where practical.

### 14.3 Dry run

Every import implementation shall provide validation-only behaviour.

The dry-run result shall identify:

- validity;
- migration performed;
- changed JSON Pointer paths;
- source and target schema versions;
- reconnect requirements;
- restart requirements;
- device-persistent changes;
- safety confirmations required;
- warnings;
- candidate fingerprint.

### 14.4 Apply behaviour

Applying host-side settings shall be transactional.

If any changed hot setting fails to apply:

- the driver shall restore the prior in-memory configuration where possible;
- the operation shall fail;
- the result shall state whether rollback was complete;
- physical-device state shall be reported separately;
- no persistent profile shall be overwritten.

### 14.5 Reconnect and restart

Settings annotated `NEXT_CONNECTION` or `DRIVER_RESTART` shall not be partially forced into an active session.

The result shall identify pending values and the required action.

An automatic reconnect may occur only when:

- the caller explicitly requests it;
- the reconnect is safe;
- teardown succeeds;
- the new configuration was fully validated;
- failure leaves the driver disconnected rather than silently restoring another resource.

### 14.6 Device-persistent settings

A profile containing `DEVICE_PERSISTENT` fields may be imported and validated without writing the device.

Application of such fields shall require:

- an explicit apply flag;
- an explicit device-persistent authorization flag;
- any RFDS-017 safety preconditions;
- a connected supported device;
- a protocol operation through declared public capability;
- RFDS-019 evidence for the device write;
- read-back or other declared verification when supported.

Loading or saving a host profile alone shall never write device non-volatile memory.

---

## 15. Export Workflow

### 15.1 Export scopes

Export shall support:

- `EFFECTIVE`;
- `PACKAGE_DEFAULT`;
- `ACTIVE_PROFILE`;
- `SESSION`;
- `DIFF_FROM_DEFAULT`.

### 15.2 Export content

Export shall include:

- RFDS-014 version;
- schema identity and version;
- driver compatibility;
- profile identity;
- selected settings;
- supported extensions;
- safe metadata;
- configuration fingerprint.

### 15.3 Redaction

Standard export shall never include plaintext secrets.

Sensitive fields shall be exported as one of:

```json
{"secret_ref": "ENV:RFDS_DEVICE_TOKEN"}
```

```json
{"secret_ref": "OS_VAULT:rfds/device/token"}
```

```json
{"redacted": true}
```

The selected representation shall validate against the field schema.

### 15.4 Destination behaviour

Export may return the configuration as a Robot/Python dictionary and may optionally write a JSON file.

A file export shall:

- validate the destination;
- create parent directories only when explicitly permitted;
- refuse path traversal outside a managed profile directory when using a profile name;
- avoid overwriting an existing file unless `overwrite=true`;
- use atomic replacement;
- return the final absolute path and fingerprint.

### 15.5 Reproducibility

Export followed by import on a compatible driver shall reproduce an equivalent semantic configuration and the same semantic fingerprint, except for approved host-specific or unresolved secret references.

---

## 16. Persistence Model

### 16.1 Managed configuration root

The configuration root shall resolve in this order:

1. explicit application-provided configuration root;
2. `RFDS_CONFIG_HOME`;
3. operating-system user configuration directory.

Recommended user locations:

```text
Windows:
%APPDATA%\RFDS\<driver_name>\

Linux:
${XDG_CONFIG_HOME:-~/.config}/rfds/<driver_name>/
```

System-wide profiles may use an administrator-controlled directory documented by the driver.

The driver shall not write profiles into:

- the installed Python package;
- the release ZIP extraction root unless explicitly selected as a project profile directory;
- the current working directory by default;
- the Robot output directory unless explicitly requested;
- a device-driver installation directory;
- a temporary directory as long-term persistence.

### 16.2 Managed layout

Recommended managed layout:

```text
<config_root>/
├── profiles/
│   ├── default.json
│   └── <profile_name>.json
├── backups/
├── rejected/
├── locks/
└── state/
    └── active_profile.json
```

### 16.3 Active-profile pointer

The active-profile pointer shall identify a profile by managed identifier, not by unvalidated arbitrary path.

Updating the active-profile pointer shall be atomic.

Failure to read the active-profile pointer shall not cause another profile to be selected silently.

### 16.4 Explicit save

Saving shall require:

- a profile name or approved destination;
- a fully valid normalized configuration;
- successful safety classification;
- overwrite authorization when required;
- a finite lock-acquisition timeout.

### 16.5 No autosave by default

Drivers shall not persist every setter keyword automatically.

An optional autosave mode may exist only when:

- disabled by package default;
- explicitly enabled;
- clearly reported in diagnostics;
- writes are debounced;
- atomic persistence is used;
- sensitive and device-persistent fields remain subject to their normal restrictions.

---

## 17. Atomicity, Integrity, and Recovery

### 17.1 Atomic write sequence

A managed configuration write shall:

1. serialize canonical human-readable JSON;
2. write a temporary file in the destination directory;
3. flush application buffers;
4. perform an operating-system flush where supported and required by the integrity policy;
5. validate the temporary file by re-reading it;
6. preserve the previous valid file as a backup when configured;
7. replace the destination atomically;
8. update the active-profile pointer only after successful replacement;
9. remove temporary files;
10. record the resulting fingerprint.

The implementation should use an atomic same-filesystem replace operation.

### 17.2 Last-known-good copy

Before overwriting an existing valid profile, the configuration manager should preserve a bounded number of last-known-good backups.

Backup retention shall be finite and documented.

Backups shall be subject to the same secret and file-permission rules as active profiles.

### 17.3 Invalid file

When a managed profile is malformed or invalid:

- it shall not replace the active configuration;
- it shall not be repaired silently;
- it may be copied to `rejected/` with a timestamp and reason;
- the user shall receive a structured error;
- the driver shall remain disconnected or retain its prior validated configuration;
- the invalid content shall not be logged in full when it may contain sensitive values.

### 17.4 Interrupted write

On startup or profile discovery, orphan temporary files shall not be treated as valid profiles.

Recovery may promote a temporary file only after complete validation and explicit recovery rules.

### 17.5 Integrity mismatch

A stored semantic fingerprint mismatch shall produce a warning or failure according to project policy.

A schema-lock mismatch in the installed package shall fail configuration initialization and release validation.

---

## 18. Concurrent Access

### 18.1 File locking

Managed profile writes shall use a cross-process lock or equivalent exclusive-write mechanism.

The lock shall have a finite acquisition timeout.

A lock record should identify:

- driver name;
- profile;
- process identifier;
- host identifier;
- creation time;
- operation.

### 18.2 Stale locks

Stale-lock recovery shall be deterministic and documented.

A lock shall not be considered stale solely because a fixed short duration elapsed. Process and host evidence should be considered where available.

### 18.3 Reader behaviour

Readers may operate concurrently with each other.

A reader shall observe either the previous complete profile or the new complete profile, not a partial file.

### 18.4 Multi-process conflicts

When two writers target the same profile:

- one shall acquire the lock;
- the other shall wait up to a finite timeout or fail;
- silent last-writer-wins behaviour is prohibited for managed profiles;
- optional optimistic concurrency may use the prior fingerprint.

### 18.5 Active sessions

Applying a profile to one active named session shall be synchronized with operations using that session.

The driver shall not change transport settings while another keyword is using the same transport.

---

## 19. Versioning and Migration

### 19.1 Version fields

RFDS configuration uses:

- `rfds014_version` — version of this platform model;
- `schema_version` — driver configuration schema version;
- driver release version — installed package version;
- profile metadata version — optional profile revision.

### 19.2 Schema version policy

Schema versions shall follow semantic intent:

- major — incompatible key removal, rename, type change, unit change, meaning change, or default that changes safety/behaviour incompatibly;
- minor — backward-compatible optional fields, enum additions that old consumers may ignore only through approved extension behaviour, or new annotations;
- patch — clarifications, documentation, non-semantic metadata, or validation corrections that do not invalidate valid prior profiles.

### 19.3 Migration path

A driver shall provide a deterministic migration path for every configuration schema version declared supported.

Migrations shall:

- operate on parsed data, not textual search-and-replace;
- be ordered;
- have explicit source and target versions;
- be idempotent for the same already-migrated input;
- preserve semantic intent;
- preserve unsupported extension data where safe;
- never invent credentials or hardware limits;
- produce a migration report;
- be unit-tested with fixed vectors;
- fail without applying when information is insufficient.

### 19.4 Automatic migration

Automatic in-memory migration may occur during validation.

Persistent overwrite of the original profile shall require explicit save or `persist_migration=true`.

Before persistent migration, the original valid profile shall be backed up.

### 19.5 Breaking migration

A migration requiring user choice shall stop and report structured questions or required fields.

The driver shall not guess between resources, channels, units, safety limits, or transport types.

### 19.6 Downgrade

Importing a profile from a newer unsupported schema shall fail unless a tested reverse migration or compatible export target exists.

Unknown newer fields shall not be silently discarded.

### 19.7 Migration evidence

The result shall include:

```json
{
  "source_schema_version": "1.0.0",
  "target_schema_version": "2.0.0",
  "steps": [
    {
      "migration_id": "1.0.0_to_2.0.0",
      "changed_paths": ["/settings/timeouts/read_timeout_s"]
    }
  ],
  "warnings": [],
  "requires_user_action": false
}
```

---

## 20. Secret and Sensitive Data Policy

### 20.1 Plaintext secrets

Plaintext credentials, tokens, passwords, private keys, and certificates shall not be stored in normal RFDS driver profiles.

### 20.2 Secret references

A schema may permit a structured secret reference:

```json
{
  "secret_ref": "ENV:RFDS_DEVICE_PASSWORD"
}
```

Supported secret-reference providers shall be explicitly documented.

The base required provider is environment-variable reference. Operating-system vault providers may be added.

### 20.3 Resolution

Secret resolution shall occur only when required for an operation.

Resolved secret values shall:

- remain in memory only as long as necessary;
- not be returned by configuration keywords;
- not be included in diagnostics, traces, Robot logs, exceptions, fingerprints, or exports;
- be redacted from validation errors;
- not be copied into migrated profiles.

### 20.4 Logs and evidence

Configuration evidence shall record the secret-reference type and whether resolution succeeded, not the secret value.

### 20.5 Sensitive non-secret values

Private IP addresses, serial numbers, and local paths may be marked sensitive by project policy even when they are not authentication secrets.

Normal support bundles should provide a redacted option.

### 20.6 Permissions

Profile files containing sensitive references should be created with user-only access where the operating system supports it.

Failure to enforce requested permissions shall produce a warning or failure according to the selected security policy.

---

## 21. Safety Requirements

### 21.1 Safety annotation

Every setting that can affect energy, motion, temperature, pressure, relay routing, calibration, protection, or device persistence shall carry appropriate RFDS schema annotations.

### 21.2 Safety limits

A driver shall not infer approved DUT or fixture limits from the connected instrument model alone.

Package defaults may define conservative instrument limits but shall not claim bench or DUT safety.

RFDS-018 remains authoritative for deployed bench limits and interlocks.

### 21.3 Applying safety-related changes

A high-risk or destructive change shall require explicit authorization and shall identify:

- changed path;
- prior value;
- requested value;
- risk level;
- preconditions;
- required reconnect or restart;
- physical-device write involvement;
- rollback limitations.

### 21.4 Unsafe combinations

Cross-field semantic validation shall reject unsafe combinations before application.

Examples:

- output enabled by default;
- protection disabled while active output values exceed conservative limits;
- relay parallelization that violates isolation requirements;
- temperature limits outside approved chamber or fixture bounds;
- auto-reconnect to an unidentified device when device identity is safety-relevant.

### 21.5 Configuration does not equal authorization

A stored setting permitting a hazardous operation does not itself authorize the operation.

The public capability shall still enforce RFDS-017 risk, state, and confirmation requirements when called.

### 21.6 Safe startup

Loading a profile at driver construction shall not connect to hardware or energize outputs unless the user explicitly invokes a connection or operation keyword.

---

## 22. Standard Robot Framework API

The configuration manager should be supplied by the shared RFDS base library so that equivalent drivers expose equivalent configuration keywords.

Drivers shall expose the following canonical keywords unless an approved platform exception is documented.

### 22.1 `Get Driver Configuration Schema`

Purpose:

- return the active JSON Schema as a Robot Framework-compatible dictionary.

Minimum result fields:

- `schema_id`;
- `schema_version`;
- `schema`;
- `schema_fingerprint`.

This keyword shall not access hardware.

### 22.2 `Get Driver Default Configuration`

Purpose:

- return the validated package default configuration.

Arguments:

```text
redact_sensitive=True
```

This keyword shall not access hardware or writable user storage.

### 22.3 `Get Driver Configuration`

Purpose:

- return configuration for a selected scope.

Arguments:

```text
scope=EFFECTIVE
alias=None
redact_sensitive=True
include_sources=False
```

The result shall identify pending restart or reconnect requirements.

### 22.4 `Validate Driver Configuration`

Purpose:

- parse, migrate, normalize, compatibility-check, and validate configuration without applying it.

Arguments:

```text
configuration
mode=REPLACE
strict=True
alias=None
```

Minimum result:

```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "source_schema_version": "1.0.0",
  "target_schema_version": "1.0.0",
  "changed_paths": [],
  "requires_reconnect": false,
  "requires_restart": false,
  "device_persistent_changes": [],
  "confirmation_required": false,
  "configuration_fingerprint": "sha256:..."
}
```

### 22.5 `Import Driver Configuration`

Purpose:

- validate and optionally apply an imported configuration.

Arguments:

```text
source
mode=REPLACE
apply=False
persist=False
profile_name=None
strict=True
reconnect=False
allow_device_persistent_changes=False
confirm_high_risk=False
alias=None
```

Defaults shall make the operation validation-only and non-persistent.

### 22.6 `Export Driver Configuration`

Purpose:

- return and optionally write a portable JSON configuration.

Arguments:

```text
destination=None
scope=EFFECTIVE
profile_name=None
overwrite=False
alias=None
```

Plaintext secrets shall never be exported.

### 22.7 `Save Driver Configuration`

Purpose:

- save the current validated configuration as a managed profile.

Arguments:

```text
profile_name
scope=EFFECTIVE
overwrite=False
set_active=False
alias=None
```

Saving shall not write physical-device non-volatile state.

### 22.8 `Load Driver Configuration`

Purpose:

- load a managed profile and optionally apply it.

Arguments:

```text
profile_name
apply=False
reconnect=False
alias=None
```

Defaults shall not reconnect hardware.

### 22.9 `List Driver Configuration Profiles`

Purpose:

- list discoverable managed profiles and their status.

The result shall not expose secret values.

### 22.10 `Delete Driver Configuration Profile`

Purpose:

- delete a user-managed profile.

Arguments:

```text
profile_name
confirm=False
```

Package, project read-only, or administrator-controlled profiles shall not be deleted through this keyword.

### 22.11 `Reset Driver Configuration`

Purpose:

- reset selected settings or a scope to package defaults.

Arguments:

```text
path=None
scope=INSTANCE_OVERRIDE
apply=False
persist=False
confirm=False
alias=None
```

Resetting host configuration shall not reset the physical device unless a separate explicitly named device-reset capability is called.

### 22.12 Return-value rules

All standard configuration keywords shall return only Robot Framework-compatible primitive values:

- string;
- number;
- Boolean;
- list;
- dictionary;
- `None`.

`pathlib.Path`, dataclasses, enums, schema-validator objects, open files, exception objects, and arbitrary Python models shall not be returned directly.

---

## 23. Configuration Operation Result Model

Mutating or validation operations shall return a structured result equivalent to:

```json
{
  "status": "VALID",
  "valid": true,
  "applied": false,
  "persisted": false,
  "profile_name": null,
  "source": "<memory>",
  "schema_id": "rf_<driver_name>.configuration",
  "source_schema_version": "1.0.0",
  "target_schema_version": "1.0.0",
  "configuration_fingerprint": "sha256:...",
  "changed_paths": [],
  "pending_paths": [],
  "requires_reconnect": false,
  "requires_restart": false,
  "device_persistent_changes": [],
  "rollback_status": "NOT_REQUIRED",
  "warnings": [],
  "errors": []
}
```

Permitted `status` values:

- `VALID`;
- `APPLIED`;
- `SAVED`;
- `LOADED`;
- `MIGRATED`;
- `REJECTED`;
- `PARTIAL_ROLLBACK`;
- `FAILED`.

Permitted `rollback_status` values:

- `NOT_REQUIRED`;
- `COMPLETE`;
- `PARTIAL`;
- `FAILED`;
- `NOT_POSSIBLE`.

Errors shall include:

```json
{
  "code": "RFDS_CONFIG_RANGE",
  "path": "/settings/timeouts/read_timeout_s",
  "message": "Value is below the allowed minimum.",
  "expected": ">= 0.1",
  "actual": "<redacted-or-safe-value>",
  "source": "USER_PROFILE"
}
```

---

## 24. Configuration Errors

The configuration subsystem shall use stable error codes.

Minimum error catalogue:

| Code | Meaning |
|---|---|
| `RFDS_CONFIG_SOURCE_NOT_FOUND` | Requested profile or file does not exist |
| `RFDS_CONFIG_ACCESS_DENIED` | Source or destination cannot be accessed |
| `RFDS_CONFIG_TOO_LARGE` | Input exceeds configured limit |
| `RFDS_CONFIG_ENCODING` | Input is not valid UTF-8 |
| `RFDS_CONFIG_JSON_SYNTAX` | Invalid JSON syntax |
| `RFDS_CONFIG_SCHEMA_ID` | Wrong schema or driver identity |
| `RFDS_CONFIG_SCHEMA_VERSION` | Unsupported schema version |
| `RFDS_CONFIG_SCHEMA_VALIDATION` | JSON Schema validation failed |
| `RFDS_CONFIG_UNKNOWN_KEY` | Unapproved key encountered |
| `RFDS_CONFIG_TYPE` | Wrong value type |
| `RFDS_CONFIG_RANGE` | Value outside allowed range |
| `RFDS_CONFIG_ENUM` | Unsupported enum value |
| `RFDS_CONFIG_SEMANTIC` | Cross-field rule failed |
| `RFDS_CONFIG_SECRET_UNRESOLVED` | Required secret reference cannot be resolved |
| `RFDS_CONFIG_SAFETY` | Safety rule rejected candidate |
| `RFDS_CONFIG_CONFIRMATION_REQUIRED` | Explicit authorization absent |
| `RFDS_CONFIG_DEVICE_IDENTITY` | Profile incompatible with connected device |
| `RFDS_CONFIG_MIGRATION_UNAVAILABLE` | No approved migration path |
| `RFDS_CONFIG_MIGRATION_FAILED` | Migration could not complete |
| `RFDS_CONFIG_LOCK_TIMEOUT` | Managed profile lock not acquired |
| `RFDS_CONFIG_CONFLICT` | Fingerprint or concurrent-write conflict |
| `RFDS_CONFIG_WRITE_FAILED` | Atomic persistence failed |
| `RFDS_CONFIG_INTEGRITY` | Fingerprint or schema-lock mismatch |
| `RFDS_CONFIG_APPLY_FAILED` | Runtime apply failed |
| `RFDS_CONFIG_ROLLBACK_FAILED` | Previous runtime state could not be restored |
| `RFDS_CONFIG_RECONNECT_REQUIRED` | Change cannot apply to active connection |
| `RFDS_CONFIG_RESTART_REQUIRED` | Driver restart required |
| `RFDS_CONFIG_DEVICE_WRITE_BLOCKED` | Device-persistent write not authorized |
| `RFDS_CONFIG_PROFILE_NAME` | Invalid managed profile identifier |
| `RFDS_CONFIG_PATH_POLICY` | Destination violates managed-path policy |

Configuration errors shall integrate with the RFDS unified exception and diagnostics standard.

---

## 25. Capability Discovery Integration

RFDS-013 capability discovery shall identify configuration support.

The driver-capabilities result shall include a structure equivalent to:

```json
{
  "configuration": {
    "supported": true,
    "rfds014_version": "1.0",
    "schema_id": "rf_<driver_name>.configuration",
    "schema_version": "1.0.0",
    "import_formats": ["JSON"],
    "export_formats": ["JSON"],
    "scopes": [
      "PACKAGE_DEFAULT",
      "PROJECT_PROFILE",
      "USER_PROFILE",
      "SESSION_OVERRIDE",
      "INSTANCE_OVERRIDE",
      "EFFECTIVE"
    ],
    "supports_named_profiles": true,
    "supports_migration": true,
    "supports_hot_apply": true,
    "supports_device_persistent_fields": false,
    "secret_reference_providers": ["ENV"],
    "max_configuration_bytes": 1048576
  }
}
```

Capability discovery shall not expose active secret values or private configuration contents.

The capability declaration shall match the actual configuration API, schema, documentation, and tests.

---

## 26. RFDS-017 AI Driver Contract Integration

The RFDS-017 AI Driver Contract shall describe:

- the configuration persistence model;
- configuration-related public keywords;
- risk levels;
- preconditions and postconditions;
- side effects;
- errors;
- timing;
- exclusive resources;
- device-persistent effects;
- configuration limitations;
- required setup and teardown.

The AI contract shall not duplicate every schema property when the schema is machine-accessible. It shall reference:

- RFDS-014 version;
- schema ID;
- schema version;
- schema fingerprint;
- configuration capability identifiers.

An AI agent shall be able to distinguish:

- changing host-side configuration;
- applying volatile device state;
- writing device non-volatile state;
- saving a host profile.

---

## 27. RFDS-018 Test Bench Integration

The deployed RFDS-018 bench contract remains authoritative for:

- actual device addresses;
- installed instrument aliases;
- USB, VISA, serial, and LAN resource assignments;
- fixture connections;
- relay routing;
- DUT safety limits;
- approved operating ranges;
- shared resources;
- operator actions;
- emergency procedures.

A driver profile may reference a bench resource identifier, but it shall not silently redefine bench topology or global safety.

Bench configuration may select driver profiles by name or fingerprint.

A bench contract should record the required driver configuration fingerprint for reproducible execution.

---

## 28. GUI and Generic Application Integration

Generic operator applications shall be able to construct configuration interfaces from `schema.json` and RFDS annotations.

A GUI shall:

- display field descriptions and units;
- enforce type, range, enum, and pattern constraints;
- distinguish hot, reconnect, restart, and device-persistent settings;
- identify sensitive fields;
- show source scope and default status;
- preview changed paths;
- provide validation-only action;
- require confirmation for risky changes;
- show whether apply, reconnect, restart, or device write is pending;
- never expose resolved secret values;
- preserve unsupported namespaced extensions without applying them;
- show structured validation errors at the relevant field.

A GUI shall not infer that a field is safe merely because it appears in a configuration schema.

---

## 29. RFDS-019 Conformance Integration

Configuration keywords shall be included in the exported Robot Framework keyword inventory.

For host-only configuration keywords, RFDS-019 shall verify:

- callability;
- argument conversion;
- return schema;
- file and persistence effects where applicable;
- absence of unintended protocol operations.

For configuration operations that apply device-facing settings, RFDS-019 shall additionally verify:

- the intended outbound protocol operation;
- response or acknowledgement;
- error handling;
- no-response behaviour where applicable;
- recovery after documented failure;
- no device write during validation-only, load-only, or save-only operations.

Each device-persistent configuration field shall map to a declared public capability and protocol vector or an approved exclusion.

---

## 30. Testing Requirements

### 30.1 Unit tests

Unit tests shall cover at least:

- valid package default;
- valid example profile;
- malformed JSON;
- invalid UTF-8;
- wrong driver identity;
- unsupported RFDS-014 version;
- unsupported schema version;
- missing required key;
- unknown key;
- wrong type;
- range boundary;
- enum normalization;
- forbidden null;
- object merge;
- array replacement;
- replace mode;
- validate-only mode;
- environment precedence;
- constructor precedence;
- session precedence;
- source reporting;
- canonicalization;
- stable fingerprint;
- metadata exclusion from fingerprint;
- secret redaction;
- unresolved secret reference;
- profile-name validation;
- path traversal rejection;
- managed directory resolution;
- atomic write success;
- simulated interrupted write;
- invalid temporary file;
- backup creation and retention;
- lock timeout;
- optimistic fingerprint conflict where supported;
- migration success;
- migration failure;
- newer-schema rejection;
- rollback success;
- rollback failure reporting;
- restart and reconnect classification;
- device-persistent authorization block;
- size limit;
- no hardware access during schema/default retrieval.

### 30.2 Robot Framework tests

Robot tests shall verify:

- all standard configuration keywords are discoverable;
- schema and default configuration are returned;
- default configuration validates;
- validate-only import does not change effective configuration;
- invalid import returns actionable failure;
- merge produces expected effective configuration;
- export and re-import preserve fingerprint;
- save, list, load, and delete profile workflow;
- reset to default;
- per-session isolation where supported;
- no automatic reconnect by default;
- no physical-device write during host-only operations.

### 30.3 Compatibility tests

Compatibility tests shall cover:

- every declared supported prior schema version;
- migration vectors;
- deprecated key warnings;
- compatibility with supported driver release boundaries;
- round-trip export and import;
- rejection of unsupported future schema;
- failure when schema lock is stale.

### 30.4 Security tests

Security tests shall cover:

- secret redaction in return values;
- secret redaction in exceptions;
- secret redaction in Robot logs;
- path traversal;
- symbolic-link or reparse-point policy where applicable;
- managed-directory escape;
- oversized input;
- maliciously deep JSON according to parser limits;
- profile-name injection;
- concurrent write conflict;
- file-permission warning or failure;
- configuration content not executed as code.

### 30.5 HIL tests

HIL tests are required only for settings whose application changes the physical device or depends on real device identity.

HIL tests shall:

- begin from a documented safe state;
- use RFDS-018 resource and safety data;
- verify device identity;
- use explicit authorization;
- capture protocol evidence;
- verify read-back where supported;
- restore safe state;
- record any physical-device persistence.

---

## 31. Test Evidence

Each configuration test run should produce:

```text
results/configuration/<driver>/<timestamp>/
├── output.xml
├── log.html
├── report.html
├── configuration_test_summary.md
├── environment.json
├── schema_validation.json
├── default_validation.json
├── migration_results.json
├── round_trip_results.json
├── persistence_results.json
├── security_results.json
└── exclusions.json
```

Evidence shall identify:

- driver version;
- RFDS-014 version;
- schema ID and version;
- schema fingerprint;
- package default fingerprint;
- operating system;
- Python and Robot Framework versions;
- tests executed;
- migrations tested;
- persistence location policy;
- redaction status;
- failures, skips, and exclusions.

Evidence shall not contain resolved secrets.

---

## 32. Documentation Requirements

`docs/configuration.md` shall include:

- configuration domains;
- schema version;
- package defaults;
- precedence;
- profile locations;
- import and export examples;
- merge and replace semantics;
- environment variables;
- session configuration;
- restart and reconnect rules;
- migration policy;
- secret references;
- safety considerations;
- standard keyword examples;
- troubleshooting.

`guide/configuration_profiles.md` shall provide step-by-step instructions for:

1. exporting the effective configuration;
2. creating a named profile;
3. validating before application;
4. importing without applying;
5. applying a profile;
6. saving and activating a profile;
7. moving a portable profile to another host;
8. supplying machine-specific resources through environment variables;
9. recovering from invalid or corrupt configuration;
10. migrating an old profile;
11. comparing fingerprints;
12. deleting a user profile;
13. distinguishing host save from device-persistent write.

At least one numbered Robot Framework example shall demonstrate JSON round-trip configuration without real hardware.

At least one example shall demonstrate validation failure.

---

## 33. Lifecycle Integration

### Gate 1 — Architecture and Skeleton

Deliver:

- configuration manager architecture;
- schema skeleton;
- package default skeleton;
- standard keyword declarations;
- persistence-location policy;
- migration strategy;
- unit-test skeleton.

### Gate 2 — Core Implementation

Deliver:

- JSON parsing and normalization;
- schema validation;
- effective configuration resolution;
- standard get and validate keywords;
- initial import/export;
- core unit tests.

### Gate 3 — Extended Features

Deliver:

- named profiles;
- atomic persistence;
- migration;
- session overrides;
- capability discovery;
- secret references;
- safety annotations;
- rollback and concurrency handling.

### Gate 4 — Tests and Documentation

Deliver:

- complete unit, Robot, compatibility, security, and applicable HIL tests;
- configuration guide;
- GitHub Pages content;
- examples;
- evidence generation;
- RFDS-017 and RFDS-019 updates.

### Gate 5 — Review and Release

Verify:

- schema and lock;
- safe defaults;
- migration coverage;
- persistence integrity;
- secret redaction;
- API compatibility;
- RFDS-019 conformance;
- documentation consistency;
- history and review records;
- release package inclusion.

---

## 34. Acceptance Criteria

A driver passes RFDS-014 only when:

1. canonical JSON schema, lock, default, and example files exist;
2. package and root configuration artifacts are synchronized;
3. `default.json` and all packaged profiles validate;
4. JSON import and export work without optional dependencies;
5. every configuration value is validated before application;
6. strict mode rejects unknown core keys;
7. effective configuration precedence is deterministic;
8. resolved field sources can be reported;
9. validation-only import causes no state, persistence, connection, or device change;
10. runtime application is transactional or reports rollback limitations;
11. persistence occurs only through explicit action;
12. managed writes are atomic;
13. concurrent writes do not silently overwrite each other;
14. invalid or corrupt profiles do not replace active valid configuration;
15. configuration schema versions are explicit;
16. every declared supported prior schema has tested migration;
17. unsupported future schemas are rejected;
18. plaintext secrets are absent from profiles, exports, logs, evidence, and fingerprints;
19. risky settings are annotated and require appropriate authorization;
20. loading or saving a host profile does not write physical-device non-volatile state;
21. standard Robot Framework configuration keywords are discoverable and documented;
22. RFDS-013 capability discovery accurately reports configuration support;
23. RFDS-017 configuration semantics match the released API;
24. RFDS-019 verifies configuration keyword callability and applicable protocol behaviour;
25. documentation and at least two relevant examples are current;
26. configuration tests pass;
27. no Critical configuration, safety, security, or persistence review finding remains open.

---

## 35. Failure Conditions

RFDS-014 shall fail when:

- JSON import or export requires an undocumented optional dependency;
- no canonical schema exists;
- schema and lock differ;
- package default is invalid;
- unsafe hardware state is enabled by package default;
- an explicitly selected invalid profile silently falls back to another profile;
- unknown core keys are silently ignored in strict mode;
- constructor or environment overrides bypass validation;
- merge behaviour is undocumented or nondeterministic;
- runtime changes are persisted without explicit authorization;
- profile loading connects to hardware or energizes outputs unexpectedly;
- validation-only import changes active configuration;
- saving a host profile writes physical-device non-volatile state;
- a device-persistent setting is applied without declared capability and authorization;
- partial application is reported as complete success;
- persistence may expose a partially written file;
- concurrent writers use uncontrolled last-writer-wins behaviour;
- a corrupt profile replaces the previous valid profile;
- migration silently drops meaningful data;
- a newer unsupported schema is partially accepted;
- plaintext secrets appear in configuration files, exports, logs, errors, traces, evidence, or fingerprints;
- path traversal permits writing outside the approved destination;
- standard configuration keywords return non-Robot-compatible objects;
- capability discovery, AI contract, schema, documentation, or implementation disagree;
- required tests or migration vectors are missing;
- configuration changes are absent from history and review evidence.

---

## 36. Change Control

Whenever a configuration field, default, schema constraint, annotation, environment variable, precedence rule, merge rule, persistence path, keyword, error, or migration changes, the same driver revision shall update:

- `schema.json`;
- `schema.lock`;
- `default.json` where applicable;
- `example.json`;
- migration logic;
- configuration tests;
- standard keyword documentation;
- RFDS-013 capability data;
- RFDS-017 AI Driver Contract;
- RFDS-019 conformance vectors when device-facing behaviour changes;
- README and GitHub Pages;
- configuration guide;
- history entry;
- code review;
- compatibility review;
- requirement traceability;
- release notes.

A behavioural configuration change without a schema-version assessment shall fail review.

A breaking configuration change without migration or an approved major-version policy shall fail release review.

---

## 37. Review Checklist

1. Is JSON the canonical import/export and persistence format?
2. Does the driver provide schema, lock, default, and example JSON?
3. Does package default validate?
4. Are package defaults safe and free of local resources and credentials?
5. Are unknown keys rejected in strict mode?
6. Are all fields typed, constrained, documented, and unit-normalized?
7. Are apply mode, risk, sensitivity, and device-write annotations complete?
8. Is the precedence order deterministic?
9. Can the source of every effective value be reported?
10. Are merge, replace, array, null, and reset semantics explicit?
11. Does validation occur before any mutation?
12. Does validation-only mode leave all state unchanged?
13. Are reconnect and restart requirements reported before application?
14. Are physical-device non-volatile writes separately authorized?
15. Are imports size-limited and path-safe?
16. Are exports portable and secret-free?
17. Are writes atomic?
18. Is previous valid configuration recoverable?
19. Are concurrent writers controlled?
20. Are schema versions explicit?
21. Are supported migrations deterministic and tested?
22. Are unsupported newer profiles rejected?
23. Are secret values absent from logs, errors, reports, and fingerprints?
24. Are standard Robot configuration keywords exposed?
25. Does RFDS-013 accurately advertise configuration support?
26. Does RFDS-017 distinguish host persistence from device persistence?
27. Does RFDS-019 prove no unintended device operation occurs?
28. Are Robot, compatibility, security, and applicable HIL tests complete?
29. Are documentation and examples current?
30. Are all changes represented in history, review, and traceability?

---

## 38. Minimum Definition of Done

RFDS-014 implementation is complete for a driver when:

- configuration architecture is implemented;
- canonical schema and lock are valid;
- safe package default and complete example exist;
- JSON import, export, validate, merge, replace, load, save, list, delete, and reset workflows work;
- effective-value source reporting works;
- named user profiles persist atomically;
- invalid profiles fail safely;
- migration works for every declared supported schema;
- secrets remain external and redacted;
- safety-sensitive and device-persistent fields are controlled;
- standard Robot Framework configuration keywords are callable;
- capability discovery and AI contract are synchronized;
- applicable RFDS-019 vectors pass;
- required tests and evidence are generated;
- documentation and examples are complete;
- acceptance criteria in Section 34 pass.

---

## 39. Goal

Provide one predictable configuration model across all RFDS drivers so that humans, Robot Framework suites, generic operator applications, and AI agents can validate, exchange, persist, migrate, inspect, and safely apply driver settings without relying on undocumented local behaviour.

---

## Appendix A — Complete Example Profile

```json
{
  "rfds014_version": "1.0",
  "schema_id": "rf_example_instrument.configuration",
  "schema_version": "1.0.0",
  "driver": {
    "driver_name": "rf_example_instrument",
    "minimum_driver_version": "26.1",
    "maximum_driver_version_exclusive": "27.0",
    "supported_models": [
      "EXAMPLE-1000"
    ],
    "required_capabilities": [
      "configuration",
      "simulation"
    ]
  },
  "profile": {
    "name": "usb_safe",
    "description": "Safe USB profile with output disabled.",
    "scope": "EXPORTED"
  },
  "settings": {
    "transport": {
      "type": "VISA_USB",
      "resource": "${ENV:EXAMPLE_VISA_RESOURCE}",
      "auto_discover": false,
      "read_termination": "\n",
      "write_termination": "\n"
    },
    "timeouts": {
      "open_timeout_s": 5.0,
      "read_timeout_s": 10.0,
      "write_timeout_s": 5.0
    },
    "retry": {
      "enabled": true,
      "max_attempts": 2,
      "backoff_s": 0.25,
      "reconnect_on_transport_error": false
    },
    "logging": {
      "level": "INFO",
      "protocol_trace": false,
      "redact_sensitive": true,
      "output_directory": "${ENV:RFDS_RESULTS_DIR}"
    },
    "simulation": {
      "enabled": false,
      "profile": "default",
      "deterministic_seed": 1
    },
    "safety": {
      "connect_only_to_supported_model": true,
      "allow_device_persistent_changes": false,
      "allow_output_enable_from_profile": false
    },
    "device": {
      "default_channel": 1,
      "line_frequency_hz": 50,
      "remote_mode_on_connect": true,
      "clear_error_queue_on_connect": false
    }
  },
  "extensions": {},
  "metadata": {
    "created_utc": "2026-07-26T00:00:00Z",
    "modified_utc": "2026-07-26T00:00:00Z",
    "exported_by_driver_version": "26.1",
    "migration_history": [],
    "configuration_fingerprint": "sha256:<calculated-value>"
  }
}
```

---

## Appendix B — Schema Fragment with RFDS Annotations

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:rfds:rf_example_instrument:configuration:1.0.0",
  "title": "RFDS Example Instrument Configuration",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "rfds014_version",
    "schema_id",
    "schema_version",
    "driver",
    "profile",
    "settings"
  ],
  "properties": {
    "rfds014_version": {
      "const": "1.0"
    },
    "schema_id": {
      "const": "rf_example_instrument.configuration"
    },
    "schema_version": {
      "const": "1.0.0"
    },
    "settings": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "transport",
        "timeouts",
        "retry",
        "logging",
        "simulation",
        "safety",
        "device"
      ],
      "properties": {
        "timeouts": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "read_timeout_s"
          ],
          "properties": {
            "read_timeout_s": {
              "type": "number",
              "minimum": 0.1,
              "maximum": 120.0,
              "default": 10.0,
              "description": "Maximum response wait time.",
              "x-rfds-unit": "s",
              "x-rfds-apply-mode": "HOT",
              "x-rfds-risk-level": "NONE",
              "x-rfds-sensitive": false,
              "x-rfds-merge": "REPLACE"
            }
          }
        },
        "safety": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "allow_device_persistent_changes": {
              "type": "boolean",
              "default": false,
              "x-rfds-apply-mode": "DEVICE_PERSISTENT",
              "x-rfds-risk-level": "HIGH",
              "x-rfds-requires-confirmation": true,
              "x-rfds-device-write": false
            }
          }
        }
      }
    }
  },
  "x-rfds-schema-version": "1.0.0"
}
```

---

## Appendix C — Migration Example

Source:

```json
{
  "schema_version": "1.0.0",
  "settings": {
    "timeout_ms": 10000
  }
}
```

Migration rule:

```text
Migration ID: 1.0.0_to_2.0.0
- Rename /settings/timeout_ms to /settings/timeouts/read_timeout_s
- Convert milliseconds to seconds
- Reject negative values
- Preserve the source profile as backup before persistent migration
```

Target:

```json
{
  "schema_version": "2.0.0",
  "settings": {
    "timeouts": {
      "read_timeout_s": 10.0
    }
  },
  "metadata": {
    "migration_history": [
      {
        "migration_id": "1.0.0_to_2.0.0",
        "source_schema_version": "1.0.0",
        "target_schema_version": "2.0.0"
      }
    ]
  }
}
```

---

## Appendix D — Required Cross-Specification Alignment

The following RFDS documents should be updated or interpreted consistently with RFDS-014:

1. **RFDS-001**  
   Add the configuration manager and configuration resolution path to the platform architecture and traceability model.

2. **RFDS-002**  
   Add the standard configuration keywords and return schemas.

3. **RFDS-003**  
   Assign shared configuration-manager responsibilities to `BaseInstrumentLibrary`.

4. **RFDS-005**  
   Canonical `default.json`, `example.json`, `schema.json`, and `schema.lock` are now listed in RFDS-005 §6; `configuration.py`, profiles, and migration directories remain to be reflected there as the package layout evolves.

5. **RFDS-006**  
   Add coding requirements for pure validation functions, type-safe models, redaction, atomic writes, and migration code.

6. **RFDS-007**  
   Include the RFDS configuration error catalogue and rollback-state reporting.

7. **RFDS-008**  
   Add configuration fingerprints, schema identity, redaction status, and migration evidence to the RFDS-008 §33 diagnostic bundle and §20 configuration evidence sections.

8. **RFDS-009**  
   Add configuration, migration, persistence, concurrency, and security test layers.

9. **RFDS-010**  
   Add the Section 37 review checklist.

10. **RFDS-011**  
    Require schema-version assessment, migration documentation, and profile-compatibility notes for every release.

11. **RFDS-012**  
    Require generic GUI generation from schema and RFDS annotations.

12. **RFDS-013**  
    Add the configuration capability structure in Section 25.

13. **RFDS-017**  
    Reference schema identity, configuration capabilities, host/device persistence distinction, and configuration errors.

14. **RFDS-018**  
    Allow bench contracts to select driver profiles by name and fingerprint without duplicating driver schema.

15. **RFDS-019**  
    Include host-only configuration keyword callability, side-effect checks, and protocol proof for device-facing apply operations.
