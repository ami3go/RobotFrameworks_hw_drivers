# Release v26.6 change review matrix

| Change | Functional review | Architecture/API review | Documentation/test evidence | Result |
|---|---|---|---|---|
| Add `history/` | Release records are discoverable | No runtime impact | Structure test plus six history files | Pass |
| Add twelve examples | Simulated-safe workflows cover major functions | Uses existing public keywords only | Static syntax/keyword audit; launch scripts | Pass, execution pending Robot dependency |
| Add run scripts | Root and output paths are deterministic | No driver coupling | `bash -n`; structure test | Pass |
| Add setup guides | Covers PyCharm, venv, Robot, hardware, troubleshooting | Consistent with package layout | Link validation | Pass |
| Add GitHub Pages/CI | Documentation and tests have repository automation | Source package unchanged | Workflow YAML and local link review | Pass |
| Add licence | Matches declared MIT metadata | No API impact | Root `LICENSE` | Pass |
| Preserve fallback keyword metadata | Restores source-only conformance tests | Robot keyword surface unchanged | RFDS conformance tests | Pass |
| Reject duplicate alias | Prevents orphaned live transport | Earlier failure; no signature change | Unit regression | Pass |
| Close transport after failed identity | Prevents serial-handle leak | Original failure preserved | Unit regression | Pass |
| Update AI/release metadata | Planner sees current package and version | Contract revision incremented; lock regenerated | Contract conformance tests | Pass |
