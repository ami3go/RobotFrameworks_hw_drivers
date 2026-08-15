# Architecture

## Runtime layers

The active Robot entry point is `rf_hp34401a.Hp34401ALibrary`.

The 2026-08-16 remediation preserves the complete reviewed 26.07 keyword implementation in `rf_hp34401a/legacy_library.py` and places a small corrected facade in `rf_hp34401a/library.py`. The facade inherits all compatibility and measurement keywords and overrides only cross-cutting RFDS behavior: effective configuration application, runtime metadata, communication-health caching, evidence teardown, timeout enforcement, and public core accessors. This avoids rewriting or duplicating the mature 109-keyword implementation while making the corrected behavior explicit and reviewable.

The device core follows the same pattern. `hp34401a_dmm/legacy_driver.py` preserves the reviewed 1.2.8 SCPI implementation. `hp34401a_dmm/driver.py` subclasses it to expose explicit runtime-policy, communication-timeout, raw-response, and transport-metadata methods. The Robot layer therefore no longer needs direct access to the private transport object.

`SessionManager` owns named DMM aliases. The core driver owns SCPI sequencing, parsing, recovery, measurement safety, and transport interaction. This keeps one device-protocol implementation and prevents Robot-specific code from creating a second SCPI stack.

## RFDS-003 shared-core boundary

`rfds-core>=1.0,<2.0` is a mandatory runtime dependency and the plugin validates its installed version. Driver information, driver metadata, and RFDS evidence resolve the effective installed shared-core version at runtime.

Full RFDS-003 migration is **not yet claimed** because the authoritative shared `BaseInstrumentLibrary` implementation is not available in this repository/connected development environment. `Hp34401ALibrary` therefore does not yet inherit it. A local compatibility class or copied fork is intentionally not created because RFDS-003 defines `rfds-core` as a shared external authority.

When the authoritative package is supplied, the migration must integrate its lifecycle/session/timeout/diagnostic orchestration rather than merely adding a superficial base class to the current facade.

## Configuration architecture

`config/schema.json`, `config/schema.lock`, and `config/default.json` are the repository authorities and are mirrored into `rf_hp34401a/resources/configuration/` for installed-package access. Tests require the root and packaged copies to remain byte-identical.

`ConfigurationManager` verifies the schema lock before accepting configuration and validates documents with Draft 2020-12 JSON Schema. Resolved sources are tracked per settings leaf. The active facade applies the supported host policy to open/new sessions without opening hardware during import.

## Evidence architecture

`hp34401a_dmm/evidence.py` records one evidence run per Robot library instance. Run status is accumulated fail-closed: once an operation fails, later successful cleanup cannot change the final run back to `PASS`. The listener finalizes an unfinished run during suite/library cleanup, and diagnostic export records its export event before generating the integrity manifest.

## Compatibility layer

The RFDS canonical keywords coexist with the earlier DMM-specific names. Non-decorated Python compatibility methods support orchestration code written against earlier generic DMM method names. `ROBOT_AUTO_KEYWORDS` is disabled, so helper methods do not enlarge the Robot interface.

The effective public surface—not the physical contents of one source file—is the authority. Contract and RFDS-019 validators introspect the actual decorated inherited Robot methods so facade inheritance cannot hide or invent keywords.

## AI-contract layer

`ai/hp34401a_ai_contract.yaml` is the machine-readable semantic description of the driver. It includes exact keyword signatures, state/resource rules, error and recovery information, safety constraints, verification objectives, timing, retry, and planning metadata.

`ai/hp34401a_ai_contract.lock` hashes the normalized effective Robot surface. `scripts/validate_ai_contract.py` compares the installed/effective library surface with the RFDS-002 public API, RFDS-017 contract, RFDS-019 inventory, and lock.

RFDS-018 describes the complete bench and is intentionally supplied only as a template here. Actual wiring, shared resources, safety zones, and aliases must be verified by the bench repository/site configuration.
