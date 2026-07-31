# RFDS-018 Test-Bench Contract

The repository root contains `system_ai_contract.yaml`, a structurally complete RFDS-018 v1.0 template for a climate-chamber test bench.

It describes:

- available drivers and versions;
- chamber, DUT, reference sensor and network topology;
- exclusive chamber-volume and TCP resources;
- environmental signal flow;
- preferred control and reference measurements;
- requirement coverage and reusable workflows;
- operator actions, scheduling and stabilization rules;
- global forbidden sequences and emergency shutdown behavior.

The package cannot know the actual DUT, fixture, chamber model, laboratory emergency procedure or reference sensor. Those fields intentionally use `UNKNOWN`. Control-changing automation must remain disabled until the bench owner resolves every critical unknown.
