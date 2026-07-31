# Agent Instructions

Treat `api/public_api.yaml` as the public API authority, `ai/ai_contract.yaml` as
the AI semantics authority, and `tests/conformance/data/protocol_vectors.yaml`
as the protocol-call authority. Any public keyword change must update all three,
the examples, history, review, and release artifacts in the same revision.

Never infer hardware model limits or digital-output mappings. Preserve UNKNOWN
until real-device evidence is recorded. Use `SIM::` resources for autonomous
validation. Do not connect to physical hardware during import, construction,
plugin discovery, metadata inspection, or documentation generation.
