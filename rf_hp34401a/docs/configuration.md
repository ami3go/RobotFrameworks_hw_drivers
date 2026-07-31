# Driver configuration

RFDS-014 JSON configuration is host-side only. Importing a profile never opens the DMM and never writes instrument non-volatile state. `config/default.json` is the safe disconnected default. User profiles are saved only by the explicit `Save Driver Configuration` keyword.
