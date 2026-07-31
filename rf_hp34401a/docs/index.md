# RF HP34401A 26.06

RFDS Robot Framework driver for the HP/Agilent/Keysight 34401A DMM.

Release 26.06 fixes real-hardware API evidence bookkeeping. The official HIL launcher now registers a file-backed Robot listener, disabled fixture profiles are recorded during suite setup as `EXCLUDED`, and the summary is logged before acceptance is asserted. The complete 108-keyword public API remains unchanged.

**Qualification:** D0 development candidate. The user's prior physical run proved the real VISA connection and non-fixture lifecycle/status groups; rerun v26.06 to generate corrected per-keyword evidence.

Start with [Installation](installation.md), [Quick start](quick_start.md), and [Real-hardware all-API verification](real_hardware_api_verification.md).
