# RFDS-010 — Driver Production Readiness Review Checklist

**Document ID:** RFDS-010  
**Version:** 1.0  
**Status:** Draft Project Standard (Normative)  
**Applies to:** Every RFDS Robot Framework driver gate, phase completion, release candidate, and production release

---

## 1. Purpose

This specification defines the mandatory review method used to decide whether an RFDS Robot Framework driver is ready for production release.

The review shall evaluate the exact release candidate as an integrated product, not only the Python source code. It shall combine evidence for:

- functional correctness;
- architecture and maintainability;
- Robot Framework public API quality;
- transport and protocol behaviour;
- error handling, timeout, retry, and recovery;
- safety and cleanup;
- configuration and resource ownership;
- testing and regression protection;
- real-device or approved simulator validation;
- RFDS-019 call and protocol conformance;
- AI Driver Contract consistency;
- packaging, installation, documentation, examples, and scripts;
- compatibility, security, release integrity, and traceability.

The output of RFDS-010 is a documented production-readiness verdict supported by reproducible evidence and an explicit finding register.

A numerical score may summarize quality, but it shall never override a release-blocking defect.

---

## 2. Scope

### 2.1 In scope

RFDS-010 covers:

- review of the final release ZIP and the extracted stable project root;
- review of all files changed in the current gate or release;
- review of unchanged components whose behaviour is affected by the change;
- verification of required RFDS package content;
- source-code and architecture review;
- public Robot Framework API review;
- protocol and transport review;
- safety, state, resource, and cleanup review;
- test strategy, execution results, coverage, and evidence review;
- RFDS-017, RFDS-018 where applicable, and RFDS-019 consistency;
- documentation, examples, scripts, guides, README, and GitHub Pages review;
- versioning, release identity, changelog, history, checksums, and provenance review;
- compatibility, dependency, supply-chain, licence, and secret-handling review;
- known-risk and residual-risk review;
- final release decision.

### 2.2 Out of scope

RFDS-010 does not replace:

- detailed implementation requirements for a specific instrument;
- unit, integration, simulator, HIL, performance, or conformance test execution;
- RFDS-019 protocol-vector execution;
- formal electrical, metrological, calibration, machinery, medical, or functional-safety certification;
- vendor compliance certification;
- independent penetration testing unless required by the device or deployment scope.

RFDS-010 reviews the evidence from those activities and determines whether the evidence is sufficient for the claimed release status.

---

## 3. Normative terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviation requires recorded justification;
- **may** — permitted implementation choice;
- **release candidate** — the exact archive and source revision submitted for review;
- **finding** — a documented nonconformity, defect, risk, or observation;
- **blocking finding** — a finding that prohibits the requested release verdict;
- **evidence** — a reproducible file, report, command output, trace, test result, or reviewed source reference supporting a conclusion;
- **residual risk** — risk remaining after implemented corrections and controls;
- **waiver** — formal acceptance of a specific unresolved requirement or finding by an authorized approver.

---

## 4. Normative references

The review shall use the latest approved applicable revision of:

- RFDS-001 — Platform Requirements;
- RFDS-002 — Mandatory Public API and Robot Framework Keyword Standard;
- RFDS-003 — BaseInstrumentLibrary Specification;
- RFDS-004 — Transport Layer Specification;
- RFDS-005 — Driver Package Specification;
- RFDS-006 — Coding Standard;
- RFDS-007 — Error and Exception Standard;
- RFDS-008 — Logging and Evidence Standard;
- RFDS-009 — Testing Standard;
- RFDS-011 — Release Process;
- RFDS-017 — AI Driver Contract Specification;
- RFDS-018 — AI Test Bench Contract Specification, when bench integration is claimed or required;
- RFDS-019 — Robot Framework Driver Call and Protocol Conformance Test Specification;
- RFDS-020 — Driver Implementation Lifecycle;
- the device-specific implementation requirements;
- applicable vendor protocol and programming documentation;
- applicable hardware safety limits and approved bench configuration.

When requirements conflict, precedence shall be:

1. safety and legal requirements;
2. approved device-specific hardware constraints;
3. latest approved RFDS normative requirement;
4. approved implementation task;
5. historical package behaviour and examples.

A conflict shall be recorded and resolved. It shall not be silently interpreted.

---

## 5. Review occasions

RFDS-010 shall be applied at the following occasions.

### 5.1 Gate review

Every implementation gate shall receive a scoped review of the delivered change. Gate review may use reduced evidence appropriate to the gate, but shall still record findings and release limitations.

### 5.2 Phase-completion review

Gate 5 of every phase shall include a complete review of the phase output, regression impact, documentation, AI contract, and release package.

### 5.3 Production release review

Every production release shall receive a full RFDS-010 review against the exact packaged bytes proposed for release.

### 5.4 Hotfix review

A hotfix may use a focused review only when:

- the change scope is narrow and documented;
- affected components and regression risks are identified;
- all release-blocking checks remain executed;
- the full package is rebuilt and validated;
- the hotfix does not bypass safety, protocol, compatibility, or release-integrity controls.

### 5.5 Re-review

Re-review is required after:

- correction of a Critical or Major finding;
- change to public keywords or signatures;
- change to protocol serialization or parsing;
- change to connection, timeout, retry, recovery, or cleanup behaviour;
- change to safety limits or safe state;
- change to package identity, dependencies, build, or release scripts;
- regeneration of the release archive;
- any change that invalidates previous evidence.

---

## 6. Review independence and responsibilities

### 6.1 Reviewer independence

A production review should be performed by a person or agent other than the primary implementer. When this is not practical, the review shall explicitly state that it is a self-review and identify compensating controls such as additional automated checks, independent test evidence, or second approval.

### 6.2 Required roles

The review record shall identify:

- implementation owner;
- reviewer;
- release approver;
- hardware or bench owner when HIL is required;
- risk owner for each accepted residual risk.

One person may hold multiple roles, but role overlap shall be visible.

### 6.3 Reviewer obligations

The reviewer shall:

- inspect the exact release candidate;
- reproduce representative build, install, test, and example workflows;
- verify evidence rather than rely only on statements in documentation;
- distinguish verified facts from assumptions;
- avoid marking an item PASS when evidence is absent;
- record all skipped, deferred, excluded, or not-applicable items;
- issue a verdict consistent with the blocking rules in this specification.

---

## 7. Required review inputs

The release candidate shall provide at least:

1. release ZIP named according to the project versioning rule;
2. stable internal root `rf_<driver_name>/`;
3. source revision or commit identifier;
4. package and dependency metadata;
5. implementation requirements and traceability matrix;
6. current history and release notes;
7. current code, architecture, Robot API, documentation, and release-readiness reviews;
8. unit, Robot, integration, simulator/replay, compatibility, HIL, performance, and conformance evidence as applicable;
9. RFDS-017 `ai_contract.yaml` and lock file;
10. RFDS-018 bench contract or template when applicable;
11. RFDS-019 inventory, vectors, traces, matrices, and summary;
12. generated Libdoc and API manifest;
13. README, guides, examples, scripts, and GitHub Pages source/build evidence;
14. known-risks register;
15. release manifest, checksums, SBOM, and provenance evidence when required by RFDS-005 or RFDS-011;
16. supported Python, Robot Framework, operating-system, transport, device-model, and firmware matrix.

Missing mandatory input shall be recorded as a finding. The review shall not infer a PASS from the absence of evidence.

---

## 8. Required review outputs

The `review/` directory shall contain, directly or through equivalent current files:

```text
review/
├── README.md
├── vYY.RR_code_review.md
├── vYY.RR_architecture_review.md
├── vYY.RR_robot_api_review.md
├── vYY.RR_documentation_review.md
├── vYY.RR_release_readiness.md
├── requirement_traceability.md
├── known_risks.md
├── findings.yaml
└── review_evidence_manifest.json
```

For phase-and-gate versions, the project may use `vYY.PP.GG_*` names.

The release-readiness review shall include:

- reviewed archive filename and checksum;
- reviewed source revision;
- review date;
- reviewers and approver;
- scope and claimed release status;
- environment used for verification;
- checklist result by review domain;
- findings and corrective actions;
- quality score;
- blocking-rule evaluation;
- residual risks and waivers;
- final verdict;
- conditions for promotion or re-review.

---

## 9. Finding severity

Only the following severities shall be used.

### 9.1 CRITICAL

A Critical finding is a defect or omission that can cause one or more of:

- unsafe physical behaviour or failure to reach the declared safe state;
- uncontrolled voltage, current, power, temperature, motion, pressure, relay topology, or other hazardous output;
- false PASS or materially incorrect measurement/result reporting;
- silent command corruption, wrong channel/resource control, or incorrect unit conversion;
- loss or corruption of user, calibration, or device data;
- security compromise, secret disclosure, malicious dependency execution, or release tampering;
- indefinite blocking in a safety-relevant or release-essential operation;
- package identity or provenance failure that prevents determining what code was released;
- a known production defect with no reliable containment.

Any open Critical finding blocks every production or conditional-production verdict.

### 9.2 MAJOR

A Major finding is a defect or omission that materially affects:

- supported functionality;
- public API compatibility;
- protocol correctness or recovery;
- deterministic installation or operation;
- required test or HIL evidence;
- RFDS-019 conformance;
- AI-contract correctness;
- documentation needed for safe or correct use;
- packaging, version consistency, or release reproducibility;
- maintainability in a way likely to cause production defects.

A Major finding normally blocks production release. A waiver may be considered only under Section 22.

### 9.3 MINOR

A Minor finding has limited impact and does not prevent safe, correct use of the supported release scope. Examples include localized documentation defects, non-blocking code-quality issues, incomplete optional examples, or low-risk maintainability improvements.

Minor findings shall have an owner and disposition but may remain open at release when the residual risk is accepted.

### 9.4 NOTE

A Note is an observation, recommendation, or future improvement without a current nonconformity.

---

## 10. Checklist item statuses

Every checklist item shall use one of:

- **PASS** — requirement verified with sufficient evidence;
- **FAIL** — requirement not met;
- **PARTIAL** — some required aspects are met but the requirement is incomplete;
- **NOT VERIFIED** — evidence was not available or verification was not performed;
- **NOT APPLICABLE** — requirement does not apply and a reason is recorded;
- **WAIVED** — requirement is not met but an authorized, time-bounded waiver has been approved.

`NOT VERIFIED` shall not be treated as PASS. For a mandatory production criterion, `NOT VERIFIED` is release-blocking.

---

## 11. Review Domain A — Release identity and package integrity

Verify that:

1. the archive follows `rf_<driver_name>_v<year>.<release>.zip` or the currently approved RFDS release naming rule;
2. the archive contains exactly one stable root named `rf_<driver_name>/`;
3. archive name, Python package version, driver constant, README, history, release notes, AI contract, generated API, and manifests identify the same revision;
4. Python-normalized version forms are documented where they differ from display versions;
5. the archive is generated from a clean, identified source revision;
6. checksums are generated after the final archive is built;
7. the reviewed archive checksum matches the promoted artifact;
8. the release manifest lists included files and versions;
9. temporary files, local results, credentials, private addresses, caches, virtual environments, and editor artifacts are excluded;
10. required licence, governance, support, security, and contribution files are present;
11. wheel and source/archive content are consistent when multiple artifacts are released;
12. clean extraction does not depend on files outside the stable root.

**Blocking examples:** wrong root folder, inconsistent release version, unreviewed rebuilt archive, missing mandatory package content, secret included in archive.

---

## 12. Review Domain B — Installation, import, and basic operation

Verify on each claimed primary platform, or on the approved compatibility matrix, that:

1. a clean virtual environment can be created;
2. production and development dependencies install using documented commands;
3. dependency resolution is bounded and reproducible enough for the support policy;
4. the package builds successfully;
5. the wheel installs successfully when a wheel is provided;
6. the library imports in Python;
7. Robot Framework imports the library;
8. Libdoc generation succeeds without import side effects;
9. no hardware connection or output activation occurs merely from importing the module;
10. the minimal simulated or safe identity workflow executes;
11. uninstall/reinstall does not leave hidden required state;
12. scripts resolve paths from their own location and work outside the repository working directory.

**Blocking examples:** clean install fails, Robot import fails, import activates hardware, documented quick start is not reproducible.

---

## 13. Review Domain C — Architecture and maintainability

Verify that:

1. Robot Framework adapter, device semantics, protocol mapping, and transport responsibilities are separated;
2. the public Robot adapter does not duplicate protocol logic;
3. raw transport details are not required in normal Robot tests except documented resource configuration;
4. state ownership and state transitions are explicit;
5. connection/session ownership is explicit;
6. cleanup behaviour is defined for normal close, failed connection, keyword failure, suite abort, and process exit where practical;
7. retry, timeout, and recovery policy is implemented at the correct layer;
8. protocol knowledge has a single authoritative implementation location;
9. device-specific and bench-specific configuration is not hard-coded into reusable logic;
10. dependencies flow in one direction without circular or test-only production coupling;
11. core logic can be tested without Robot Framework or uncontrolled hardware where practical;
12. extension points do not expose unstable internals as public API;
13. concurrency and multi-session behaviour are defined and conservative by default;
14. files, modules, classes, and functions have coherent responsibilities;
15. complex logic is documented and covered by focused tests;
16. approved architectural exceptions are recorded with rationale and risk.

**Blocking examples:** protocol duplicated across conflicting paths, session leak after connection failure, hidden global state causing cross-test contamination, architecture prevents deterministic testing of critical logic.

---

## 14. Review Domain D — Public Robot Framework API

Verify that:

1. only intended keywords are exported;
2. keywords are discoverable and unique after Robot Framework normalization;
3. names follow RFDS-002 conventions and are consistent with equivalent driver classes;
4. argument order, names, defaults, units, enums, and accepted types are documented;
5. aliases and deprecations are explicit;
6. minor releases preserve compatible names and signatures unless an approved exception exists;
7. return values are Robot Framework-compatible and stable;
8. verification keywords produce actionable failures;
9. setup and teardown keywords are usable without private helper calls;
10. connection keywords support the documented transport-neutral workflow where required;
11. keyword documentation states preconditions, postconditions, side effects, risk, timing, and failure behaviour;
12. unsupported capabilities fail explicitly rather than silently doing nothing;
13. raw protocol access, when exposed, is clearly marked diagnostic/high risk and does not bypass safety without warning;
14. the API manifest, Libdoc, README, examples, tests, and RFDS-017 contract agree;
15. public keyword additions, changes, aliases, deprecations, and removals are recorded in history and release notes.

**Blocking examples:** missing keyword used by documented workflows, accidental public method exposure, undocumented breaking change, wrong return type, keyword reports success after failed device operation.

---

## 15. Review Domain E — Transport and protocol correctness

Verify that:

1. supported transports match documentation and package dependencies;
2. open, read, write, query, transaction, and close semantics are bounded by finite timeouts;
3. terminators, encodings, addresses, channels, checksums, byte order, and framing are correct;
4. command/query serialization preserves units and precision;
5. raw responses are validated before semantic conversion;
6. malformed, incomplete, stale, or unexpected responses are rejected;
7. command-only operations do not wait for undefined responses;
8. transport errors are not converted into success;
9. partial connection failures close and reset acquired resources;
10. transport tracing can observe the device boundary without changing functional behaviour;
11. simulator or replay behaviour preserves the relevant real protocol boundary;
12. vendor SDK calls are mapped and observed with equivalent rigor;
13. reconnect and session reset behaviour are defined;
14. representative protocol operations are verified on a real device when safe and practical;
15. RFDS-019 mandatory vectors, traces, matrices, and acceptance criteria pass.

**Blocking examples:** wrong command or frame, parser accepts malformed response as valid, query reads mismatched response, timeout can block indefinitely, RFDS-019 missing or failing for supported device-facing keywords.

---

## 16. Review Domain F — Errors, diagnostics, retry, and recovery

Verify that:

1. exceptions follow RFDS-007 taxonomy;
2. transport, protocol, device, validation, state, configuration, timeout, and safety failures remain distinguishable;
3. error messages identify operation, resource/alias, relevant arguments, and recovery guidance without exposing secrets;
4. invalid user values are rejected before transmission when appropriate;
5. device-rejected values are reported with the original device error where available;
6. retries are limited, observable, and used only for operations safe to repeat;
7. non-idempotent operations are not retried without explicit protection;
8. timeout behaviour is deterministic;
9. recovery leaves the driver in a documented state;
10. a known-good operation is verified after recoverable faults;
11. error queues or status registers are handled according to device semantics;
12. diagnostics export records versions, configuration, state, recent errors, and logs with secrets redacted;
13. cleanup errors are not silently discarded when they affect safety or resource release;
14. regression tests exist for corrected failures.

**Blocking examples:** malformed error response interpreted as “no error,” infinite retry, unsafe repeated command, recovery claims success while session is unusable, critical cleanup failure hidden.

---

## 17. Review Domain G — Safety, limits, and resource ownership

Verify that:

1. safety responsibilities are assigned to keyword, driver, device, fixture, bench, test plan, or operator layers;
2. connection and initialization do not unintentionally energize outputs or alter hazardous state;
3. safe limits are configurable, validated, documented, and represented in RFDS-017/RFDS-018 where applicable;
4. unsafe ranges, channel combinations, relay paths, or command sequences are prohibited or explicitly controlled;
5. manual actions and physical reconfiguration are visible and cannot be silently assumed;
6. normal teardown reaches the declared safe state;
7. failure, abort, timeout, and emergency paths attempt the safest achievable state;
8. the driver does not claim a safe state that it cannot verify or enforce;
9. disconnect semantics distinguish logical session closure from physical output state;
10. resources requiring exclusive ownership are declared and locked or otherwise protected;
11. concurrency is disabled unless safe behaviour is demonstrated;
12. current, voltage, power, temperature, pressure, motion, relay, and other applicable risks are reviewed;
13. HIL profiles declare allowed and prohibited operations;
14. HIL tests preserve evidence of startup state, limits, cleanup, and final state;
15. known safety assumptions and residual risks are prominent in README, guides, contracts, and review records.

**Blocking examples:** missing safe teardown for controllable output, wrong-channel actuation, unbounded output, hidden hazardous default, unverified safety claim, concurrent access can produce unsafe state.

---

## 18. Review Domain H — Configuration, state, and resources

Verify that:

1. configuration schema defines names, types, units, defaults, limits, and required values;
2. safe reusable defaults are separated from bench-specific resource assignments;
3. precedence among constructor arguments, Robot variables, environment variables, and files is documented;
4. unknown keys are handled deterministically;
5. configuration can be exported in normalized form with secrets redacted;
6. local paths, real credentials, private bench addresses, serial numbers, and user names are not committed as reusable defaults;
7. aliases, sessions, channels, and resources have deterministic lifecycle rules;
8. repeated connect/disconnect and failed connect do not leave stale state;
9. configuration changes that require reconnect are enforced or documented;
10. calibration, correction, or persistent device files are versioned and protected from accidental overwrite where applicable;
11. multi-session and multi-channel isolation are tested where supported;
12. resource conflict rules align with RFDS-017 and RFDS-018.

---

## 19. Review Domain I — Tests, coverage, and evidence

Verify that the applicable test layers are present and current:

1. static analysis and packaging checks;
2. Python unit tests;
3. protocol serialization and parser tests;
4. transport-adapter tests;
5. integration tests;
6. deterministic simulator or replay tests;
7. Robot Framework acceptance tests;
8. RFDS-019 conformance tests;
9. real-device/HIL tests;
10. safety and recovery tests;
11. regression tests for corrected defects;
12. compatibility tests;
13. performance, soak, memory, or concurrency tests where required.

For test quality, verify that:

14. tests assert meaningful results rather than only absence of exceptions;
15. failure paths and boundary values are covered;
16. tests are independent and declare prerequisites;
17. hardware tests are disabled by default and require explicit enablement and resources;
18. hardware tests never silently fall back to simulation;
19. skipped and excluded tests have reasons;
20. expected failures are not used to hide unresolved defects;
21. coverage is measured against the correct production code;
22. coverage thresholds follow RFDS-009 or the approved task;
23. coverage does not replace protocol or HIL evidence;
24. evidence records driver, Python, Robot Framework, OS, transport, simulator/device identity, firmware, configuration profile, and safety limits;
25. result totals in README, review, history, and reports agree;
26. test reports can be reproduced using packaged scripts;
27. evidence corresponds to the exact release candidate.

**Blocking examples:** mandatory tests fail, results are stale or from different bytes, no HIL evidence for a production hardware claim, skipped mandatory conformance tests, false coverage caused by excluding critical modules.

---

## 20. Review Domain J — Hardware qualification, performance, and compatibility

Verify, as applicable, that:

1. representative supported device models and firmware are identified;
2. real-device identity and transport are captured;
3. representative command classes and workflows execute on hardware;
4. physical state/readback confirms device-side operation where feasible;
5. startup, disconnect, abort, and recovery behaviour are observed;
6. unsupported models, cards, modules, firmware, or transport combinations are explicit;
7. timing, stabilization, and timeout values are supported by evidence;
8. repeated operation does not show resource leakage or state drift;
9. long-duration, stress, throughput, memory, or concurrency tests exist when required by scope;
10. supported Python, Robot Framework, dependency, OS, architecture, transport, device, and firmware combinations are listed;
11. minimum and maximum supported versions are tested or justified;
12. optional dependencies fail gracefully when absent;
13. deprecation and migration policy is documented;
14. known compatibility limitations are reflected consistently across documentation and contracts.

A driver that controls real hardware shall not receive an unconditional production verdict solely from simulator evidence unless its released scope explicitly excludes physical-device support.

---

## 21. Review Domain K — AI contracts and traceability

Verify that:

1. RFDS-017 files exist at the required paths;
2. the lock is valid and generated from the released contract;
3. identity and version match the release;
4. every intended public keyword has a capability entry;
5. capability signatures match the library and Libdoc;
6. inputs, outputs, preconditions, postconditions, side effects, risk, timing, stabilization, retry, errors, and resources are complete;
7. state-machine references are valid;
8. setup and teardown workflows use existing public keywords;
9. limitations and UNKNOWN handling are explicit;
10. verification objectives have usable pass/fail oracles;
11. protocol intent aligns with RFDS-019 vectors;
12. safety rules align with implementation and documentation;
13. RFDS-018 template or deployed bench contract is present when required;
14. bench topology, shared resources, signal graph, preferred measurement sources, scheduling, and global safety are not incorrectly invented inside the single-driver contract;
15. requirement traceability links requirements to code, tests, documentation, contracts, protocol evidence, hardware evidence, review findings, and history;
16. no requirement is marked complete without implementation and test evidence;
17. deferred and not-applicable requirements have reasons and owners where appropriate.

**Blocking examples:** stale AI contract describes nonexistent keyword, wrong safety semantics, invalid lock, missing protocol vector mapping, traceability claims hardware-tested without hardware evidence.

---

## 22. Review Domain L — Documentation, examples, scripts, and GitHub Pages

Verify that:

1. README identifies purpose, supported devices, release version, compatibility, transports, installation, quick start, safety, HIL status, limitations, and documentation links;
2. README does not contradict code, AI contract, examples, or release evidence;
3. Libdoc is generated from the released library;
4. GitHub Pages builds strictly without broken links or stale generated API content;
5. installation and PyCharm/Robot Framework guides are current for Windows and Linux;
6. hardware setup separates reusable guidance from private bench configuration;
7. troubleshooting covers import, permission, resource, vendor-runtime, timeout, protocol, and recovery problems;
8. at least ten numbered, complete Robot Framework examples are present unless an approved exception exists;
9. examples use only supported public APIs unless explicitly marked as diagnostics;
10. every example states purpose, mode, prerequisites, variables, setup, teardown, expected result, safety limits, and exact run command;
11. examples avoid hard-coded personal paths, credentials, private addresses, and uncontrolled hardware defaults;
12. safe cleanup is visible in every hardware-changing example;
13. Windows PowerShell, Windows batch where required, and Linux shell scripts are present and current;
14. scripts can run one example and the complete example set;
15. simulation examples run in CI where practical;
16. release notes and history describe public API, behaviour, safety, dependency, compatibility, test, and documentation changes;
17. documentation clearly distinguishes simulated, protocol-conformant, and physically validated claims.

**Blocking examples:** stale README for another version, unsafe example, fewer than ten examples without approved exception, scripts cannot run documented workflows, GitHub Pages exposes outdated API.

---

## 23. Review Domain M — Security, dependencies, and release provenance

Verify that:

1. no credentials, tokens, private keys, passwords, or private bench data are present in source, history, tests, examples, traces, reports, or archive metadata;
2. logs and diagnostics redact secrets;
3. dependencies are declared, reviewed, and constrained according to the support policy;
4. dependency licences are compatible with the project licence;
5. known material vulnerabilities are reviewed and dispositioned;
6. CI and release workflows use minimum permissions;
7. third-party actions are pinned according to project policy;
8. release creation is deterministic or sufficiently reproducible to detect unexpected differences;
9. release manifest, SBOM, checksums, and provenance are generated where required;
10. build and release scripts do not download or execute unverified content without control;
11. archive extraction is safe from path traversal and unexpected executables;
12. generated evidence does not disclose sensitive device identifiers when policy requires redaction;
13. raw protocol or file-upload capabilities validate paths, sizes, and inputs appropriate to their risk;
14. security limitations and reporting procedure are documented.

**Blocking examples:** committed secret, known exploitable dependency with no containment, mutable unreviewed release workflow, checksum generated before final artifact mutation.

---

## 24. Code-review method

The code review shall:

1. identify all changed files and symbols;
2. determine behavioural impact, not only textual diff size;
3. trace each changed public behaviour to tests and documentation;
4. inspect neighbouring code affected by shared state, inheritance, helpers, configuration, or transport changes;
5. verify typing and documentation for public interfaces;
6. review all exception swallowing, broad catches, retries, waits, loops, threads, locks, callbacks, and cleanup paths;
7. review numeric conversion, units, rounding, limits, enum mapping, channel indexing, masks, framing, and parsing;
8. review file, network, serial, VISA, USB, CAN, Modbus, SDK, and subprocess boundaries as applicable;
9. search for hard-coded resources, credentials, unsafe defaults, TODO/FIXME markers, disabled tests, debug prints, and unreachable code;
10. verify that corrections include regression tests;
11. record file-specific findings with severity, evidence, correction, and residual risk.

A code review that only reports style or test totals is insufficient for production readiness.

---

## 25. Evidence quality rules

Evidence used for PASS shall be:

- attributable to the exact release candidate;
- dated or otherwise identifiable;
- reproducible by documented command or workflow;
- sufficiently complete to support the conclusion;
- stored at a stable path or referenced by checksum;
- sanitized of secrets;
- consistent with other release records.

Evidence shall distinguish:

- static inspection;
- simulated execution;
- protocol-boundary conformance;
- real-device execution;
- independent physical verification.

A statement such as “tests passed” without test reports, environment, version, and scope is not sufficient production evidence.

---

## 26. Scoring model

### 26.1 Domain weights

| Domain | Weight |
|---|---:|
| A. Release identity and package integrity | 8 |
| B. Installation, import, and basic operation | 7 |
| C. Architecture and maintainability | 8 |
| D. Public Robot Framework API | 9 |
| E. Transport and protocol correctness | 10 |
| F. Errors, diagnostics, retry, and recovery | 8 |
| G. Safety, limits, and resource ownership | 10 |
| H. Configuration, state, and resources | 6 |
| I. Tests, coverage, and evidence | 10 |
| J. Hardware qualification, performance, and compatibility | 7 |
| K. AI contracts and traceability | 6 |
| L. Documentation, examples, scripts, and GitHub Pages | 6 |
| M. Security, dependencies, and release provenance | 5 |
| **Total** | **100** |

### 26.2 Item scoring

Each applicable checklist item shall be scored:

- PASS = 1.0;
- PARTIAL = 0.5;
- FAIL = 0.0;
- NOT VERIFIED = 0.0;
- WAIVED = 0.5 maximum unless the approver assigns a lower value;
- NOT APPLICABLE = removed from that domain’s denominator.

For each domain:

```text
Domain achievement = obtained applicable item points / maximum applicable item points
Weighted domain score = domain achievement × domain weight
```

Overall score:

```text
Production readiness score = sum of weighted domain scores
Normalized score = production readiness score / 10
```

Example: 94 points equals 9.4/10.

### 26.3 Score interpretation

| Score | Interpretation |
|---:|---|
| 9.5–10.0 | Production-grade with strong evidence and low residual risk |
| 9.0–9.49 | Production-ready when all blocking rules pass |
| 8.0–8.99 | Release candidate; further correction or evidence required |
| 7.0–7.99 | Development quality; material gaps remain |
| Below 7.0 | Not suitable for release review |

The score is informative. The verdict shall be determined by both score and blocking rules.

---

## 27. Mandatory release-blocking rules

A production release shall be blocked when any of the following applies:

1. an open Critical finding exists;
2. an open Major finding affects safety, correctness, protocol behaviour, error reporting, data integrity, security, public API compatibility, or release identity;
3. the release score is below 9.0/10;
4. any of Domains D, E, F, G, or I scores below 85%;
5. any other applicable domain scores below 70%;
6. the final archive differs from the reviewed archive;
7. clean installation, Python import, Robot import, or basic workflow fails;
8. mandatory tests fail or mandatory evidence is NOT VERIFIED;
9. RFDS-019 acceptance fails for supported device-facing public keywords;
10. a driver claiming physical-device production support lacks representative HIL evidence;
11. safe initialization, teardown, abort, or recovery is absent or unverified for controllable hazardous state;
12. public API, AI contract, documentation, examples, and release version materially disagree;
13. the package includes secrets or uncontrolled private bench data;
14. a breaking public API change lacks approved migration and release classification;
15. required history, review, traceability, known-risks, or release evidence is missing;
16. checksums or provenance do not identify the exact artifact proposed for release.

---

## 28. Waiver rules

A waiver shall not be used for:

- an open Critical finding;
- a known unsafe state or missing emergency containment;
- false PASS or materially wrong result reporting;
- known protocol corruption affecting supported operations;
- committed secrets or active critical security exposure;
- inability to identify the released code;
- mandatory RFDS-019 failure for a supported keyword;
- absent HIL evidence when unconditional physical-device production support is claimed.

A Major finding may be waived only when all of the following are true:

1. the affected feature or environment is clearly excluded from the supported release scope;
2. safe and correct use of the supported scope is not affected;
3. the limitation is prominent in README, documentation, AI contract, compatibility matrix, and release notes;
4. a reliable containment or feature-disable mechanism exists;
5. a risk owner and release approver accept the residual risk;
6. the waiver has an expiry version or date;
7. a correction plan and tracking reference exist.

Every waiver shall identify the exact requirement, finding, scope, rationale, mitigation, owner, approver, expiry, and re-review trigger.

---

## 29. Production-readiness verdicts

Only the following final verdicts are permitted.

### 29.1 APPROVED FOR PRODUCTION

Permitted only when:

- all mandatory blocking rules pass;
- score is at least 9.0/10;
- no open Critical finding exists;
- no unwaived blocking Major finding exists;
- the claimed support scope is fully evidenced;
- the exact archive is approved.

### 29.2 APPROVED WITH RESTRICTED SCOPE

Permitted only when:

- all supported-scope blocking rules pass;
- exclusions are technically enforced or unmistakably documented;
- no Critical finding exists;
- no safety, false-result, protocol-corruption, security, or release-identity defect is waived;
- every waiver meets Section 28;
- score is at least 9.0/10 for the supported scope.

The verdict shall state the exact permitted models, firmware, transports, operating systems, features, and hardware profile.

### 29.3 RETURN TO DEVELOPMENT

Required when:

- one or more blocking rules fail;
- evidence is incomplete;
- score is below 9.0/10;
- mandatory corrections are feasible within the project;
- the candidate may be reconsidered after correction and re-review.

### 29.4 REJECTED AS RELEASE BASELINE

Used when the submitted package is structurally, technically, or evidentially unsuitable as the basis of a production release and requires substantial rework or replacement.

### 29.5 REVIEW INVALID

Used when the exact candidate cannot be identified, the evidence belongs to different code, the archive changes during review, or the review cannot establish a trustworthy basis for a verdict.

---

## 30. Required review workflow

### Step 1 — Freeze candidate

- identify archive, source revision, version, and checksum;
- prohibit candidate mutation during review;
- record claimed support scope.

### Step 2 — Inventory

- list package files;
- list public keywords;
- list capabilities, transports, models, firmware, dependencies, and examples;
- identify mandatory and conditional RFDS requirements.

### Step 3 — Reproduce build and install

- create a clean environment;
- build and install package artifacts;
- import in Python and Robot Framework;
- generate Libdoc and API manifest.

### Step 4 — Execute automated validation

- run static, unit, integration, simulator/replay, Robot, compatibility, and RFDS-019 suites;
- capture versions and result evidence;
- review skips and exclusions.

### Step 5 — Execute hardware validation

- apply approved RFDS-018 bench profile;
- record identity, firmware, transport, fixture, safety limits, startup state, and cleanup state;
- execute representative and risk-based workflows;
- preserve evidence.

### Step 6 — Perform source and architecture review

- inspect changed and affected code;
- verify state, resource, timeout, error, retry, recovery, concurrency, and cleanup behaviour;
- confirm regression tests for corrected defects.

### Step 7 — Review API and contracts

- compare library, Libdoc, API manifest, examples, RFDS-017, and RFDS-019 inventory;
- validate signatures, return types, protocol mapping, risks, errors, and states.

### Step 8 — Review documentation and package

- verify README, guides, examples, scripts, GitHub Pages, history, release notes, manifests, security files, and package layout;
- run representative example scripts from outside the repository working directory.

### Step 9 — Classify findings

- assign severity and checklist domain;
- record evidence, impact, required correction, owner, and residual risk;
- identify blockers.

### Step 10 — Correct and re-test

- implement corrections;
- add regression tests;
- regenerate invalidated evidence;
- rebuild and re-freeze the archive;
- re-review changed and affected areas.

### Step 11 — Score and decide

- calculate domain and total scores;
- evaluate all blocking rules;
- document waivers and restricted scope;
- issue one permitted verdict.

### Step 12 — Promote exact artifact

- verify final checksum;
- sign or publish provenance where required;
- ensure the promoted artifact is byte-identical to the approved artifact;
- preserve the final review in the release.

---

## 31. Minimum release-readiness report template

```markdown
# <driver> Production Readiness Review

## Candidate
- Archive:
- SHA-256:
- Source revision:
- Driver version:
- Review date:
- Reviewer:
- Approver:
- Claimed support scope:

## Environment
- Operating system:
- Python:
- Robot Framework:
- Transport/runtime:
- Simulator:
- Device model/serial/firmware:
- Bench profile:

## Verification performed
- Build/install:
- Unit tests:
- Integration tests:
- Robot tests:
- RFDS-019:
- HIL:
- Performance/soak/concurrency:
- Documentation/GitHub Pages:
- Example scripts:
- Security/release integrity:

## Domain scores
| Domain | Weight | Achievement | Weighted score | Status |
|---|---:|---:|---:|---|

## Findings
| ID | Severity | Domain | Finding | Evidence | Required correction | Status |
|---|---|---|---|---|---|---|

## Blocking-rule evaluation
| Rule | Result | Evidence or reason |
|---|---|---|

## Residual risks and waivers

## Final score
- Points: __ / 100
- Normalized: __ / 10

## Verdict
APPROVED FOR PRODUCTION / APPROVED WITH RESTRICTED SCOPE / RETURN TO DEVELOPMENT / REJECTED AS RELEASE BASELINE / REVIEW INVALID

## Conditions and next actions
```

---

## 32. Machine-readable findings

`review/findings.yaml` should use equivalent information to:

```yaml
review:
  document_id: RFDS-010
  specification_version: "1.0"
  driver: rf_example
  release_version: "26.01"
  archive: rf_example_v26.01.zip
  archive_sha256: "..."
  source_revision: "..."

findings:
  - id: RFDS010-REV-001
    severity: MAJOR
    domain: E
    requirement: RFDS-019 Section 15
    title: Missing outbound protocol evidence
    evidence:
      - review/evidence/conformance_summary.md
    impact: Device-facing keyword behaviour is not proven.
    required_correction: Add and execute the mandatory protocol vector.
    owner: implementation-owner
    status: OPEN
    residual_risk: HIGH
    waiver: null

score:
  points: 0
  normalized: 0.0

verdict: RETURN_TO_DEVELOPMENT
```

Machine-readable findings shall not replace the human-readable review.

---

## 33. Review consistency checks

Before issuing the verdict, verify that:

1. test totals agree across reports and review text;
2. release versions agree across all artifacts;
3. the public keyword count agrees across Libdoc, API manifest, RFDS-017, and RFDS-019 inventory;
4. supported model, firmware, transport, Python, and Robot Framework claims agree;
5. HIL claims match recorded device evidence;
6. exclusions and known limitations appear consistently;
7. every PASS has evidence;
8. every FAIL, PARTIAL, NOT VERIFIED, or WAIVED item appears in findings or risk records;
9. every corrected Major or Critical finding has re-test evidence;
10. the reviewed checksum matches the final release archive.

Any unexplained inconsistency shall be classified at least Major when it affects release truth, supported scope, safety, API, or evidence validity.

---

## 34. Review checklist summary

A reviewer shall be able to answer **yes, with evidence** to all applicable questions before approving production release:

1. Is the exact release archive identified and immutable during review?
2. Does it contain the correct stable root and mandatory RFDS structure?
3. Are release versions consistent across every artifact?
4. Can the package be cleanly built, installed, imported, and documented?
5. Is the architecture layered and maintainable?
6. Is the public Robot Framework API intentional, stable, documented, and usable?
7. Are transport and protocol operations correct and finitely bounded?
8. Are malformed responses, timeouts, device errors, and disconnects handled correctly?
9. Does recovery restore a documented usable state?
10. Are safe initialization, limits, teardown, abort, and resource ownership defined and verified?
11. Are all applicable test layers present, passing, reproducible, and tied to this release?
12. Does RFDS-019 pass for every supported device-facing public keyword?
13. Is representative real-device evidence available for the claimed production scope?
14. Are performance, soak, and concurrency risks addressed where applicable?
15. Does RFDS-017 exactly match the released API and behaviour?
16. Is RFDS-018 bench information correct where integration is claimed?
17. Is requirement traceability complete and evidence-based?
18. Are at least ten safe, complete, runnable examples provided or formally excepted?
19. Are README, guides, scripts, Libdoc, GitHub Pages, history, and release notes current?
20. Are dependencies, secrets, licences, security risks, SBOM, checksums, and provenance controlled?
21. Are all findings classified, owned, and dispositioned?
22. Are no Critical or blocking Major findings open?
23. Is the score at least 9.0/10 and are critical domains above threshold?
24. Is the final promoted artifact byte-identical to the reviewed artifact?

---

## 35. Minimum definition of done

RFDS-010 is complete for a release when:

- the exact release candidate and checksum are recorded;
- all applicable review domains are evaluated;
- all mandatory build, install, test, conformance, and hardware evidence is reviewed;
- source, architecture, API, safety, documentation, package, AI-contract, compatibility, and security reviews are complete;
- findings are recorded with severity, evidence, owner, correction, and residual risk;
- corrections have regression evidence;
- score and domain thresholds are calculated;
- blocking rules are evaluated explicitly;
- waivers, restricted scope, and known risks are documented;
- one permitted verdict is issued;
- the promoted artifact matches the approved artifact;
- final review records are included in `review/` and referenced by history and release notes.

---

## 36. Goal

Provide a repeatable, evidence-based decision that an RFDS Robot Framework driver is safe, correct, supportable, reproducible, and sufficiently validated for its explicitly declared production scope.

The review shall make it impossible to confuse a promising development package, a simulator-only implementation, or a partially documented driver with a production-approved release.

---

## Appendix A — Recommended finding identifiers

Use:

```text
RFDS010-REV-001
RFDS010-REV-002
...
```

Device-specific projects may prefix the driver name while preserving a stable numeric identifier.

---

## Appendix B — Recommended correction priority

| Priority | Meaning |
|---|---|
| P0 | Immediate safety, correctness, security, data-integrity, or false-result correction |
| P1 | Required before production release |
| P2 | Required for full RFDS conformance but may be planned after a restricted-scope release only when waiver rules permit |
| P3 | Maintainability or usability improvement |

Priority does not replace severity. A Critical finding remains release-blocking regardless of planned correction date.

---

## Appendix C — Relationship to RFDS-019

RFDS-019 proves that declared public Robot Framework calls reach the intended protocol operation and correctly return applicable device responses.

RFDS-010 shall consume RFDS-019 evidence but shall not duplicate or weaken it. RFDS-010 adds the wider production-readiness decision covering architecture, safety, tests, hardware qualification, documentation, packaging, AI contracts, compatibility, security, provenance, and release governance.

A driver may pass RFDS-019 and still fail RFDS-010. A device-facing production driver shall not pass RFDS-010 when mandatory RFDS-019 conformance fails.
