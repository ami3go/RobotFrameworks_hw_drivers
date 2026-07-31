# RFDS-018 bench integration template

`bench/system_ai_contract.yaml` is a conservative RFDS-018 template for a laboratory
that includes this electronic-load driver. It is not an assertion that a particular
bench is wired or qualified.

The file contains all RFDS-018 sections:

- available drivers;
- physical topology;
- shared resources;
- signal graph;
- preferred measurement sources;
- requirement coverage;
- reusable multi-driver test templates;
- bench constraints;
- scheduling rules;
- global safety and emergency shutdown.

It remains marked `TEMPLATE_INCOMPLETE` because a single driver package cannot know the
actual power source, DUT ratings, wiring, fusing, fixture, DMM, emergency stop, or
calibration status. Copy it into the bench-level project, replace every `UNKNOWN`, add
the exact RFDS-017 contracts for all installed drivers, review the physical topology,
and only then change its status.
