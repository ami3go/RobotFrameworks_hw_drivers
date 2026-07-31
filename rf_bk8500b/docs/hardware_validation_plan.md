# Hardware-in-the-loop validation plan

## Bench record

Record instrument model, serial, firmware, interface, adapter part number, cable, host OS, Python version, and calibration status. Use an independent DMM and a protected source appropriate for the load rating.

## Mandatory evidence

- SCPI write/read terminators and maximum reliable command rate.
- Identity and version responses.
- Every stable setter plus readback at minimum, representative, and near-maximum values.
- Input OFF/ON/OFF with independent current observation.
- Short operation only on a protected low-energy fixture.
- Status/protection bits and destructive event-register behavior.
- Cable removal during read and during write.
- Host restart and device restart.
- Legacy request/response captures for each promoted command.
- Legacy checksum, response status location, address, scaling, and error return codes.
- Model/firmware capability matrix.

Store captures under `docs/validation/captures/` and reference evidence IDs from the command policy matrix.
