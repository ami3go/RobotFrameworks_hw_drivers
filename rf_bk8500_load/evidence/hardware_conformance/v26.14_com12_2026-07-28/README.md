# Evidence bundle

This directory preserves the original Robot Framework output supplied from the
physical BK8500 conformance run and adds machine-readable indexes generated from
`output.xml`.

Files:

- `output.xml`, `log.html`, `report.html` — original Robot Framework evidence;
- `conformance_summary.md` — reviewed result and scope statement;
- `environment.json` — software, host, transport, and result metadata;
- `device_identity.json` — physical instrument identity;
- `keyword_coverage.csv` — one row per keyword/workflow test;
- `expected_negative_messages.json` — expected negative-path messages;
- `evidence_manifest.sha256` — SHA-256 hashes for integrity checking.
