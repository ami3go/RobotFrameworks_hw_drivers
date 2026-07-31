# RFDS-018 bench contract template

`system_ai_contract.yaml` is intentionally marked `TEMPLATE_INCOMPLETE`. A single
instrument driver cannot truthfully define the actual laboratory wiring, DUT ratings,
source limits, fixture, emergency stop, or calibration status.

Copy this file into the bench-level project, replace every `UNKNOWN`, add the exact
RFDS-017 contracts for the other installed drivers, and change `contract_status` only
after the physical topology and global safety workflow have been reviewed.
