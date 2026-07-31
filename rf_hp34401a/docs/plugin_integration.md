# Plugin integration

The package registers plugin ID `rf_hp34401a` in the `rfds.drivers` entry-point group. Metadata inspection and provider validation perform no hardware I/O. `create_library()` returns an unconnected `Hp34401ALibrary` instance and never falls back from hardware to simulation.
