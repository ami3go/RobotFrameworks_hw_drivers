# Known risks — v26.06

| Risk | Impact | Mitigation/status |
|---|---|---|
| Vendor VISA backends differ in clear, timeout, lock, USBTMC, and termination behavior. | Real-device behavior may differ from simulation. | Run the packaged VISA HIL profile for each supported backend; D0 until official Robot conformance and hardware evidence exist. |
| RS-232 cabling, DTR/DSR, baud, parity, data bits, stop bits, and instrument menu settings are installation-specific. | Connection or remote/local behavior may fail. | Use explicit serial profile and execute the serial HIL group. |
| Current terminal can open the DMM fuse or disturb a DUT. | Equipment damage or false result. | Current profile defaults disabled and requires an approved fused fixture. |
| Resistance, diode, and continuity modes on an energized DUT are unsafe or invalid. | Equipment damage or invalid data. | These HIL profiles default disabled and require a verified de-energized fixture. |
| Reset and self-test disturb active measurement state. | Test interruption. | Explicit high/medium-risk calls and separate disabled HIL profiles. |
| Raw SCPI bypasses high-level state tracking. | Unknown device state. | Disabled by default; explicit opt-in; calibration commands remain core-guarded. |
| Simulator cannot prove physical accuracy, cable behavior, instrument firmware behavior, or terminal wiring. | Overstated validation. | Release class D0; physical evidence explicitly pending. |
| Shared `rfds-core` v2 implementation is unavailable. | RFDS-003 v2 reusable base conformance cannot be claimed. | Optional dependency and documented deviation; local semantics tested. |
| Existing core is text-oriented rather than the RFDS-004 v2 canonical byte transport. | Full v2 transport conformance not proven. | Controlled architectural deviation; separate migration/HIL phase required. |
| Final Robot, Libdoc, MkDocs, and HIL evidence was not generated in this build container. | Final release qualification incomplete. | Run documented uv commands against exact extracted candidate. |
| GitHub Actions use major-version tags. | Workflow supply-chain immutability does not meet P1 hardening. | Pin actions to reviewed immutable SHAs before production promotion. |
| RFDS-018 template contains UNKNOWN bench facts by design. | Unsafe autonomous multi-driver planning if mistaken for deployed truth. | Keep authoritative deployed system contract in bench repository and resolve every safety/topology field. |
