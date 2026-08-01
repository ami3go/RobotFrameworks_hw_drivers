# Keyword reference

The machine-readable risks, preconditions, timing, errors, and resource locks
are authoritative in `ai/phidget_relay_ai_contract.yaml`.

| Keyword | Purpose |
|---|---|
| Connect Relays | Attach eight outputs using device A/B serial numbers |
| Disconnect Relays | Safely open and release all output handles |
| Open/Close Relay | Control one logical channel |
| Set Relay State | Set one channel using boolean or readable state text |
| Get Relay State | Return OPEN or CLOSED commanded state |
| Open/Close All Relays | Apply one state across the bank |
| Set Relay Pattern | Apply CH1..CH8 from an eight-digit binary string |
| Set Multiple Relays | Apply a Robot dictionary of selected states |
| Get All Relay States | Return all commanded states as a dictionary |
| Pulse Relay | Close, wait, and open in a `finally` block |
| Get Relay Mapping | Show serial/output behind each logical channel |
| Relay Should Be Open/Closed | Assert one commanded output state |
| Get Connection Status | Report whether all eight handles are registered |
| Get Driver Information | Return version, serials, polarity, and state evidence |
| Emergency Open All Relays | Best-effort software safe-state action |

Robot Framework's Libdoc can generate the authoritative API from docstrings:

```console
python -m robot.libdoc rf_phidget_relay.PhidgetRelayLibrary docs/libdoc.html
```
