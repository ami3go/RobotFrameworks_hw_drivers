# Migration from the Python driver

Use Robot keywords instead of calling driver methods directly. Range, NPLC, aperture, filter, trigger, terminal, Boolean, and duration values may be supplied in Robot-friendly string form. Scalar measurement keywords validate the result; use `Get Last DMM Reading` when full metadata is needed.
