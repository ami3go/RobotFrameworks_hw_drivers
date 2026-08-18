Keysight
34970A/34972A
Command Reference
Notice: This document contains references to Agilent Technologies.
Agilent's former Test and Measurement business has become Keysight
Technologies. For more information, go to www.keysight.com.
This Help file contains reference information to help you program the
Keysight 34970A/34972A over a remote interface using the programming
language.
Introduction to the Command Language
Commands by Subsystem
Commands A-Z
Command Quick Reference
Error Messages
Factory Reset State
Instrument Preset State
Plug-In Module Reference Information

Related Information
For further information, click on the link of interest:
Libraries and Instrument Drivers
Keysight 34970A/34972A Documentation
Keysight 34972A Web Interface
Programming Examples
Contact Keysight Technologies
Trademarks
© Keysight Technologies, Inc. Version 2.00
2009-2014

Commands by Subsystem
ABORt
FETCh?
INITiate
INPut:IMPedance:AUTO
READ?
R?
UNIT:TEMPerature
CALCulate Subsystem
CALibration Subsystem
CONFigure Subsystem
DATA Subsystem
DIAGnostic Subsystem
DISPlay Subsystem
FORMat Subsystem Introduction
IEEE-488.2 Common Commands
INSTrument Subsystem Introduction
MEASure Subsystem
MEMory Subsystem
MMEMory Subsystem
OUTPut Subsystem
ROUTe Subsystem
SENSe Subsystem

SOURce Subsystem
STATus Subsystem
SYSTem Subsystem
TRIGger Subsystem

ABORt
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
ABORt

Description
This command aborts a measurement in progress from a scan.

Remarks
If a scan is in progress when the command is received, the scan
will not be completed and you cannot resume the scan from where
it left off. Note that if you initiate a new scan, all readings are
cleared from memory.
The *RST command will abort a measurement, clear the scan list,
and set all measurement parameters to their factory settings. The
Instrument Preset (SYSTem:PRESet command) also aborts a
measurement but it does not clear the scan list.

Example
The following command aborts the measurement in progress.
ABOR

See Also
*RST
SYSTem:PRESet

FETCh?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
FETCh?

Description
This command transfers readings stored in non-volatile memory to the
instrument's output buffer, where you can read them into your computer.
The readings stored in memory are not erased when you read them with
FETCh?. The format of the readings can be changed using
FORMat:READing commands.

Remarks
The FETCh? command will wait until the measurement is
complete to terminate.
Readings can be acquired during a scan using the multiplexer and
digital modules.
You can store at least 50,000 readings in memory and all readings
are automatically time stamped. If memory overflows, the new
readings will overwrite the first (oldest) readings stored; the most
recent readings are always preserved.
Each time you start a new scan, the instrument clears all readings
(including alarm data) stored in reading memory from the previous
measurement. Therefore, the contents of memory are always from
the most recent measurement.
When you abort a measurement (see ABORt command), the
instrument will terminate any reading in progress (readings are not
cleared from memory). The readings remain in memory and can
be read until you clear them or initiate a new scan.
The output from this command is affected by the settings of the
FORMat:READing commands. Depending on the formats
selected, each reading may or may not be stored with
measurement units, time stamp, channel number, and alarm
status information.
The *RST command will clear the scan list and set all
measurement parameters to their factory settings. The Instrument
Preset (SYSTem:PRESet command) will not clear the scan list;
however, this command will clear reading memory and all stored
statistical data.
The instrument clears all readings from memory when a new scan
is initiated, when any measurement parameters are changed

(CONFigure and SENSe commands), and when the triggering
configuration is changed (TRIGger commands).
The instrument clears all readings from memory after a Factory
Reset (*RST command) or after an Instrument Preset
(SYSTem:PRESet command).

Return Format
The command transfers all readings from memory (with formatting as set
by the FORMat:READing commands) but does not erase them. Multiple
responses are separated by commas.

Example
The following program segment shows how to use the FETCh?
command with the CONFigure and INITiate commands. The
ROUTe:SCAN command puts the two channels into the scan list (and
redefines the scan list). The INITiate command places the instrument in
the "wait-for-trigger" state, scans the specified channels when the rear-
panel Ext Trig Input line is pulsed low, and then sends the readings to
memory. The FETCh? command transfers the readings from memory to
the instrument's output buffer.
CONF:VOLT:DC 10,0.003,(@103,108)
ROUT:SCAN (@103,108)
TRIG:SOUR EXT
INIT
FETC?
Typical Response: +4.27150000E-03,+1.32130000E-03

See Also
INITiate
ROUTe:SCAN

INITiate
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
INITiate

Description
This command changes the state of the triggering system from the "idle"
state to the "wait-for-trigger" state. Scanning will begin when the
specified trigger conditions are satisfied following the receipt of the
INITiate command. Readings are stored in the instrument's internal
reading memory. Note that the INITiate command also clears the
previous set of readings from memory.
If a scan list is currently defined (see ROUTe:SCAN command), the
INITiate command performs a scan of the specified channels.
If a scan list is not currently defined, the INITiate command fails.

Remarks
Storing readings in memory using the INITiate command is
generally faster than sending readings to memory using the
READ? command. The INITiate command is also an "overlapped"
command. This means that after executing the INITiate command,
you can send other commands that do not affect the
measurements.
You can store up to 50,000 readings in memory and all readings
are automatically time stamped. If memory overflows, the new
readings will overwrite the first (oldest) readings stored; the most
recent readings are always preserved. In addition, bit 9 is set in
the Questionable Data Register's condition register (see Status
System Introduction).
For scanning measurements using the multiplexer modules, an
error is generated if the internal DMM is disabled (see
INSTrument:DMM command) or not installed in the mainframe.
The internal DMM is not required for operations on the digital
modules.
If a scan list containing multiplexer channels is currently defined
(see ROUTe:SCAN command), the INITiate command performs a
scan of the specified channels. When the scan is initiated, the
instrument will open all channels in banks that contain one or more
channels in the scan list.
The instrument scans the list of channels in ascending order from
slot 100 through slot 300 (channels are re-ordered as
needed).When you specify a range of channels in the <scan_list>,
the channels are always sorted in ascending order. Therefore,
(@109:101) will always be interpreted as 101, 102, 103, etc.
Once you initiate a scan, an error will be generated if you attempt
to change any measurement parameters (CONFigure and SENSe

commands) or the triggering configuration (TRIGger commands).
To abort a scan in progress, send the ABORt command.
To retrieve the readings from memory, use the FETCh? command.
The readings are not erased from memory when you read them.
You can send the command multiple times to retrieve the same
data in reading memory.

Example
The following program segment shows how to use the INITiate command
with the CONFigure and FETCh? commands. The ROUTe:SCAN
command puts the two channels into the scan list (and redefines the
scan list). The INITiate command places the instrument in the "wait-for-
trigger" state, scans the specified channels when the rear-panel Ext Trig
Input line is pulsed low, and then sends the readings to memory. The
FETCh? command transfers the readings from memory to the
instrument's output buffer.
CONF:VOLT:DC 10,0.003,(@103,108)
ROUT:SCAN (@103,108)
TRIG:SOUR EXT
INIT
FETC?
Typical Response: +4.27150000E-03,+1.32130000E-03

See Also
FETCh?
READ?
ROUTe:SCAN

INPut:IMPedance:AUTO
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
INPut:IMPedance:AUTO <state>[,(@<ch_list>)]
INPut:IMPedance:AUTO? [(@<ch_list>)]

Description
This command enables or disables the automatic input resistance mode
for DC voltage measurements on the specified channels.

Parameters
Name Type Range of Values Default
Value
<state> Boolean {OFF|0|ON|1} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
With AUTO OFF (default), the input resistance is fixed at 10 MΩ
for all ranges.
With AUTO ON, the input resistance is set to >10 GΩ for the 100
mV, 1 V, and 10 V ranges.

Return Format
The query returns the input resistance setting as 0 (OFF) or 1 (ON) on
the specified channels.

Examples
The following command sets the impedance to >10 GΩ for two channels.
INP:IMP:AUTO ON (@105,109)
The following queries for the impedance on two channels.
INP:IMP:AUTO? (@105,109)
Typical Response: 1,1

See Also
CONFigure:VOLTage:DC
MEASure:VOLTage:DC?

R?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
R? [<max_count>]

Description
This query reads and erases readings from volatile memory up to the
specified <max_count>. The readings are erased from memory starting
with the oldest reading first. The purpose of this command is to allow you
to periodically remove readings from memory that would normally cause
reading memory to overflow (for example, during a scan with an infinite
scan count).

Parameters
| Name        | Type    | Range	of   | Default      |
| ----------- | ------- | ---------- | ------------ |
|             |         | Values     | Value        |
| <max_count> | Numeric | Maximum    | Erase	all    |
|             |         | number	of  | stored       |
|             |         | readings   | readings,	up |
|             |         | to	be	read | to	50,000    |
and	erased
from
memory,
from	1	to
50,000.

Remarks
This command is a special version of the DATA:REMove?
command with faster execution time. You can read memory at any
time using the R? command, even during a scan.
Readings can be acquired during a scan using the multiplexer and
digital modules. For scanning measurements using the multiplexer
modules, an error is generated if the internal DMM is disabled (see
INSTrument:DMM command) or not installed in the mainframe.
The internal DMM is not required for operations on the digital
modules.
You can store up to 50,000 readings in memory and all readings
are automatically time stamped. If memory overflows, the new
readings will overwrite the first (oldest) readings stored; the most
recent readings are always preserved. In addition, bit 9 is set in
the Questionable Data Register's condition register (see Status
System Introduction).
Each reading is returned with some combination of measurement
units, time stamp, channel number, and alarm status information,
depending on the settings set by the FORMat:READing
commands. The time stamp is either in relative format (time in
seconds since the beginning of the scan) or absolute format (time
of day with date, based on the instrument's clock as set by the
SYSTem:DATE and SYSTem:TIME commands). The choice of
absolute and relative time is determined by the
FORMat:READing:TIME:TYPE command.
The instrument clears all readings from memory when a new scan
is initiated, when any measurement parameters are changed
(CONFigure and SENSe commands), and when the triggering
configuration is changed (TRIGger commands).
The instrument clears all readings from memory after a Factory

Reset (*RST command) or after an Instrument Preset
(SYSTem:PRESet command).

Return Format
The query returns a series of readings in Definite-Length Block format.
The syntax is a pound sign (#) followed by a non-zero digit representing
the number of digits in the decimal integer to follow. This digit is followed
by a decimal integer indicating the number of 8-bit data bytes to follow.
This is followed by a block of data containing the specified number of
bytes.
For example:

Example
This query reads the two oldest readings and erases them from memory.
R? 2
Typical Response: #231+2.87536000E-04,+3.18131400E-03

See Also
DATA:REMove?

READ?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
34970A Syntax: READ?
34972A Syntax: READ? [(@<scan_list>)]

Description
This command changes the instrument's triggering system from the "idle"
state to the "wait-for-trigger" state. Scanning will begin when the
specified trigger conditions are satisfied following the receipt of the
READ? command. Readings are then sent immediately to reading
memory and the instrument's output buffer. On the 34970A, you must
then receive the readings into your computer or the instrument will stop
scanning when the output buffer becomes full. Readings are not stored
in the instrument’s internal memory when using READ?. On the 34972A,
the readings are always sent to memory and they will still be available
after READ? finishes.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <scan_list> | Scan |     | This	is	a |
| ----------- | ---- | --- | --------- |
One	or	more	channels,
|     | List      |     | required   |
| --- | --------- | --- | ---------- |
|     | as	shown: |     | parameter. |
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
Sending the READ? command is similar to sending the INITiate
command followed immediately by the FETCh? command.
You can store up to 50,000 readings in memory and all readings
are automatically time stamped. If memory overflows, the new
readings will overwrite the first (oldest) readings stored; the most
recent readings are always preserved. In addition, bit 9 is set in
the Questionable Data Register's condition register (see Status
System Introduction).
For scanning measurements using the multiplexer modules, an
error is generated if the internal DMM is disabled (see
INSTrument:DMM command) or not installed in the mainframe.
The internal DMM is not required for operations on the digital
modules.
The instrument scans the list of channels in ascending order from
slot 100 through slot 300 (channels are re-ordered as
needed).When you specify a range of channels in the <scan_list>,
the channels are always sorted in ascending order. Therefore,
(@109:101) will always be interpreted as 101, 102, 103, etc.
Once you initiate a scan, an error will be generated if you attempt
to change any measurement parameters (CONFigure and SENSe
commands) or the triggering configuration (TRIGger commands).
To abort a scan in progress, send the ABORt command.
Each reading is returned with some combination of measurement
units, time stamp, channel number, and alarm status information,
depending on the settings set by the FORMat:READing
commands. The time stamp is either in relative format (time in
seconds since the beginning of the scan) or absolute format (time
of day with date, based on the instrument's clock as set by the
SYSTem:DATE and SYSTem:TIME commands). The choice of

absolute and relative time is determined by the
FORMat:READing:TIME:TYPE command.
The READ? query is not valid with the *TRG command (used with
TRIGger:SOURce BUS command for software triggering).
The instrument clears all readings from memory after a Factory
Reset (*RST command) or after an Instrument Preset
(SYSTem:PRESet command).
If you specify a <scan_list> with this query (34972A only), it will
overwrite the current scan list.

Return Format
The command sends readings directly to reading memory and the
instrument's output buffer (with formatting as set by the
FORMat:READing commands). Multiple responses are separated by
commas.

Examples
The following program segment shows how to use the READ? command
with the CONFigure command. The ROUTe:SCAN command puts the
two channels into the scan list (and redefines the scan list). The READ?
command places the instrument in the "wait-for-trigger" state, scans the
specified channels when the rear-panel Ext Trig Input line is pulsed low,
sends the readings to reading memory and the instrument's output
buffer.
CONF:VOLT:DC 10,0.003,(@103,108) !Configure
channels
ROUT:SCAN (@103,108) !Define the scan list
TRIG:SOUR EXT
READ? !Applies to the present scan list
Typical Response: +4.27150000E-03,+1.32130000E-03

See Also
FETCh?
INITiate
ROUTe:SCAN

UNIT:TEMPerature
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
UNIT:TEMPerature <units>[,(@<ch_list>) ]
UNIT:TEMPerature? [(@<ch_list>)]

Description
This	command	selects	the	temperature	units	(°C,	°F,	or	Kelvin)	on	the
specified	channels.	If	you	omit	the	optional	<ch_list>	parameter,	this
command	applies	to	the	currently	defined	scan	list.
The	following	table	shows	which	temperature	transducers	are	supported
by	each	of	the	multiplexer	modules.
| Module | Thermocouple | RTD RTD | Thermistor |
| ------ | ------------ | ------- | ---------- |
|        |              | 2- 4-   |            |
Wire Wire
|     | Yes | Yes Yes | Yes |
| --- | --- | ------- | --- |
34901A
Armature
Multiplexer
| 34902A | Yes | Yes Yes | Yes |
| ------ | --- | ------- | --- |
Reed
Multiplexer
| 34908A   | Not          | Yes No | Yes |
| -------- | ------------ | ------ | --- |
| Armature | Recommended1 |        |     |
Multiplexer
(1-Wire)
1
With	a	one-wire	multiplexer,	even	very	small	ground	currents	can
introduce	substantial	measurement	error.

Parameters
Name Type Range of Values Default
Value
<units> Discrete {C|F|K}, for Celsius, This is a
Fahrenheit or Kelvin required
parameter.
The
factory
default is
C.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
You can mix temperature units on different channels within the
instrument and on the same module.
If the corresponding channels are not configured for temperature
measurements prior to the sending of the UNIT:TEMPerature
command, the instrument will dispatch an error message.
Setting the Mx+B (see CALCulate:SCALe:UNIT command)
measurement label to °C, °F, or K has no effect on the
temperature measurement units currently selected.
The CONFigure and MEASure? commands automatically select
°C.
The instrument sets the temperature units to °C after a Factory
Reset (*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns C, F, or K for each channel specified. Multiple
responses are separated by commas.

Examples
The following command sets the temperature units to °F on channels 12
and 13 in slot 300.
CONF:TEMP TC,B, (@312,313)
UNIT:TEMP F,(@312,313)
The following query returns the temperature units selected on channels
12 and 13 in slot 300.
UNIT:TEMP? (@312,313)
Typical Response: F,F

See Also
CALCulate:SCALe:UNIT
CONFigure:TEMPerature
MEASure:TEMPerature?

CALCulate Subsystem Introduction
The internal DMM is required to store readings in memory and perform
calculations. Readings can be acquired during a scan using the
34970A/34972A multiplexer modules listed below.
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module
34908A 40 Channel Single-Ended Multiplexer Module

Command Summary
CALCulate:AVERage:AVERage?
CALCulate:AVERage:CLEar
CALCulate:AVERage:COUNt?
CALCulate:AVERage:MAXimum?
CALCulate:AVERage:MAXimum:TIME?
CALCulate:AVERage:MINimum?
CALCulate:AVERage:MINimum:TIME?
CALCulate:AVERage:PTPeak?
CALCulate:COMPare:DATA
CALCulate:COMPare:DATA?
CALCulate:COMPare:MASK
CALCulate:COMPare:MASK?
CALCulate:COMPare:STATe
CALCulate:COMPare:STATe?
CALCulate:COMPare:TYPE
CALCulate:COMPare:TYPE?
CALCulate:LIMit:LOWer
CALCulate:LIMit:LOWer?
CALCulate:LIMit:LOWer:STATe
CALCulate:LIMit:LOWer:STATe?
CALCulate:LIMit:UPPer

CALCulate:LIMit:UPPer?
CALCulate:LIMit:UPPer:STATe
CALCulate:LIMit:UPPer:STATe?
CALCulate:SCALe:GAIN
CALCulate:SCALe:GAIN?
CALCulate:SCALe:OFFSet
CALCulate:SCALe:OFFSet?
CALCulate:SCALe:OFFSet:NULL
CALCulate:SCALe:STATe
CALCulate:SCALe:STATe?
CALCulate:SCALe:UNIT
CALCulate:SCALe:UNIT?

CALCulate:AVERage:MINimum?
CALCulate:AVERage:AVERage?
CALCulate:AVERage:MAXimum?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CALCulate:AVERage:MINimum? [(@<ch_list>)]
CALCulate:AVERage:AVERage? [(@<ch_list>)]
CALCulate:AVERage:MAXimum? [(@<ch_list>)]

Description
These queries return the minimum, average (arithmetic mean) and
maximum values found on each of the specified channels during the
scan. Each channel should be a multiplexer, digital or totalizer channel
that has been configured to be part of the scan list. If it is not part of the
scan list, no error will be generated, but the value returned will be a
meaningless value of 0.

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
You can read the values at any time, even during a scan. An error
is generated if the internal DMM is disabled (see
INSTrument:DMM command) or not installed in the mainframe.
The calculation starts when the internal DMM is triggered. The
instrument clears the stored statistical data on all channels when a
new scan is started, when the CALCulate:AVERage:CLEar
command is executed, after a Factory Reset (*RST command), or
after an Instrument Preset (SYSTem:PRESet command).

Return Format
The query returns a number in the form "+2.61920000E+01". Multiple
responses are separated by commas. If no data is available for the
specified channels, it returns +0.00000000E+00.

Example
The following query returns the minimum values found on channels 05
through 08 on the module in slot 100.
In this example, you can replace the MIN node with MAX or AVER.
CALC:AVER:MIN? (@105:108)
Typical Response:
+3.13830293E+01,+1.98732123E+01,9.38293055E+00,1.20393822E+01

See Also
CALCulate Subsystem Introduction

CALCulate:AVERage:CLEar
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CALCulate:AVERage:CLEar [(@<ch_list>)]

Description
This command clears all values from the statistics registers for the
specified channels. Each channel should be a multiplexer, digital or
totalizer channel that has been configured to be part of the scan list. If it
is not part of the scan list, no error will be generated, but the value
returned will be a meaningless value of 0. The minimum, maximum,
average, count, and peak-to-peak values are cleared. The values for all
scanned channels are also cleared at the start of a new scan.

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Although this command clears the minimum, maximum, average,
count, and peak-to-peak values, no readings are cleared from
memory.
The instrument generates an error if the internal DMM is disabled
(see INSTrument:DMM) or not installed in the mainframe.
The instrument clears the stored statistical data on all channels
when a new scan is started, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).

Example
The following command clears the stored statistical data on channels 1
through 10 in slot 200.
CALC:AVER:CLEar (@201:210)

See Also
CALCulate Subsystem Introduction
CALCulate:AVERage:MINimum?
CALCulate:AVERage:MAXimum?
CALCulate:AVERage:AVERage?
CALCulate:AVERage:COUNt?
CALCulate:AVERage:PTPeak?

CALCulate:AVERage:COUNt?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CALCulate:AVERage:COUNt? [(@<ch_list>)]

Description
This query returns the number of readings taken on each of the specified
channels during the scan. Each channel should be a multiplexer, digital
or totalizer channel that has been configured to be part of the scan list. If
it is not part of the scan list, no error will be generated, but the value
returned will be a meaningless value of 0.

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
You can read the values at any time, even during a scan. An error
is generated if the internal DMM is disabled (see
INSTrument:DMM command) or not installed in the mainframe.
The calculation starts when the internal DMM is triggered. The
instrument clears the stored statistical data on all channels when a
new scan is started, when the CALCulate:AVERage:CLEar
command is executed, after a Factory Reset (*RST command), or
after an Instrument Preset (SYSTem:PRESet command).

Return Format
The query returns a number in the form "+7.90000000E+01". Multiple
responses are separated by commas. If no data is available for the
specified channels, it returns 0.

Example
The following query returns the number of readings taken on channels
05 through 08 on the module in slot 100.
CALC:AVER:COUNt? (@105:108)
Typical Response:
+2.00000000E+01,1.90000000E+01,2.10000000E+01,2.00000000E+01

See Also
CALCulate Subsystem Introduction
CALCulate:AVERage:MINimum?
CALCulate:AVERage:MAXimum?
CALCulate:AVERage:AVERage?

CALCulate:AVERage:MINimum:TIME?
CALCulate:AVERage:MAXimum:TIME?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CALCulate:AVERage:MINimum:TIME? [(@<ch_list>)]
CALCulate:AVERage:MAXimum:TIME? [(@<ch_list>)]

Description
These queries return the time that the minimum or maximum reading
was taken on the specified channels during the scan (in full time and
date format). Each channel must be a multiplexer, digital input or totalizer
channel that has been configured to be part of the scan list.

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
You can read the values at any time, even during a scan. An error
is generated if the internal DMM is disabled (see
INSTrument:DMM command) or not installed in the mainframe.
The calculation starts when the internal DMM is triggered. The
instrument clears the stored statistical data on all channels when a
new scan is started, when the CALCulate:AVERage:CLEar
command is executed, after a Factory Reset (*RST command), or
after an Instrument Preset (SYSTem:PRESet command).
This command is not affected by the
FORMat:READing:TIME:TYPE command, which selects the time
format for storing scanned data in memory (absolute time versus
relative time).

Return Format
For each channel, the query returns the time in the form
yyyy,mm,dd,hh,mm,ss.sss. For example, 2009,10,03,14,35,06.215 would
mean October 3, 2009 at 2:35:06.215 PM.

Example
The following query returns the time of the minimum reading on channels
03 and 04 on the module in slot 100.
CALC:AVER:MIN:TIME? (@103:104)
Typical Response: 2009,12,20,08,39,27.283,2009,12,20,08,39,28.011

See Also
CALCulate Subsystem Introduction

CALCulate:AVERage:PTPeak?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CALCulate:AVERage:PTPeak? [(@<ch_list>)]

Description
This query returns the peak to peak value (maximum minus minimum)
found on each of the specified channels during the scan. Each channel
should be a multiplexer, digital or totalizer channel that has been
configured to be part of the scan list. If it is not part of the scan list, no
error will be generated, but the value returned will be a meaningless
value of 0.

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
list One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
You can read the values at any time, even during a scan. An error
is generated if the internal DMM is disabled (see
INSTrument:DMM command) or not installed in the mainframe.
The calculation starts when the internal DMM is triggered. The
instrument clears the stored statistical data on all channels when a
new scan is started, when the CALCulate:AVERage:CLEar
command is executed, after a Factory Reset (*RST command), or
after an Instrument Preset (SYSTem:PRESet command).

Return Format
The query returns a number in the form "+2.61920000E+01". Multiple
responses are separated by commas. If no data is available for the
specified channels, it returns +0.00000000E+00.

Example
The following query returns the peak to peak values found on channels
05 through 08 on the module in slot 100.
CALC:AVER:PTP? (@105:108)
Typical Response:
+3.13830293E+01,+1.98732123E+01,9.38293055E+00,1.20393822E+01

See Also
CALCulate Subsystem Introduction
CALCulate:AVERage:MINimum?
CALCulate:AVERage:MAXimum?
CALCulate:AVERage:AVERage?

CALCulate:COMPare:DATA
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALCulate:COMPare:DATA <data>[,(@<ch_list>)]
CALCulate:COMPare:DATA? [(@<ch_list>)]

Description
This command sets the digital data for pattern comparisons on the
specified digital input channels. You can use the pattern comparison
feature to generate an alarm when a specific digital pattern is detected.
Used With:
34907A Multifunction Module (digital input channels only)

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <data> | Numeric | An	8-bit	digital	pattern | This	is	a  |
| ------ | ------- | ------------------------ | ---------- |
|        |         | for	comparison,          | required   |
|        |         | specified	as	an	integer  | parameter. |
from	0	to	255.
| <ch_list> | Channel |     | If	you |
| --------- | ------- | --- | ------ |
One	or	more
|     | List |                     | omit	the |
| --- | ---- | ------------------- | -------- |
|     |      | channels,	as	shown: | optional |
<ch_list>
(@301)	-	channel	01
parameter,
on	the	module	in	slot
this
300.
command
applies	to
(@301:302)	-
the
channels	01	and	02
currently
on	the	module	in	slot
defined
300.
scan	list.
(@101,201:202,302)
-	channel	01	on	the
module	in	slot	100,
channels	01	and	02
on	the	module	in	slot
200,	and	channel	02
on	the	module	in	slot
300.

Remarks
Note that the specified channels do not have to be part of the scan
list to generate an alarm. Alarms are evaluated continuously as
soon as you enable them. Alarms are evaluated constantly on the
multifunction module, but alarm data is stored in reading memory
only during a scan.
The channel width takes precedence over the specified digital
pattern. If the specified pattern is greater than the channel width,
additional bits will be ignored. For example, if you set the channel
width to "BYTE" and then specify a pattern of "256" (1 0000 0000),
the pattern will be truncated to "0000 0000" (the leading "1" will be
ignored).
After specifying the desired digital pattern, use the
CALCulate:COMPare:STATe command to enable pattern
comparisons on the specified channels. If you want to monitor the
state of specific bits, use the CALCulate:COMPare:DATA
command in conjunction with the CALCulate:COMPare:MASK
command to specify a mask pattern.
Use the CALCulate:COMPare:TYPE command to specify whether
an alarm or hardware interrupt condition is generated when a
specific bit pattern or bit pattern change is detected.
A Factory Reset (*RST command) clears the digital pattern and
turns off the pattern comparison mode. An Instrument Preset
(SYSTem:PRESet command) or Card Reset (SYSTem:CPON
command) does not clear the data and does not turn off the
pattern comparison mode.

Return Format
The query returns the comparison pattern as a decimal value (binary and
hexadecimal values are converted to their decimal equivalents). Multiple
responses are separated by commas.

Examples
The following query returns the comparison pattern selected for channel
01 of the 34907A multifunction module in slot 300.
CALC:COMP:DATA? (@301) !Always returns decimal
equivalent
Typical Response: 140
The following program segment sets the digital pattern for the 34907A
multifunction module in slot 100 and then enables the pattern
comparison mode. When the data read from the bank is equal to the
comparison pattern, an alarm will be generated on Alarm 2.
CALC:COMP:DATA #HF6,(@101) !Set comparison pattern
(1111 0110)
CALC:COMP:TYPE EQUAL,(@101) !Generate alarm on
pattern match
OUTP:ALARM2:SOUR (@101) !Enable alarms
CALC:COMP:STAT ON,(@101) !Enable pattern comparison
mode
The following query returns the comparison pattern selected for the
34907A multifunction module in slot 100.
CALC:COMP:DATA? (@101) !Always returns decimal
equivalent
Typical Response: +246

See Also
CALCulate Subsystem Introduction
CALCulate:COMPare:MASK
CALCulate:COMPare:STATe
CALCulate:COMPare:TYPE
OUTPut:ALARm{1|2|3|4}:SOURce

CALCulate:COMPare:MASK
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALCulate:COMPare:MASK <mask>[,(@<ch_list>)]
CALCulate:COMPare:MASK? [(@<ch_list>)]

Description
This command is used in conjunction with the
CALCulate:COMPare:DATA command to set the digital mask data for
pattern comparisons on the specified digital input channels. You can use
the pattern comparison feature to generate an alarm when a specific
digital pattern is detected.
Used With:
34907A Multifunction Module (digital input channels only)

Parameters
Name Type Range of Values Default
Value
<mask> Numeric An 8-bit mask pattern This is a
for comparison, required
specified as an integer parameter.
from 0 to 255. Active
bits are specified as
1's, and "don't care"
bits are specified as
0's.
<ch_list> Channel If you
List One or more omit the
channels, as shown: optional
<ch_list>
(@301) - channel 01
parameter,
on the module in slot
this
300.
command
applies to
(@301:302) -
the
channels 1 and 2 on
currently
the module in slot
defined
300.
scan list.
(@101,201:202,302)
- channel 1 on the
module in slot 100,
channels 01 and 02
on the module in slot
200, and channel 02
on the module in slot
300.

Remarks
Note that the specified channels do not have to be part of the scan
list to generate an alarm. Alarms are evaluated continuously as
soon as you enable them. Alarms are evaluated constantly on the
multifunction module, but alarm data is stored in reading memory
only during a scan.
The channel width takes precedence over the specified digital
pattern. If the specified pattern is greater than the channel width,
additional bits will be ignored. For example, if you set the channel
width to "BYTE" and then specify a pattern of "256" (1 0000 0000),
the pattern will be truncated to "0000 0000" (the leading "1" will be
ignored).
After specifying the desired digital pattern, use the
CALCulate:COMPare:STATe command to enable pattern
comparisons on the specified channels.
A Factory Reset (*RST command) clears the mask and turns off
the pattern comparison mode. An Instrument Preset
(SYSTem:PRESet command) or Card Reset (SYSTem:CPON
command) does not clear the mask and does not turn off the
pattern comparison mode.

Return Format
The query returns the mask as a decimal value (binary and hexadecimal
values are converted to their decimal equivalents). Multiple responses
are separated by commas.

Examples
To illustrate how the calculations are performed, see the example below
which assumes that a decimal 146 was read from the channel. Since the
calculations produce a non-zero result (decimal 16), an interrupt is not
generated.
MSB LSB
1001 0010 Data read from port (decimal 146)
1000 1100 CALC:COMP:DATA command (decimal 140)
0001 1110 X-OR result
1111 0000 CALC:COMP:MASK command (decimal 240)
0001 0000 AND result (decimal 16, no interrupt generated)
The following query returns the comparison pattern selected for the
module in slot 300.
CALC:COMP:MASK? (@301) !Always returns decimal
equivalent
Typical Response: 240
The following program segment sets the digital pattern for the 34907A
multifunction module in slot 100, applies a mask to the lower byte, and
then enables the pattern comparison mode. When the data read from the
lower byte is equal to the comparison pattern, an alarm will be generated
on Alarm 2.
CALC:COMP:DATA:WORD #HF6F6,(@101) !Set comparison
pattern (1111 0110 1111 0110)
CALC:COMP:MASK #H00FF,(@101) !Set mask pattern (0000
0000 1111 1111)
CALC:COMP:TYPE EQUAL,(@101) !Generate alarm on
pattern match

OUTP:ALARM2:SOUR (@101) !Enable alarms
CALC:COMP:STAT ON,(@101) !Enable pattern comparison
mode
To illustrate how the calculations are performed, see the example below
which assumes that a decimal 37595 was read from the channel. Since
the calculations produce a non-zero result (decimal 13), an alarm is not
generated.
MSB LSB
1001 0010 1101 1011 Data read from port (decimal 37595)
1111 0110 1111 0110 CALC:COMP:DATA command (decimal 63222)
0110 0100 0010 1101 X-OR result
0000 0000 1111 1111 CALC:COMP:MASK command (decimal 255)
0000 0000 0000 1101 AND result (decimal 13, no alarm generated)
The following query returns the comparison pattern selected for channel
01 of the 34907A multifunction module in slot 100.
CALC:COMP:MASK? (@101) !Always returns decimal
equivalent
Typical Response: + 255

See Also
CALCulate Subsystem Introduction
CALCulate:COMPare:DATA
CALCulate:COMPare:STATe
CALCulate:COMPare:TYPE
OUTPut:ALARm{1|2|3|4}:SOURce

CALCulate:COMPare:STATe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALCulate:COMPare:STATe <state>[,(@<ch_list>)]
CALCulate:COMPare:STATe? [(@<ch_list>)]

Description
This command disables or enables the pattern comparison mode on the
specified digital input channels. You can use the pattern comparison
feature to generate an alarm when a specific digital pattern is detected.
Used With:
34907A Multifunction Module (digital input channels only)

Parameters
Name Type Range of Values Default
Value
<state> Boolean {OFF|0|ON|1} This is a
required
parameter.
<ch_list> Channel If you
List One or more omit the
channels, as shown: optional
<ch_list>
(@301) - channel 01
parameter,
on the module in slot
this
300.
command
applies to
(@301:302) -
the
channels 01 and 02
currently
on the module in slot
defined
300.
scan list.
(@101,201:202,302)
- channel 01 on the
module in slot 100,
channels 01 and 02
on the module in slot
200, and channel 02
on the module in slot
300.

Remarks
Note that the specified channels do not have to be part of the scan
list to generate an alarm. Alarms are evaluated continuously as
soon as you enable them. Alarms are evaluated constantly on the
multifunction module, but alarm data is stored in reading memory
only during a scan.
A Factory Reset (*RST command) turns off the pattern comparison
mode. An Instrument Preset (SYSTem:PRESet command) or Card
Reset (SYSTem:CPON command) does not turn off the pattern
comparison mode.

Return Format
The query returns the state of the comparison mode as 0 (OFF) or 1
(ON) for the specified bank. Multiple responses are separated by
commas.

Examples
The following command sets the comparison mode ON for the three
specified channels.
CALC:COMP:STAT 1,(@201,202,301)
The following query returns the state of the pattern comparison mode for
channel 01 on the modules in slot 200 and 300.
CALC:COMP:STAT? (@201,301)
Typical Response: 1,1

See Also
CALCulate Subsystem Introduction
CALCulate:COMPare:DATA
CALCulate:COMPare:MASK
CALCulate:COMPare:TYPE
OUTPut:ALARm{1|2|3|4}:SOURce

CALCulate:COMPare:TYPE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALCulate:COMPare:TYPE <mode>[,(@<ch_list>)]
CALCulate:COMPare:TYPE? [(@<ch_list>)]

Description
This command configures the specified digital input channels to generate
an alarm when a specific bit pattern or bit pattern change is detected.
This command is used in conjunction with the
CALCulate:COMPare:DATA command which sets the data bit pattern
and the CALCulate:COMPare:MASK command which sets the mask bit
pattern.
Used With:
34907A Multifunction Module (digital input channels only)

Parameters
Name Type Range of Values Default
Value
<mode> Discrete {EQUal|NEQual} This is a
required
parameter.
The
power-on
value is
NEQual.
<ch_list> Channel If you
List One or more omit the
channels, as shown: optional
<ch_list>
(@301) - channel 01
parameter,
on the module in slot
this
300.
command
applies to
(@301:302) -
the
channels 01 and 02
currently
on the module in slot
defined
300.
scan list.
(@101,201:202,302)
- channel 01 on the
module in slot 100,
channels 01 and 02
on the module in slot
200, and channel 02
on the module in slot
300.

Remarks
Note that the specified channels do not have to be part of the scan
list to generate an alarm. Alarms are evaluated continuously as
soon as you enable them. Alarms are evaluated constantly on the
multifunction module, but alarm data is stored in reading memory
only during a scan.
Select EQUal to generate an alarm or interrupt when the data read
from the specified channel is equal to CALCulate:COMPare:DATA,
after being masked by CALCulate:COMPare:MASK.
Select NEQual (not equal) to generate an alarm or interrupt when
the data read from the bank is not equal to
CALCulate:COMPare:DATA after being masked by
CALCulate:COMPare:MASK.
Bits masked off as 0 ("don't care") by CALCulate:COMPare:MASK
are ignored.
The channel width takes precedence over the specified digital
pattern. If the specified pattern is greater than the channel width,
additional bits will be ignored. For example, if you set the channel
width to "BYTE" and then specify a pattern of "256" (1 0000 0000),
the pattern will be truncated to "0000 0000" (the leading "1" will be
ignored).
A Factory Reset (*RST command) clears the pattern compare
setting and turns off the pattern comparison mode. An Instrument
Preset (SYSTem:PRESet command) or Card Reset
(SYSTem:CPON command) does not clear the pattern compare
setting and does not turn off the pattern comparison mode.

Return Format
The query returns EQU or NEQ for the specified bank. Multiple
responses are separated by commas.

Examples
The following command sets the comparison mode for the specified
channels to EQUal.
CALC:COMP:TYPE EQU,(@301:302)
The following query returns the comparison mode for the two specified
channels.
CALC:COMP:TYPE? (@301:302)
Typical Response: EQU,EQU

See Also
CALCulate:COMPare:DATA
CALCulate:COMPare:MASK
CALCulate:COMPare:STATe
OUTPut:ALARm{1|2|3|4}:SOURce

CALCulate:LIMit:LOWer
CALCulate:LIMit:UPPer
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALCulate:LIMit:LOWer <lo_limit>[,(@<ch_list>)]
CALCulate:LIMit:LOWer? [(@<ch_list>)]
CALCulate:LIMit:UPPer <hi_limit>[,(@<ch_list>)]
CALCulate:LIMit:UPPer? [(@<ch_list>)]

Description
The instrument has four alarms which you can configure to alert you
when a reading exceeds specified limits on a multiplexer channel during
a scan. These commands set the lower and upper limits for alarms on
the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (totalizer channel only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<lo_limit> Numeric Any numeric value 0
<hi_limit> Numeric Any numeric value; for 0
totalizer channels, the
<hi_limit> refers to a
maximum count.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Alarms are evaluated during a scan or a monitor measurement on
channels of a multiplexer module. For scanning using a
multiplexer module, an error is generated if the internal DMM is
disabled (see INSTrument:DMM command) or not installed in the
mainframe. The internal DMM is not required for operations on the
digital modules and the specified channels do not have to be part
of the active scan list to generate an alarm.
You can assign a lower limit, an upper limit, or both to any
configured channel in the scan list. The lower limit must always be
less than or equal to the upper limit.
Once you have defined the lower limits, use the
CALCulate:LIMit:LOWer:STATe command to enable alarms on the
specified channels. Similarly, use CALCulate:LIMit:UPPer:STATe
after setting the upper limits.
The alarms are evaluated by the internal DMM from the time the
CALCulate:LIMit:LOWer:STATe ON and
CALCulate:LIMit:UPPer:STATe ON commands are executed.
You must configure the channel (function, transducer type, etc.)
before setting any alarm limits. If you change the measurement
configuration, alarms are turned off and the limit values are
cleared. Alarms are also turned off when you change the
temperature probe type, temperature units, or disable the internal
DMM.
You can assign multiple channels to any of the four available
alarms (numbered 1 through 4, see OUTPut:ALARm<n>:SOURce
command). For example, you can configure the instrument to
generate an alarm on the Alarm 1 output when a limit is exceeded
on any of channels 103, 205, or 310. You cannot, however, assign
alarms on a specific channel to more than one alarm number.

If you plan to use alarms on a channel which will also use Mx+B
scaling, be sure to configure the scaling values first. If you attempt
to assign the alarm limits first, the instrument will turn off alarms
and clear the limit values when you enable scaling on that
channel. If you specify a custom measurement label with scaling, it
is automatically used when alarms are logged on that channel.
If you redefine the scan list, alarms are no longer evaluated on
those channels (during a scan) but the limit values are not cleared.
If you decide to add a channel back to the scan list (without
changing the function), the original limit values are restored and
alarms are turned back on. This makes it easy to temporarily
remove a channel from the scan list without entering the alarm
values again.
To generate an alarm when a specific count is reached on a
totalizer channel, see the CALCulate:LIMit:UPPer command. To
generate an alarm when a specific bit pattern or bit pattern change
is detected on a digital input channel, see the
CALCulate:COMPare commands.
The instrument clears all alarm limits and turns off all alarms after
a Factory Reset (*RST command), Instrument Preset
(SYSTem:PRESet command), or Card Reset (SYSTem:CPON
command).

Return Format
The query returns the upper or lower limit in the form "-1.00000000E+15"
for each channel specified. Multiple responses are separated by
commas.

Examples
In the following examples, you can substitute the node name UPP for
LOW.
The following command sets the lower limit to -0.25 on channels 03 and
13 in slot 100.
CALC:LIM:LOW -0.25,(@103,113)
The following query returns the lower limit settings on channels 03 and
13 in slot 100.
CALC:LIM:LOW? (@103,113)
Typical Response: -2.50000000E-01,-2.50000000E-01

See Also
CALCulate Subsystem Introduction
CALCulate:LIMit:LOWer:STATe

CALCulate:LIMit:LOWer:STATe
CALCulate:LIMit:UPPer:STATe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALCulate:LIMit:LOWer:STATe <mode>,(@<ch_list>)
CALCulate:LIMit:LOWer:STATe? (@<ch_list>)
CALCulate:LIMit:UPPer:STATe <mode>,(@<ch_list>)
CALCulate:LIMit:UPPer:STATe? (@<ch_list>)

Description
These commands disable or enable the lower and upper alarm limits on
the specified multiplexer channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<mode> Boolean {OFF|0|ON|1} OFF
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Alarm data can be stored in one of two locations depending on
whether a scan list is running when the alarm occurs.
a. If an alarm event occurs on a channel as it is being scanned, then
that channel's alarm status is stored in reading memory as the
readings are taken. Each reading that is outside the specified alarm
limit is logged in memory. You can store at least 50,000 readings in
memory during a scan.
b. As alarm events are generated, they are also logged in an alarm
queue, which is separate from reading memory. This is the only
place that non-scanned alarms get logged (alarms during a
channel monitor, alarms generated by the digital modules, etc.). Up
to 20 alarms can be logged in the alarm queue. If more than 20
alarm events are generated, they will be lost (only the first 20
alarms are saved). Even if the alarm queue is full, the alarm status
is stored in reading memory during a scan.
Alarms are evaluated during a scan or a monitor measurement on
channels of a multiplexer module. For scanning using a
multiplexer module, an error is generated if the internal DMM is
disabled (see INSTrument:DMM command) or not installed in the
mainframe. The internal DMM is not required for operations on the
digital modules and the specified channels do not have to be part
of the active scan list to generate an alarm.
When an alarm occurs, the instrument stores relevant information
about the alarm in the queue. This includes the reading that
caused the alarm, the time of day and date of the alarm, and the
channel number on which the alarm occurred. The information
stored in the alarm queue is always in absolute time and is not
affected by the FORMat:READing:TIME:TYPE command setting.
Alarms are logged in the alarm queue only when a reading

crosses a limit, not while it remains outside the limit and not when
it returns to within limits.
In addition to being stored in reading memory, alarms are also
recorded in their own SCPI Status System. You can configure the
instrument to use the status register to generate a Service
Request (SRQ) when alarms are generated. For more information
on the Status System for the instrument, see Status System
Introduction.
On the digital modules, you can set an upper limit for the totalizer
channels (no lower limit is allowed). These channels do not have
to be part of the active scan list to generate an alarm, but alarm
data is stored in reading memory only as part of a scan.
To generate an alarm when a specific count is reached on a
totalizer channel, see the CALCulate:LIMit:UPPer command. To
generate an alarm when a specific bit pattern or bit pattern change
is detected on a digital input channel, see the
CALCulate:COMPare commands.
The instrument clears all alarm limits and turns off all alarms after
a Factory Reset (*RST command), Instrument Preset
(SYSTem:PRESet command), or Card Reset (SYSTem:CPON
command).

Return Format
The query returns 0 (OFF) or 1 (ON) for each channel specified. Multiple
responses are separated by commas.

Examples
In the examples below, you can replace the node name UPP with LOW.
The following program segment sets an upper limit on channels 03 and
13 in slot 100 and then enables alarms on these channels.
CALC:LIM:UPP 10.25,(@103,113)
CALC:LIM:UPP:STAT ON,(@103,113)
The following query returns the state of upper limits on channels 03 and
13 in slot 100.
CALC:LIM:UPP:STAT? (@103,113)
Typical Response: 1,1
The following command sets the upper limit to 4095 on totalizer channels
01 and 02 in slot 300 and then enables alarms on these channels.
CALC:LIM:UPP 4.095E+03,(@301,302)
CALC:LIM:UPP:STAT ON,(@301,302)

See Also
CALCulate Subsystem Introduction
CALCulate:LIMit:UPPer
OUTPut:ALARm{1|2|3|4}:SOURce
SYSTem:ALARm?

CALCulate:SCALe:GAIN
CALCulate:SCALe:OFFSet
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALCulate:SCALe:GAIN <gain>[,(@<ch_list>)]
CALCulate:SCALe:GAIN? [(@<ch_list>)]
CALCulate:SCALe:OFFSet <offset>[,(@<ch_list>)]
CALCulate:SCALe:OFFSet? [(@<ch_list>)]

Description
These commands set the gain ("M") and offset ("B") for scaled readings
on the specified multiplexer channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<gain> Numeric Any value between -1E15 This is a
to +1E15 required
parameter.
The
factory
default is
1.
<offset> Numeric Any value between -1E+15 This is a
and +1E+15. required
parameter.
The
factory
default is
0.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in

slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Scaling is applied using the following equation:
Scaled Reading = (Gain x Measurement) + Offset
After setting the gain and offset values, use the
CALCulate:SCALe:STATe command to enable the scaling
function.
Readings can be acquired during a scan using the multiplexer. For
scanning measurements using the multiplexer modules, an error is
generated if the internal DMM is disabled (see INSTrument:DMM
command) or not installed in the mainframe.
You must configure the channel (function, transducer type, etc.)
before applying any scaling values. If you change the
measurement configuration, scaling is turned off on that channel
and the gain and offset values are reset (M=1 and B=0). Scaling is
also turned off when you change the temperature probe type,
temperature units, or disable the internal DMM.
If you change the measurement configuration (function, transducer
type, etc.) on a channel or the internal DMM, scaling is turned off
on those channels and the gain and offset values are cleared.
If you plan to use scaling on a channel which will also use alarms,
be sure to configure the scaling values first. If you attempt to
assign the alarm limits first, the instrument will turn off alarms and
clear the limit values when you enable scaling on that channel. If
you specify a custom measurement label with scaling, it is
automatically used when alarms are logged on that channel.
If you redefine the scan list, no change will be made to the scaling
state or the gain and offset values. If you decide to add a channel
back to the scan list, the original gain and offset values are
restored.

You can use scaling to make a "null" measurement on a channel
and store it as the offset ("B") for subsequent measurements. This
allows you to adjust for voltage or resistive offsets through your
wiring to the point of the measurement. See
CALCulate:SCALe:OFFSet:NULL.
The CONFigure and MEASure? commands automatically set the
gain ("M") to 1 and offset ("B") to 0.
A Factory Reset (*RST command) turns off scaling and clears the
scaling values on all channels (gain = 1, offset = 0). An Instrument
Preset (SYSTem:PRESet command) does not clear the scaling
values and does not turn off scaling.

Return Format
The query returns the gain or offset value for each channel specified.
Multiple responses are separated by commas.

Examples
The following command sets the gain to +1.25 on channels 03 and 13 in
slot 100.
CALC:SCAL:GAIN 1.25,(@103,113)
The following query returns the gain settings on channels 03 and 13 in
slot 100.
CALC:SCAL:GAIN? (@103,113)
Typical Response: +1.25000000E+00,+1.25000000E+00
The following command sets the offset to +10.125 on channels 03 and
13 in slot 100.
CALC:SCAL:OFFS 10.125,(@103,113)
The following query returns the offset values on channels 03 and 13 in
slot 100.
CALC:SCAL:OFFS? (@103,113)
Typical Response: +1.01250000E+01,+1.01250000E+01

See Also
CALCulate Subsystem Introduction
CALCulate:SCALe:OFFSet:NULL
CALCulate:SCALe:STATe
CALCulate:SCALe:UNIT

CALCulate:SCALe:OFFSet:NULL
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CALCulate:SCALe:OFFSet:NULL [(@<ch_list>)]

Description
This command makes an immediate null measurement on the specified
channels and stores it as the offset ("B") for subsequent measurements.
This allows you to adjust for voltage or resistive offsets through your
wiring to the point of the measurement.

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Example
The following command makes an immediate null measurement on
channels 206 through 210.
CALC:SCAL:OFFS:NULL (@206:210)

See Also
CALCulate Subsystem Introduction
CALCulate:SCALe:GAIN
CALCulate:SCALe:OFFSet
CALCulate:SCALe:STATe
CALCulate:SCALe:UNIT

CALCulate:SCALe:STATe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALCulate:SCALe:STATe <state>[,(@<ch_list>)]
CALCulate:SCALe:STATe? [(@<ch_list>)]

Description
This command disables or enables Mx+B scaling on the specified
channels. If you omit the optional <ch_list> parameter, this command
applies to the currently defined scan list.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<state> Boolean {OFF|0|ON|1} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Scaling is applied using the following equation:
Scaled Reading = (Gain x Measurement) + Offset
Readings can be acquired during a scan using the multiplexer. For
scanning measurements using the multiplexer modules, an error is
generated if the internal DMM is disabled (see INSTrument:DMM
command) or not installed in the mainframe.
You must configure the channel (function, transducer type, etc.)
before applying any scaling values. If you change the
measurement configuration, scaling is turned off on that channel
and the gain and offset values are reset (M=1 and B=0). Scaling is
also turned off when you change the temperature probe type,
temperature units, or disable the internal DMM.
If you change the measurement configuration (function, transducer
type, etc.) on a channel, scaling is turned off on those channels
and the gain and offset values are cleared.
If you plan to use scaling on a channel which also uses alarms, be
sure to configure the scaling values first. If you attempt to assign
the alarm limits first, the instrument will turn off alarms and clear
the limit values when you enable scaling on that channel. If you
specify a custom measurement label with scaling, it is
automatically used when alarms are logged on that channel.
If you redefine the scan list, no change will be made to the scaling
state or the gain and offset values. If you decide to add a channel
back to the scan list, the original gain and offset values are
restored.
The CONFigure and MEASure? commands automatically disable
scaling on the specified channels.

A Factory Reset (*RST command) turns off scaling and clears the
scaling values on all channels (gain = 1, offset = 0). An Instrument
Preset (SYSTem:PRESet command) does not clear the scaling
values and does not turn off scaling.

Return Format
The query returns 0 (OFF) or 1 (ON) for each channel specified. Multiple
responses are separated by commas.

Examples
The following program segment sets gain and offset values on channels
03 and 13 in slot 100 and then enables scaling on these channels.
CALC:SCAL:GAIN 1.25,(@103,113)
CALC:SCAL:OFFS 10.125,(@103,113)
CALC:SCAL:STAT ON,(@103,113)
The following query returns the scaling settings on channels 03 and 13 in
slot 100.
CALC:SCAL:STAT? (@103,113)
Typical Response: 1,1

See Also
CALCulate Subsystem Introduction
CALCulate:SCALe:GAIN
CALCulate:SCALe:OFFSet
CALCulate:SCALe:OFFSet:NULL
CALCulate:SCALe:UNIT

CALCulate:SCALe:UNIT
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALCulate:SCALe:UNIT <quoted_string>[,(@<ch_list>)]
CALCulate:SCALe:UNIT? [(@<ch_list>)]

Description
This command allows you to specify the custom label of up to three
characters (for example, RPM, PSI) for scaled measurements on the
specified channels. If you omit the optional <ch_list> parameter, this
command applies to the currently defined scan list.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <quoted_string> | Quoted | A	quoted	ASCII	string	of    | This	is	a  |
| --------------- | ------ | --------------------------- | ---------- |
|                 | ASCII  | up	to	three	characters.	You | required   |
|                 | String | can	use	letters	(A-Z),      | parameter. |
numbers	(0-9),	an
underscore	(	_	),	or	the	"#"
character	which	displays	a
degree	symbol	(	°	)	on	the
front	panel	(displayed	as	a
blank	space	in	an	output
string	from	the	remote
interface).	The	first
character	must	be	a	letter	or
the	"#"	character	(the	"#"
character	is	allowed	only	as
the	leftmost	character	in	the
label).	The	remaining	two
characters	can	be	letters,
numbers,	or	an	underscore.
| <ch_list> | Channel |                       | If	you   |
| --------- | ------- | --------------------- | -------- |
|           | List    | One	or	more	channels, | omit	the |
|           |         | as	shown:             | optional |
<ch_list>
(@310)	-	channel	10	on
parameter,
|     |     | the	module	in	slot	300. | this |
| --- | --- | ----------------------- | ---- |
command
(@305:310)	-	channels
applies	to
05	through	10	on	the
the
module	in	slot	300.
currently
defined
(@202:207,209,302:308)
scan	list.
-	channels	02	through	07
and	09	on	the	module	in

slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Readings can be acquired during a scan using the multiplexer. For
scanning measurements using the multiplexer modules, an error is
generated if the internal DMM is disabled (see INSTrument:DMM
command) or not installed in the mainframe.
If you set the measurement label to °C, °F, or K, note that this has
no effect the temperature units set using the UNIT:TEMPerature
command.
The CONFigure and MEASure? commands automatically reverts
the unit to the natural units for the function.
A Factory Reset (*RST command) turns off scaling, clears the
scaling values (gain = 1, offset = 0), and automatically reverts the
unit to the natural units for the function. An Instrument Preset
(SYSTem:PRESet command) does not clear the scaling values or
measurement labels and does not turn off scaling.

Return Format
The query reads the measurement units for each channel specified and
returns an ASCII string enclosed in double quotes. Multiple responses
are separated by commas.

Examples
The following command adds the measurement label "RPM"
(Revolutions Per Minute) to channels 03 and 13 in slot 100.
CALC:SCAL:UNIT "RPM",(@103,113) or CALC:SCAL:UNIT
'RPM',(@103,113)
The following query returns the measurement labels assigned to
channels 03 and 13 in slot 100.
CALC:SCAL:UNIT? (@103,113)
Typical Response: "RPM","RPM"

See Also
CALCulate Subsystem Introduction
CALCulate:SCALe:GAIN
CALCulate:SCALe:OFFSet
CALCulate:SCALe:OFFSet:NULL
CALCulate:SCALe:STATe

CALibration Subsystem Introduction
The CALibration commands are used to calibrate the Keysight
34970A/34972A. Please note that the use of these commands requires a
detailed knowledge of the appropriate calibration procedures, which are
described in the Keysight 34970A/34972A Service Guide. Please refer to
that guide before attempting to calibrate the instrument as improper use
of the CALibration commands can adversely affect the accuracy and
reliability of the instrument.

Command Summary
CALibration?
CALibration:COUNt?
CALibration:SECure:CODE
CALibration:SECure:STATe
CALibration:SECure:STATe?
CALibration:STRing
CALibration:STRing?
CALibration:VALue
CALibration:VALue?

CALibration?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CALibration?

Description
This command performs a calibration of the internal DMM or DAC
channel on the 34907A multifunction module using the specified
calibration value (CALibration:VALue command). Before you can
calibrate the instrument, you must unsecure it by entering the correct
security code.
For a more detailed discussion of the
calibration procedures, see the
Keysight 34970A/34972A Service
Guide. Please refer to that guide
before attempting to calibrate the
instrument as improper use of the
CALibration commands can
adversely affect the accuracy and
reliability of the instrument.

Remarks
If a calibration fails, the instrument returns 1 and generates an
error message. For a complete listing of the error messages
related to calibration failures, see SCPI Error Messages.
The internal DMM is an optional assembly for the Keysight
34970A/34972A. The instrument generates an error with this
command if the internal DMM is disabled (see INSTrument:DMM
command) or not installed in the mainframe.
This command increments the calibration count by one count for
the DMM and DAC channels (see CALibration:COUNt?
command).

Return Format
The query returns 0 (calibration passed) or 1 (calibration failed).

Example
The following command performs a calibration and returns a pass/fail
indication.
CAL?
Typical Response: 0

See Also
CALibration:SECure:STATe
CALibration:VALue

CALibration:COUNt?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CALibration:COUNt?

Description
This command queries the instrument to determine the number of times
it has been calibrated. Note that your instrument was calibrated before it
left the factory. When you receive your instrument, be sure to read the
various counts to determine its initial value.
For a more detailed discussion of the calibration
procedures, see the Keysight 34970A/34972A Service
Guide. Please refer to that guide before attempting to
calibrate the instrument as improper use of the
CALibration commands can adversely affect the
accuracy and reliability of the instrument.
Used With:
Internal DMM

Remarks
The calibration count increments up to a maximum of 65,535, after
which it rolls over to 0. Because the value increments by one for
each calibration point, a complete calibration may increase the
value by many counts.
The mainframe calibration count is incremented by the
CALibration? command (the mainframe must be unsecured; see
CALibration:SECure:STATe OFF command). You can read the
calibration count regardless of whether the instrument is secured.
The calibration count is also incremented by calibrations of the
DAC channels on the 34907A multifunction module.
The calibration count is stored in non-volatile memory, and does
not change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).

Return Format
The query returns the calibration count indicating how many calibrations
have been performed.

Example
The following query returns the calibration count.
CAL:COUN?
Typical Response: +273

See Also
CALibration Subsystem Introduction
CALibration?
CALibration:SECure:STATe

CALibration:SECure:CODE
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CALibration:SECure:CODE <new_code>

Description
This command allows you to enter a new security code to prevent
accidental or unauthorized calibrations. The specified code is used to
unsecure the mainframe and all installed modules. To change the
security code, you must first unsecure the instrument using the old
security code, and then enter a new code.
For a more detailed discussion of the
calibration procedures, see the
Keysight 34970A/34972A Service
Guide. Please refer to that guide
before attempting to calibrate the
instrument as improper use of the
CALibration commands can
adversely affect the accuracy and
reliability of the instrument.
Used With:
Internal DMM

Parameters
Name Type Range of Default Value
Values
<new_code> ASCII A string of This is a
String up to 12 required
characters. parameter.
You do not
have to use
all 12
characters
but the first
character
must
always be a
letter (A-
Z). The
remaining
11
characters
can be
letters,
numbers
(0-9), or
the
underscore
character
("_").
Blank
spaces are
not
allowed.

Remarks
The security code is set to "HP034970" or
"AT034972", depending on the product
number, when the instrument is shipped from
the factory. Note that the third character of the
security code is a zero (0) and not a capital O.
If you forget your security code, you can
override the security feature. See the Keysight
34970A/34972A Service Guide for more
information.
The security code is stored in non-volatile
memory, and does not change when power has
been off, after a Factory Reset (*RST
command), or after an Instrument Preset
(SYSTem:PRESet command).

Example
The following command sets a new calibration security code (the
instrument must be unsecured).
CAL:SEC:CODE T3ST_DUT165

See Also
CALibration Subsystem Introduction
CALibration:SECure:STATe

CALibration:SECure:STATe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALibration:SECure:STATe <state>,<code>
CALibration:SECure:STATe?

Description
This command unsecures or secures the instrument for calibration. This
feature requires you to provide a security code to prevent accidental or
unauthorized calibrations of the instrument. Before you can calibrate the
instrument, you must unsecure it by entering the correct security code.
For a more detailed discussion of the calibration
procedures, see the Keysight 34970A/34972A Service
Guide. Please refer to that guide before attempting to
calibrate the instrument as improper use of the
CALibration commands can adversely affect the
accuracy and reliability of the instrument.
Used With:
Internal DMM

Parameters
Name Type Range of Default Value
Values
<state> Boolean {OFF|0|ON|1} ON
<code> String This is a
A string of up required
to 12 parameter.
characters.
You do not
have to use
all 12
characters
but the first
character
must always
be a letter (A-
Z). The
remaining 11
characters
can be
letters,
numbers (0-
9), or the
underscore
character
("_"). Blank
spaces are
not allowed.

Remarks
When you first receive your instrument, it is
secured, and the security code is set to
"HP034970" or "AT034972", depending on the
product number. Note that the third character of
the security code is a zero (0) and not a capital
O.
Once you enter a security code, that code must
be used for both front-panel and remote
operation. For example, if you secure the
instrument from the front panel, you must use
that same code to unsecure it from the remote
interface.
Unsecuring the instrument using this command
enables the internal DMM to be calibrated.
To calibrate the internal DMM, use the
CALibration? command.
The calibration security setting is stored in non-
volatile memory, and does not change when
power has been off, after a Factory Reset
(*RST command), or after an Instrument Preset
(SYSTem:PRESet command).

Return Format
The query returns 0 (OFF) or 1 (ON), indicating the current calibration
security setting.

Examples
The following command unsecures the instrument. Note that the
"HP034970" string applies to the 34970A; the "AT034972" string applies
to the 34972A.
CAL:SEC:STAT OFF,HP034970
The following query returns the current calibration security setting. In this
case, it is OFF.
CAL:SEC:STAT?
Typical Response: 0

See Also
CALibration Subsystem Introduction
CALibration:SECure:CODE

CALibration:STRing
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALibration:STRing <quoted_string>
CALibration:STRing?

Description
This command allows you to store one message in calibration memory in
the mainframe. For example, you can store such information as the date
when the last calibration was performed, the date when the next
calibration is due, the instrument's serial number, or even the name and
phone number of the person to contact for a new calibration.
For a more detailed discussion of
the calibration procedures, see the
Keysight 34970A/34972A Service
Guide. Please refer to that guide
before attempting to calibrate the
instrument as improper use of the
CALibration commands can
adversely affect the accuracy and
reliability of the instrument.
Used With:
Internal DMM

Parameters
| Name            | Type         | Range	of | Default    |
| --------------- | ------------ | -------- | ---------- |
|                 |              | Values   | Value      |
| <quoted_string> | Quoted       | A	string | This	is	a  |
|                 | ASCII	String | of	up	to | required   |
|                 |              | 40       | parameter. |
characters
enclosed
in	quotes.
You	can
use	letters
(A-Z),
numbers
(0-9),	and
special
characters
like	"@",
"%",	"*",
and	so	on.

Remarks
You can record a calibration message only from
the remote interface and only when the
instrument is unsecured (see
CALibration:SECure:STATe OFF command).
You can read the message from either the
front-panel or over the remote interface. You
can read the calibration message whether the
instrument is secured or unsecured.
The calibration message may contain up to 40
characters. From the front panel, you can view
only 13 characters of the message at a time.
From the front panel, commas, periods, and
semicolons share a display space with the
preceding character, and are not considered
individual characters.
Storing a calibration message will overwrite any
message previously stored in memory.
The calibration message is stored in non-
volatile memory, and does not change when
power has been off, after a Factory Reset
(*RST command), or after an Instrument Preset

(SYSTem:PRESet command).

Return Format
The query returns an ASCII string enclosed in double quotes. If no
calibration message has been specified, an empty quoted string ("") is
returned.

Examples
The following command stores a message in calibration memory in the
mainframe.
CAL:STR "CAL: 18 Aug 2009" or CAL:STR 'CAL: 18
Aug 2009'
The following query returns the message currently stored in calibration
memory in the mainframe (the quotes are also returned).
CAL:STR?
Typical Response: "CAL: 18 Aug 2009"

See Also
CALibration Subsystem Introduction
CALibration:SECure:STATe

CALibration:VALue
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CALibration:VALue <value>
CALibration:VALue?

Description
This command specifies the value of the known calibration signal as
outlined in the calibration procedures in the Keysight 34970A/34972A
Service Guide. This command is used for internal DMM calibrations.
For a more detailed discussion of the calibration
procedures, see the Keysight 34970A/34972A Service
Guide. Please refer to that guide before attempting to
calibrate the instrument as improper use of the
CALibration commands can adversely affect the
accuracy and reliability of the instrument.

Parameters
| Name | Type | Range	of | Default	Value |
| ---- | ---- | -------- | ------------- |
Values
| <value> |     | Desired | This	is	a |
| ------- | --- | ------- | --------- |
Numeric
|     |     | calibration   | required   |
| --- | --- | ------------- | ---------- |
|     |     | signal	in	the | parameter. |
units
specified	by
the	present
measurement
function.

Remarks
The internal DMM is an optional assembly for
the Keysight 34970A/34972A. The instrument
generates an error with this command if the
internal DMM is disabled (see
INSTrument:DMM command) or not installed in
the mainframe.

Return Format
The query returns the calibration value in the form +1.00000000E-01.

Examples
The following command sets calibration value to +10.001010 volts.
CAL:VAL 10.001010
The following query returns the present calibration value.
CAL:VAL?
Typical Response: +1.00101000E+01

See Also
CALibration Subsystem Introduction
CALibration?

CONFigure Subsystem Introduction
The CONFigure commands provide the most flexible way to program the
instrument for measurements. When you execute these commands, the
instrument uses default values for the requested measurement
configuration (like the MEASure? command). However, the measurement
is not automatically started and you can change some measurement
attributes before actually initiating the measurement. This allows you to
incrementally change the instrument's configuration from the default
conditions.
Use the INITiate or READ? command to initiate the
measurement.
A MEASure command is simply a CONFigure command
followed by a READ?
If you specify a <ch_list> with one of these commands, that
<ch_list> overwrites the current scan list.
The CONFigure commands are valid only with the following Keysight
34970A/34972A plug-in modules which can be configured to be part of a
scan. If the internal DMM is not installed or is disabled, then no DMM-
related configurations are allowed. However, scanning is allowed on the
digital input and totalizer channels even without the internal DMM.
34901A 20-Channel Armature Multiplexer (2-wire
or 4-wire)
34902A 16-Channel Reed Multiplexer (2-wire or 4-
wire)
34907A Multifunction Module (digital input and
totalizer channels only)
34908A 40-Channel Armature Multiplexer (2-wire
only)

Command Summary
CONFigure?
CONFigure:CURRent:AC
CONFigure:CURRent:DC
CONFigure:DIGital:BYTE
CONFigure:FREQuency
CONFigure:FRESistance
CONFigure:PERiod
CONFigure:RESistance
CONFigure:TEMPerature
CONFigure:TOTalize
CONFigure:VOLTage:AC
CONFigure:VOLTage:DC

CONFigure?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CONFigure? [(@<ch_list>)]

Description
This query returns the present configuration on the specified channels
and returns a series of quoted strings.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital I/O only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
If the internal DMM is not installed or is disabled, then no DMM-
related configurations are allowed. However, scanning is allowed
on the digital input and totalizer channels even without the internal
DMM.
The *RST command will clear the scan list and set all
measurement parameters to their factory settings. The Instrument
Preset (SYSTem:PRESet command) will not clear the scan list;
however, this command will clear reading memory and all stored
statistical data.

Return Format
The query returns a series of comma-separated fields indicating the
present function, range, and resolution for the specified channels.
Multiple responses are separated by commas. The short form of the
function name is always returned (e.g., "CURR:AC", "FREQ", etc.).
Example: Multiplexer Channel
Example: Digital I/O Channel
Example: Totalizer Channel

Examples
The following program segment configures multiplexer channels 03 and
08 in slot 100 and then reads back the configuration (the quotes are also
returned).
CONF:RES 1000,1,(@103)
CONF:TEMP THER,5000,1,0.1,(@108)
CONF? (@103,108)
Typical Response: "RES +1.000000E+03,+1.000000E-01","TEMP
THER,5000,+1.000000E+00,+1.000000E-04"
The following query returns the present configuration of every channel in
the scan list.
CONF?

See Also
CONFigure Subsystem Introduction

CONFigure:CURRent:AC
CONFigure:CURRent:DC
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CONFigure:CURRent:AC [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:CURRent:DC [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)

Description
These commands configure the channels for AC or DC current
measurements but do not initiate the scan.
The CONFigure command does not place the instrument in the "wait-for-
trigger" state. Use the INITiate or READ? command in conjunction with
CONFigure to place the instrument in the "wait-for-trigger" state.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module (channels 21
and 22 only)

Parameters
Name Type Range of Values Default
Value
<range> Numeric AUTO
Expected value in amps
(ranges shown below).
10 mA (MIN)
100 mA
1 A (MAX)
<resolution> Numeric Desired resolution in amps. Fixed at
6½ digits
<scan_list> Scan This is a
List One or more channels, required
as shown: parameter.
(@321) - channel 21 on
the module in slot 300.
(@221:222) - channels
21 through 22 on the
module in slot 200.
(@121:122,222,321:322)
- channels 21 and 22 on
the module in slot 100,
channel 22 on the
module in slot 200, and
channels 21-22 on the
module in slot 300.
Note that the channels
must be of the form s21
and s22, where s is the

first digit of the slot
number.

Remarks
When you specify a range of channels with this command, any
channels that are invalid will be ignored (no error will be
generated) but the first and last channel in the range must be valid
for the selected function.
You can allow the instrument to automatically select the
measurement range using autoranging or you can select a fixed
range using manual ranging. Autoranging is convenient because
the instrument decides which range to use for each measurement
based on the input signal. For fastest scanning operation, use
manual ranging on each measurement (some additional time is
required for autoranging since the instrument has to make a range
selection).
If you select autoranging (by specifying "AUTO" or "DEF"), an
error will be generated if you specify a discrete value for the
<resolution> parameter. When autoranging is combined with a
discrete resolution, the instrument cannot accurately resolve the
integration time (especially if the input signal is continuously
changing). If your application requires autoranging, be sure to
specify "AUTO" for the <resolution> parameter or omit the
parameter from the command.
Autorange thresholds:
Down range at: <10% of range
Up range at: >120% of range
Because this command resets all measurement parameters on the
specified channels to their default values, be sure to send the
CONFigure command before setting any other measurement
parameters.
If the input signal is greater than can be measured on the selected
range (manual ranging), the instrument gives an overload

indication: "±OVLD" from the front panel or "±9.9E+37" from the
remote interface.
For AC measurements, the resolution is fixed at 6½ digits. The
only way to control the reading rate for AC measurements is by
changing the channel delay or by setting the AC filter to the
highest frequency limit. The <resolution> parameter only affects
the number of digits shown on the front panel.
The *RST command will clear the scan list and set all
measurement parameters to their factory settings. The Instrument
Preset (SYSTem:PRESet command) will not clear the scan list;
however, this command will clear reading memory and all stored
statistical data.

Examples
These commands show the CONFigure:CURRent:AC command. In each
case, you could substitute the CONFigure:CURRent:DC command and
the example would be valid.
The following program segment configures the instrument for AC current
measurements on channel 21 in slot 100. The READ? command places
the instrument in the "wait-for-trigger" state, scans the channel once, and
then sends the reading to reading memory and the instrument's output
buffer. The default range (autorange) and resolution (fixed at 6½ digits)
are used for the measurement.
CONF:CURR:AC (@121)
ROUT:SCAN (@121)
READ?
Typical Response: +8.54530000E-02
The following program segment configures the instrument for an AC
current measurement on channels 21 and 22 in slot 100. The INITiate
command places the instrument in the "wait-for-trigger" state, scans the
channels once, and stores the readings in memory. The FETCh?
command transfers the readings from reading memory to the
instrument's output buffer. The 1 A range is selected with 200 mA
resolution.
CONF:CURR:AC 1,0.2,(@121,122)
ROUT:SCAN (@121,122)
INIT
FETC?
Typical Response: +4.27150000E-02,+1.32130000E-03

See Also
CONFigure?
FETCh?
INITiate
READ?
MEASure:CURRent:AC?
MEASure:CURRent[:DC]?
ROUTe:CHANnel:DELay
ROUTe:SCAN
[SENSe:]CURRent:AC:BANDwidth

CONFigure:DIGital:BYTE
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
CONFigure:DIGital:BYTE (@<scan_list>)

Description
This command configures the instrument to scan the specified digital
input channels on the multifunction module as byte data, but does not
initiate the scan. This command redefines the scan list.
Used With:
34907A Multifunction Module (digital input only)

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <scan_list> | Scan |     | This	is	a |
| ----------- | ---- | --- | --------- |
One	or	more	digital
|     | list |                  | required   |
| --- | ---- | ---------------- | ---------- |
|     |      | I/O	channels,	as | parameter. |
shown:
(@301)	-	channel	01
on	the	module	in	slot
300.
(@101:102,201,302)
-	channels	01	and
02	on	the	modules
on	slot	100,	channel
01	on	the	module	in
slot	200,	and
channel	02	on	the
module	in	slot	300.

Remarks
The digital input channels are numbered "s01" (LSB) and "s02"
(MSB), where s is the first digit of the slot number.
Note that if you include both digital input channels in the scan list,
the instrument will read data from both ports simultaneously with
the same time stamp. This allows you to externally combine the
two 8-bit value into one 16-bit value.

Example
The following command configures the instrument to scan channels 01
and 02 on slot 100 as byte data.
CONF:DIG:BYTE (@101:102)

See Also
CONFigure Subsystem Introduction

CONFigure:FREQuency
CONFigure:PERiod
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CONFigure:FREQuency [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:PERiod [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)

Description
These commands configure the channels for frequency or period
measurements, but they do not initiate the scan.
The CONFigure command does not place the instrument in the "wait-for-
trigger" state. Use the INITiate or READ? command in conjunction with
CONFigure to place the instrument in the "wait-for-trigger" state.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <range> | Numeric |     | AUTO |
| ------- | ------- | --- | ---- |
Expected	value	in	Hz
(frequency)	or	seconds
(period).	Valid	values
range	from	3	Hz	to	300
kHz,	and	their	inverses
(for	period).
For	frequency	and	period
measurements,	this
parameter	is	only	used	in
conjunction	with	the
<resolution>	parameter
to	set	the	gate	time.	It	is
otherwise	unnecessary
for	frequency	and	period
measurements.
| <resolution> | Numeric | Desired	resolution	in	Hz | 0.000003   |
| ------------ | ------- | ------------------------ | ---------- |
|              |         | (frequency)	or	seconds   | x	Range    |
|              |         | (period).                | (1	PLC)    |
| <scan_list>  | Scan    |                          | This	is	a  |
|              | List    | One	or	more	channels,    | required   |
|              |         | as	shown:                | parameter. |
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.

(@202:207,209,302:308)
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
When you specify a range of channels with this command, any
channels that are invalid will be ignored (no error will be
generated) but the first and last channel in the range must be valid
for the selected function.
If the input signal is greater than can be measured on the selected
range (manual ranging), the instrument gives an overload
indication: "±OVLD" from the front panel or "±9.9E+37" from the
remote interface.
The *RST command will clear the scan list and set all
measurement parameters to their factory settings. The Instrument
Preset (SYSTem:PRESet command) will not clear the scan list;
however, this command will clear reading memory and all stored
statistical data.

Examples
The following program segment configures the instrument for frequency
measurements on channel 04 in slot 300. The READ? command places
the instrument in the "wait-for-trigger" state, scans the channel once, and
then sends the reading to reading memory and the instrument's output
buffer. The default range (autorange) and resolution (fixed at 6½ digits)
are used for the measurement.
CONF:FREQ (@304)
ROUT:SCAN (@304)
READ?
Typical Response: +1.32130000E+03
The following program segment configures the instrument for frequency
measurements on channels 03 and 08 in slot 100. The INITiate
command places the instrument in the "wait-for-trigger" state, scans the
channels once, and stores the readings in memory. The FETCh?
command transfers the readings from reading memory to the
instrument's output buffer.
CONF:FREQ 100,(@103,108)
ROUT:SCAN (@103,108)
INIT
FETC?
Typical Response: +4.27150000E+03,+1.32130000E+03
The following program segment configures channel 10 on the module in
slot 300 for a frequency measurement. The READ? command places the
instrument in the "wait-for-trigger" state, initiates a trigger, and then

sends the reading to reading memory and the instrument's output buffer.
The default range (autorange) and resolution (fixed at 6½ digits) are
used for the measurement.
CONF:FREQ (@310)
READ?
Typical Response: +10.13240000E+03

See Also
CONFigure?
FETCh?
INITiate
MEASure:FREQuency?
MEASure:PERiod?
READ?
ROUTe:SCAN
[SENSe:]FREQuency:RANGe:LOWer
[SENSe:]FREQuency:VOLTage:RANGe:AUTO

CONFigure:RESistance
CONFigure:FRESistance
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CONFigure:RESistance [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:FRESistance [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)

Description
These commands configure the channels for 2-wire (RESistance) or 4-
wire (FRESistance) resistance measurements but do not initiate the
scan.
The CONFigure command does not place the instrument in the "wait-for-
trigger" state. Use the INITiate or READ? command in conjunction with
CONFigure to place the instrument in the "wait-for-trigger" state.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module (does not
support 4-wire measurement)

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <range> | Numeric |     | AUTO |
| ------- | ------- | --- | ---- |
Expected	value	in	ohms,
up	to	100	MW.
| <resolution> | Numeric | Desired	resolution	in	ohms. | 0.000003 |
| ------------ | ------- | --------------------------- | -------- |
x	Range
(1	PLC)
| <scan_list> | Scan |     | This	is	a |
| ----------- | ---- | --- | --------- |
One	or	more	channels,
|     | List |           | required   |
| --- | ---- | --------- | ---------- |
|     |      | as	shown: | parameter. |
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
For the FRESistance version of this command, channel n is paired
with channel n+10 (34901A) or n+8 (34902A) to provide source
and sense connections.
When you specify a range of channels with this command, any
channels that are invalid will be ignored (no error will be
generated) but the first and last channel in the range must be valid
for the selected function.
You can allow the instrument to automatically select the
measurement range using autoranging or you can select a fixed
range using manual ranging. Autoranging is convenient because
the instrument decides which range to use for each measurement
based on the input signal. For fastest scanning operation, use
manual ranging on each measurement (some additional time is
required for autoranging since the instrument has to make a range
selection).
If you select autoranging (by specifying "AUTO" or "DEF"), an
error will be generated if you specify a discrete value for the
<resolution> parameter. When autoranging is combined with a
discrete resolution, the instrument cannot accurately resolve the
integration time (especially if the input signal is continuously
changing). If your application requires autoranging, be sure to
specify "AUTO" for the <resolution> parameter, or omit the
parameter from the command and use the
[SENSe:]VOLTage[:DC]NPLC command to specify the desired
integration time.
Autorange thresholds:
Down range at: <10% of range
Up range at: >120% of range
Since these commands reset all measurement parameters on the

specified channels to their default values, be sure to send the
CONFigure command before setting any other measurement
parameters.
If the input signal is greater than can be measured on the selected
range (manual ranging), the instrument gives an overload
indication: "±OVLD" from the front panel or "±9.9E+37" from the
remote interface.
The *RST command will clear the scan list and set all
measurement parameters to their factory settings. The Instrument
Preset (SYSTem:PRESet command) will not clear the scan list;
however, this command will clear reading memory and all stored
statistical data.

Examples
The following program segment configures the instrument for 2-wire
resistance measurements on channel 04 in slot 300. The READ?
command places the instrument in the "wait-for-trigger" state, scans the
channel once, and then sends the reading to reading memory and the
instrument's output buffer. The default range (autorange) and resolution
(1 PLC) are used for the measurement.
CONF:RES (@304)
ROUT:SCAN (@304)
READ?
Typical Response: +1.32130000E+04
The following program segment configures the instrument for 2-wire
resistance measurements on channels 03 and 08 in slot 100. The
INITiate command places the instrument in the "wait-for-trigger" state,
scans the channels once, and stores the readings in memory. The
FETCh? command transfers the readings from reading memory to the
instrument's output buffer. The 1 kΩ range is selected with 1Ω resolution.
CONF:RES 1000,1,(@103,108)
ROUT:SCAN (@103,108)
INIT
FETC?
Typical Response: +4.27150000E+02,+1.32130000E+02
The following program segment configures the instrument for 4-wire
resistance measurements on channels 03 and 08 in slot 100. The
INITiate command places the instrument in the "wait-for-trigger" state,

scans the channels once, and stores the readings in memory. The
FETCh? command transfers the readings from reading memory to the
instrument's output buffer. The 1 kΩ range is selected with 1Ω resolution.
CONF:FRES 1000,1,(@301,302) ! Note that for a 4-wire
measurement, channels
! 301 and 302 are
automatically paired with
! 311 and 312,
respectively (34901A module).
ROUT:SCAN (@301,302)
INIT
FETC?
Typical Response: +4.27150000E+02,+1.32130000E+02

See Also
CONFigure Subsystem Introduction
CONFigure?
FETCh?
INITiate
MEASure:RESistance?
MEASure:FRESistance?
READ?
ROUTe:SCAN
[SENSe:]RESistance:OCOMpensated

CONFigure:TEMPerature
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CONFigure:TEMPerature {<probe_type>|DEF},{<type>|DEF}[,1[,
{<resolution>|MIN|MAX|DEF}]] ,(@<scan_list>)

Description
These	commands	configure	the	channels	for	temperature	measurements
but	do	not	initiate	the	scan.	If	you	omit	the	optional	<ch_list>	parameter,
this	command	applies	to	the	currently	defined	scan	list.
The	CONFigure	command	does	not	place	the	instrument	in	the	"wait-for-
trigger"	state.	Use	the	INITiate	or	READ?	command	in	conjunction	with
CONFigure	to	place	the	instrument	in	the	"wait-for-trigger"	state.
The	following	table	shows	which	temperature	transducers	are	supported
by	each	of	the	multiplexer	modules.

| Module | Thermocouple | RTD RTD | Thermistor |
| ------ | ------------ | ------- | ---------- |
|        |              | 2- 4-   |            |
Wire Wire
|     | Yes | Yes Yes | Yes |
| --- | --- | ------- | --- |
34901A
Armature
Multiplexer
| 34902A | Yes | Yes Yes | Yes |
| ------ | --- | ------- | --- |
Reed
Multiplexer
| 34908A   | Not          | Yes No | Yes |
| -------- | ------------ | ------ | --- |
| Armature | Recommended1 |        |     |
Multiplexer
(1-Wire)
1
With	a	one-wire	multiplexer,	even	very	small	ground	currents	can
introduce	substantial	measurement	error.

Parameters
| Name         | Type     |     | Range	of	Values | Default	Value |
| ------------ | -------- | --- | --------------- | ------------- |
| <probe_type> | Discrete |     |                 | TCouple       |
{TCouple|RTD|FRTD|THERmistor|DEF}
| <type> | Discrete |     | {B|E|J|K|N|R|S|T} |     |
| ------ | -------- | --- | ----------------- | --- |
For	TCouple:
For
TCouple:
For	RTD {85|91}
|     |     | For	FRTD       | {85|91}           | For	RTD  |
| --- | --- | -------------- | ----------------- | -------- |
|     |     | For	THERmistor | {2252|5000|10000} | For	FRTD |
For
THERmistor
<resolution> Numeric The	resolution	in	degrees	Celsius, 1	PLC
Fahrenheit,	or	Kelvin.	The	temperature
scale	in	use	is	specified	by	the
UNIT:TEMPerature	command.
| <scan_list> | Scan |     |     | This	is	a	required |
| ----------- | ---- | --- | --- | ------------------ |
One	or	more	channels,	as	shown:
|     | List |     |     | parameter. |
| --- | ---- | --- | --- | ---------- |
(@310)	-	channel	10	on	the	module	in
slot	300.
(@305:310)	-	channels	05	through	10
on	the	module	in	slot	300.
(@202:207,209,302:308)	-	channels	02
through	07	and	09	on	the	module	in	slot
200	and	channels	02	through	08	on	the
module	in	slot	300.

Remarks
For temperature measurements, the instrument internally selects
the range; you cannot select which range is used. In the command
syntax, be sure to include "1" as shown for the <range> parameter
(preceding the <resolution> parameter).
For RTD and FRTD measurements, use "85" to specify a =
0.00385 or "91" to specify a = 0.00391. Note that this command
also redefines the scan list. The default (DEF) type is "85" (a =
0.00385).
When you specify a range of channels with this command, any
channels that are invalid will be ignored (no error will be
generated) but the first and last channel in the range must be valid
for the selected function.
For thermocouple measurements, the instrument internally selects
the 100 mV range. For thermistor and RTD measurements, the
instrument autoranges to the correct range for the transducer
resistance measurement. Specify the paired channel in the lower
bank (source) as the <ch_list> channel.
Thermocouple measurements require a reference junction
temperature (see
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE
command). For the reference junction temperature, you can use
an internal measurement on the module's terminal block (34901A
only), an external thermistor or RTD measurement, or a known
fixed junction temperature. If you select an external reference, the
instrument makes thermocouple measurements relative to a
previously-stored RTD or thermistor measurement stored in the
reference register.
By default, a fixed reference junction temperature of 0.0 °C is used
(see [SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction

command).
If you select autoranging (by specifying "AUTO" or "DEF"), an
error will be generated if you specify a discrete value for the
<resolution> parameter. When autoranging is combined with a
discrete resolution, the instrument cannot accurately resolve the
integration time (especially if the input signal is continuously
changing). If your application requires autoranging, be sure to
specify "DEF" for the <resolution> parameter, or omit the
parameter from the command and use the
[SENSe:]TEMPerature:NPLC command to specify the desired
integration time.
Since this command resets all measurement parameters on the
specified channels to their default values, be sure to send the
CONFigure command before setting any other measurement
parameters.
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
Because channels are automatically paired for 4-wire resistance
measurements (see previous Remark), attempts to re-configure
the paired channel in Bank 2 will result in an error. For example:
CONF:VOLT:DC (@105) !Configure Bank 2 channel for
DC voltage measurements
ROUT:SCAN (@101:110) !Add channels to scan list
CONF:FRES (@101) !Generates error and clears
scan list

For 4-wire RTD measurements, the instrument automatically
enables the autozero function.
The *RST command will clear the scan list and set all
measurement parameters to their factory settings. The Instrument
Preset (SYSTem:PRESet command) will not clear the scan list;
however, this command will clear reading memory and all stored
statistical data.

Examples
The following program segment configures the instrument for B-type
thermocouple measurements on channel 04 in slot 300. The READ?
command places the instrument in the "wait-for-trigger" state, scans the
channel once, and then sends the reading to reading memory and the
instrument's output buffer. The default resolution (fixed at 6½ digits) is
used for the measurement (assumes default temperature units).
CONF:TEMP TC,B,(@304)
ROUT:SCAN (@304)
READ?
Typical Response: +3.65640000E+01
The following program segment configures the instrument for 5 kΩ
thermistor measurements on channels 03 and 08 in slot 100. The
INITiate command places the instrument in the "wait-for-trigger" state,
scans the channels once, and stores the readings in memory. The
FETCh? command transfers the readings from reading memory to the
instrument's output buffer. This 2-wire measurement is made with 0.1 °C
resolution (assumes default temperature units).
CONF:TEMP THER,5000,1,0.1,(@103,108)
ROUT:SCAN (@103,108)
INIT
FETC?
Typical Response: +2.47150000E+01,+3.12130000E+01
The following program segment configures the current scan list for a 2-
wire RTD measurement (no <ch_list> is specified). The READ?

command places the instrument in the "wait-for-trigger" state, initiates a
trigger, and then sends the reading to reading memory and the
instrument's output buffer. The default resolution (fixed at 6½ digits) is
used for the measurement (assumes default temperature units).
CONF:TEMP RTD,85 (@203)
READ?
Typical Response:+2.12320000E+01

See Also
CONFigure?
FETCh?
INITiate
MEASure:TEMPerature?
READ?
ROUTe:SCAN
[SENSe:]TEMPerature:NPLC
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]
UNIT:TEMPerature

CONFigure:TOTalize
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CONFigure:TOTalize <mode>,(@<scan_list>)

Description
This command configures the instrument to read the specified totalizer
channels on the multifunction module but does not initiate the scan. To
read the totalizer during a scan without resetting the count, set the
<mode> to READ. To read the totalizer during a scan and reset the count
to 0 after it is read, set the <mode> to RRESet (this means "read and
reset").
The CONFigure command does not place the instrument in the "wait-for-
trigger" state. Use the INITiate or READ? command in conjunction with
CONFigure to place the instrument in the "wait-for-trigger" state.
Used With:
34907A Multifunction Module (totalize channel only)

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <mode>      | Discrete | {READ|RRESet} | READ      |
| ----------- | -------- | ------------- | --------- |
| <scan_list> | Scan     |               | This	is	a |
One	or	more
|     | List |           | required   |
| --- | ---- | --------- | ---------- |
|     |      | totalizer | parameter. |
channels,	as
shown:
(@303)	-
channel	03	on
the	module	in
slot	300.
(@103,203,303)
-	channel	03	on
the	modules	on
slot	100,	200,
and	300.

Remarks
The totalizer channel is always of the form s03, where s is the first
digit of the slot number.
The maximum count is 67,108,863 (226 - 1). The count rolls over
to 0 after reaching the maximum allowed value.
If the count rolls over to 0, the "Totalizer Overflow" bit (bit 11) is set
in the Questionable Data register. For more information on the
Status System for the instrument, see Status System Introduction.
Selecting the RRESet mode performs a synchronized read and
reset operation on the specified totalizer channels. If you were to
use discrete commands, such as READ? and
[SENSe:]TOTalize:CLEar:IMMediate, you would likely lose counts
occurring between the two commands.
The *RST command will clear the scan list and set all
measurement parameters to their factory settings. The Instrument
Preset (SYSTem:PRESet command) will not clear the scan list;
however, this command will clear reading memory and all stored
statistical data.

Examples
The following command configures totalizer channel 03 on the module in
slot 200 to be read without resetting its count.
CONF:TOT READ,(@203)
The following command configures totalizer channel 03 on the module in
slot 300 to be reset to 0 after it is read.
CONF:TOT RRES,(@303)

See Also
CONFigure Subsystem Introduction
CONFigure?
FETCh?
INITiate
READ?
[SENSe:]TOTalize:DATA?

CONFigure:VOLTage:AC
CONFigure:VOLTage:DC
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
CONFigure:VOLTage:AC [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:VOLTage:DC [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)

Description
These commands configure the channels in the <scan_list> for AC or
DC voltage measurements but do not initiate the scan.
The CONFigure command does not place the instrument in the "wait-for-
trigger" state. Use the INITiate or READ? command in conjunction with
CONFigure to place the instrument in the "wait-for-trigger" state.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <range> | Numeric |     | AUTO |
| ------- | ------- | --- | ---- |
Expected	value	in	volts
| <resolution> | Numeric | Desired	resolution	in	volts. | 0.000003 |
| ------------ | ------- | ---------------------------- | -------- |
x	Range
(1	PLC)
| <scan_list> | Scan |                       | This	is	a |
| ----------- | ---- | --------------------- | --------- |
|             | List | One	or	more	channels, | required  |
as	shown:
parameter.
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
When you specify a range of channels with this command, any
channels that are invalid will be ignored (no error will be
generated) but the first and last channel in the range must be valid
for the selected function.
You can allow the instrument to automatically select the
measurement range using autoranging or you can select a fixed
range using manual ranging. Autoranging is convenient because
the instrument decides which range to use for each measurement
based on the input signal. For fastest scanning operation, use
manual ranging on each measurement (some additional time is
required for autoranging since the instrument has to make a range
selection).
If you select autoranging (by specifying "AUTO" or "DEF"), an
error will be generated if you specify a discrete value for the
<resolution> parameter. When autoranging is combined with a
discrete resolution, the instrument cannot accurately resolve the
integration time (especially if the input signal is continuously
changing). If your application requires autoranging, be sure to
specify "AUTO" for the <resolution> parameter or omit the
parameter from the command.
Autorange thresholds:
Down range at: <10% of range
Up range at: >120% of range
Because this command resets all measurement parameters on the
specified channels to their default values, be sure to send the
CONFigure command before setting any other measurement
parameters.
If the input signal is greater than can be measured on the selected
range (manual ranging), the instrument gives an overload

indication: "±OVLD" from the front panel or "±9.9E+37" from the
remote interface.
For AC measurements, the resolution is fixed at 6½ digits. The
only way to control the reading rate for AC measurements is by
changing the channel delay or by setting the AC filter to the
highest frequency limit. The <resolution> parameter only affects
the number of digits shown on the front panel.
The *RST command will clear the scan list and set all
measurement parameters to their factory settings. The Instrument
Preset (SYSTem:PRESet command) will not clear the scan list;
however, this command will clear reading memory and all stored
statistical data.

Examples
These commands show the CONFigure:VOLTage:AC command. In each
case, you could substitute the CONFigure:VOLTage:DC command and
the example would be valid.
The following program segment configures the instrument for AC voltage
measurements on channel 04 in slot 300. The READ? command places
the instrument in the "wait-for-trigger" state, scans the channel once, and
then sends the reading to reading memory and the instrument's output
buffer. The default range (autorange) and resolution (fixed at 6½ digits)
are used for the measurement.
CONF:VOLT:AC (@304)
ROUT:SCAN (@304)
READ?
Typical Response: +1.86850000E-03
The following program segment configures the instrument for AC voltage
measurements on channels 03 and 08 in slot 100. The INITiate
command places the instrument in the "wait-for-trigger" state, scans the
channels once, and stores the readings in memory. The FETCh?
command transfers the readings from reading memory to the
instrument's output buffer. The 1 V range is selected.
CONF:VOLT:AC 1,(@103,108)
ROUT:SCAN (@103,108)
INIT
FETC?
Typical Response: +4.27150000E-03,+1.32130000E-03

The following program segment configures channel 10 on the module in
slot 300 for an AC voltage measurement. The READ? command places
the instrument in the "wait-for-trigger" state, initiates a trigger, and then
sends the reading to reading memory and the instrument's output buffer.
The default range (autorange) and resolution (fixed at 6½ digits) are
used for the measurement.
CONF:VOLT:AC (@310)
READ?
Typical Response: +1.26360000E-02

See Also
CONFigure Subsystem Introduction
CONFigure:CURRent:AC
CONFigure?
FETCh?
INITiate
MEASure[:VOLTage]:AC?
MEASure[:VOLTage][:DC]?
READ?
ROUTe:CHANnel:DELay
ROUTe:SCAN
[SENSe:]VOLTage:AC:BANDwidth

DATA Subsystem Introduction
Command Summary
DATA:LAST?
DATA:POINts?
DATA:POINts:EVENt:THReshold
DATA:POINts:EVENt:THReshold?
DATA:REMove?

DATA:LAST?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
DATA:LAST? [<num_rdgs>,](@<channel>)

Description
This query returns the most recent reading or readings taken on the
specified channel during the scan.

Parameters
| Name       | Type    | Range	of   | Default |
| ---------- | ------- | ---------- | ------- |
|            |         | Values     | Value   |
| <num_rdgs> | Numeric | An	integer | 1       |
from	1	to	the
number	of
readings
stored	in
memory	for
the	specified
<channel>.
| <channel> | Channel |          | This	is	a  |
| --------- | ------- | -------- | ---------- |
|           |         | A	single | required   |
|           |         | channel, | parameter. |
specified	as
in	the
following
examples.
(@310)	-
channel	10
on	the
module	in
slot	300.
(@214)	-
channel14
on	the
module	in
slot	200.

Remarks
The query returns the readings in order, starting with the earliest
reading in the group of recent readings. If you specify more
readings than are currently stored in memory, the instrument
generates an error message.
Readings can be acquired during a scan using the multiplexer or
digital modules.
Each reading is returned with some combination of measurement
units, time stamp, channel number, and alarm status information,
depending on the settings set by the FORMat:READing
commands. The time stamp is either in relative format (time in
seconds since the beginning of the scan) or absolute format (time
of day with date, based on the instrument's clock as set by the
SYSTem:DATE and SYSTem:TIME commands). The choice of
absolute and relative time is determined by the
FORMat:READing:TIME:TYPE command.

Return Format
The query returns the specified number of readings for the specified
channel (or the internal DMM). If no data is available for the specified
channel, the query returns 0 for each field.
For example:
1 Reading with Units (26.195 °C) 4 Channel Number
2 Date (November 21, 2004) 5 Alarm Limit Threshold Crossed (0
= No Alarm, 1 = LO, 2 = HI)
3 Time of Day (3:30:23.000 PM)

Example
The following query returns the last reading on channel 08 in slot 100.
DATA:LAST? (@108)
Typical Response: +1.84280000E-05
VDC,2004,11,21,14,54,33.104,108,0

See Also
DATA Subsystem Introduction
FORMat Subsystem Introduction
SYSTem:DATE
SYSTem:TIME

DATA:POINts?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
DATA:POINts?

Description
This query returns the total number of readings currently stored in
reading memory from a scan.

Remarks
You can read the count at any time, even during a scan.
You can store at least 50,000 readings in memory and all readings
are automatically time stamped. If memory overflows, a bit in the
STATus:QUEStionable:CONDition? register is set and new
readings will overwrite the first (oldest) readings stored. The most
recent readings are always preserved. Reading memory is not
cleared when you read it.
The questionable status bit will be cleared when memory is
cleared. The questionable status bit will not be cleared if memory
is emptied with DATA:REMove? or R?.
The instrument clears all readings from memory when a new scan
is initiated, when any measurement parameters are changed
(CONFigure and SENSe commands), and when the triggering
configuration is changed (TRIGger commands).
The instrument clears all readings from memory after a Factory
Reset (*RST command) or after an Instrument Preset
(SYSTem:PRESet command).

Return Format
The query returns a value between 0 and 50,000 as a signed integer,
indicating the number of readings currently stored in reading memory.

Example
The following query returns the number of readings in memory.
DATA:POIN?
Typical Response: +320

See Also
DATA Subsystem Introduction
DATA:REMove?

DATA:POINts:EVENt:THReshold
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
DATA:POINts:EVENt:THReshold <num_rdgs>
DATA:POINts:EVENt:THReshold?

Description
This command sets a bit in the Standard Operation Register group event
register when the specified number of readings have been stored in
reading memory from a scan. The "Memory Threshold" bit (bit 9) is set to
a "1" in the event register when the number of stored readings is greater
than or equal to the specified memory threshold.
For more information on the Status System for the
instrument, see Status System Introduction.

Parameters
| Name | Type | Range | Default	Value |
| ---- | ---- | ----- | ------------- |
of
Values
| <num_rdgs> | Numeric | An        | This	is	a  |
| ---------- | ------- | --------- | ---------- |
|            |         | integer   | required   |
|            |         | from	1	to | parameter. |
50,000
The	factory
default	value
is	1.

Remarks
To report any subsequent events, the reading count must first drop
below the programmed memory threshold before reaching the
threshold again. Use the R? or DATA:REMove command to
remove readings from memory.
To enable the "Memory Threshold" bit (bit 9) to be reported to the
Status Byte, use the STATus:OPERation:ENABle command.
Once the "Memory Threshold" bit is set, it will remain set until
cleared by the STATus:OPERation[:EVENt]? command or *CLS
(clear status) command.
The instrument resets the memory threshold to "1" after a Factory
Reset (*RST command) or when mainframe power is cycled. The
memory threshold value is not reset by the SYSTem:PRESet,
*CLS, or STATus:PRESet command.

Return Format
The query returns the number of readings currently specified as the
memory threshold as a signed integer.

Examples
The following command sets the memory threshold to 125 readings.
DATA:POIN:EVEN:THR 125
The following query reads the memory threshold setting.
DATA:POIN:EVEN:THR?
Typical Response: +125

See Also
DATA Subsystem Introduction
STATus:OPERation:ENABle

DATA:REMove?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
DATA:REMove? <num_rdgs>

Description
This query reads and clears the specified number of readings from the
non-volatile memory. This allows you to continue a scan without losing
data stored in memory (if memory becomes full, new readings will
overwrite the first readings stored). The specified number of readings are
cleared from memory, starting with the oldest reading.

Parameters
| Name       | Type    | Range	of     | Default    |
| ---------- | ------- | ------------ | ---------- |
|            |         | Values       | Value      |
| <num_rdgs> | Numeric | An	integer   | This	is	a  |
|            |         | representing | required   |
|            |         | the	number   | parameter. |
of	readings
to	be	read
and	erased
from
memory.

Remarks
You can remove readings from memory at any time, even during a
scan.
You can store at least 50,000 readings in memory during a scan.
Readings are stored only during a scan. If memory overflows, the
new readings will overwrite the first (oldest) readings stored; the
most recent readings are always preserved. In addition, bit 9 is set
in the Questionable Data Register's condition register (see Status
System Introduction).
If fewer than the specified number of readings are currently in
memory, an error will be generated. You can use the
DATA:POINts? query to determine the total number of readings
currently in memory.
Each reading is returned with some combination of measurement
units, time stamp, channel number, and alarm status information,
depending on the settings set by the FORMat:READing
commands. The time stamp is either in relative format (time in
seconds since the beginning of the scan) or absolute format (time
of day with date, based on the instrument's clock as set by the
SYSTem:DATE and SYSTem:TIME commands). The choice of
absolute and relative time is determined by the
FORMat:READing:TIME:TYPE command.
The instrument clears all readings from memory when a new scan
is initiated, when any measurement parameters are changed
(CONFigure and SENSe commands), and when the triggering
configuration is changed (TRIGger commands).
The instrument clears all readings from memory after a Factory
Reset (*RST command), after an Instrument Preset
(SYSTem:PRESet command), or when mainframe power is
cycled.

Return Format
The query returns the specified number of readings (with formatting as
set by the FORMat:READing commands) and then erases them from
memory. Multiple responses are separated by commas.

Example
The following query returns three readings (starting with the oldest
reading first) and erases them from memory.
DATA:REM? 3
Typical Response:
+4.27150000E+02,+1.32130000E+03,+3.65300000E+03

See Also
DATA Subsystem Introduction
DATA:POINts?
FORMat Subsystem Introduction
R?

DIAGnostic Subsystem Introduction
Command Summary
DIAGnostic:DMM:CYCLes?
DIAGnostic:DMM:CYCLes:CLEar
DIAGnostic:PEEK:SLOT:DATA?
DIAGnostic:POKE:SLOT:DATA
DIAGnostic:RELay:CYCLes?
DIAGnostic:RELay:CYCLes:CLEar

DIAGnostic:DMM:CYCLes?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
DIAGnostic:DMM:CYCLes?

Description
This query returns the cycle count of the three backplane relays on the
internal DMM. These relays open or close when a function or range is
changed on a module. The query returns three numbers indicating the
cycle count on relays 1, 2, and 3 (which correspond to relays K102,
K103, and K104 respectively).

Remarks
The internal DMM is an optional assembly for the Keysight
34970A/34972A. The instrument generates an error with this
command if the internal DMM is disabled (see INSTrument:DMM
command) or not installed in the mainframe.
To read the cycle count on the multiplexer and switch modules,
use the DIAGnostic:RELay:CYCLes? command.
See the Keysight 34970A/34972A Service Guide for information
on replacing relays.

Return Format
The query returns the cycle count on the specified internal DMM relay.

Example
The following query returns the cycle count on the three relays.
DIAG:DMM:CYCL?
Typical Response: +58023,+57291,+66239

See Also
DIAGnostic Subsystem Introduction
DIAGnostic:DMM:CYCLes:CLEar
DIAGnostic:RELay:CYCLes?

DIAGnostic:DMM:CYCLes:CLEar
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
DIAGnostic:DMM:CYCLes:CLEar {1|2|3}

Description
This command resets the relay cycle count on the specified internal
DMM relay.

Remarks
You must unsecure the instrument with
CALibration:SECure:STATe to reset the cycle count.

Example
The following command resets the relay cycle count on internal
DMM relay 2.
DIAGnostic:DMM:CYCLes:CLEar 2

See Also
DIAGnostic Subsystem Introduction
DIAGnostic:DMM:CYCLes?

DIAGnostic:PEEK:SLOT:DATA?
DIAGnostic:POKE:SLOT:DATA
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
DIAGnostic:PEEK:SLOT:DATA? {100|200|300}
DIAGnostic:POKE:SLOT:DATA {100|200|300}, <quoted_string>

Description
The POKE command allows you to add a custom label of up to 10
characters to the module in the specified slot. Characters beyond the
tenth character are truncated, and no error message is generated. The
PEEK query returns the label string.

Parameters
| Name            | Type   | Range	of     | Default    |
| --------------- | ------ | ------------ | ---------- |
|                 |        | Values       | Value      |
| <quoted_string> | Quoted | A	quoted     | This	is	a  |
|                 | ASCII  | ASCII        | required   |
|                 | String | string	of	up | parameter. |
to	10
characters.

Remarks
One possible use for this command is to allow you to differentiate
between modules of the same type from within your program.
The custom label is stored in non-volatile memory on the module.
You must unsecure the instrument with
CALibration:SECure:STATe OFF before you can store the custom
label.

Return Format
The PEEK query returns the label string.

Examples
The following command adds a label to the module in slot 200.
DIAG:POKE:SLOT:DATA 200,"TestMod1"
The following query returns the label associated with slot 200.
DIAG:PEEK:SLOT:DATA? 200
Typical Response: TestMod1

See Also
DIAGnostic Subsystem Introduction

DIAGnostic:RELay:CYCLes?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
DIAGnostic:RELay:CYCLes? (@<ch_list>)

Description
This query reads the cycle count on the specified channels. In addition to
the channel relays, you can also query the count on the Analog Bus
relays and bank relays.
Used With:
All modules except for 34907A

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel This is a
List One or more channels, as required
shown: parameter.
(@302) - channel 12 on the
module in slot 300.
(@311:314) - channels 11
through 14 on the module in
slot 300.
(@201:212,213,322:323,198)
- channels 1 through 12 and
13 on the module in slot 200,
channels 22 through 23 on
the module in slot 300, and
tree relay 98 on the module
in slot 100.

Remarks
On the RF Multiplexer modules, each bank
consists of two leaf relays and one tree relay
(see diagram below). The module stores the
cycle count for each of the three relays on all
four banks. The DIAGnostic:RELay:CYCLes?
query always returns the same count for
channels 111 and 112, 113 and 114, 121 and
122, and 123 and 124.
a. The reset state of the three relays is shown
above for Bank 1 (a reset operation selects
the lowest channel within the bank). The
cycle count for any of the three relays is
incremented whenever the relay transitions
from the reset state. Therefore, the cycle
count reflects a complete transition of the
relay from, and back to, the reset state. For

example, closing Channel 111 will not
increment the leaf relay cycle count, but
closing Channel 112 will increment the cycle
count.
To read the cycle count on the relays
associated with function selection and isolation
on the internal DMM, use the
DIAGnostic:DMM:CYCLes? command.
See the Keysight 34970A/34972A Service
Guide for information on replacing relays.

Return Format
The query returns the cycle count for each channel specified. The value
returned is between 0 and 4,294,967,294 (32-bit value). Multiple
responses are separated by commas.

Example
The following query returns the cycle count on channels 03 and 13 in slot
100.
DIAG:REL:CYCL? (@103,113)
Typical Response: +76289,+11055

See Also
DIAGnostic Subsystem Introduction
DIAGnostic:DMM:CYCLes?
DIAGnostic:RELay:CYCLes:CLEar

DIAGnostic:RELay:CYCLes:CLEar
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
DIAGnostic:RELay:CYCLes:CLEar (@<ch_list>)

Description
This command resets the cycle count on the specified channels.

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If this
List One or more channels, parameter
as shown: is
omitted,
(@310) - channel 10 on
the
the module in slot 300.
command
applies to
(@305:310) - channels
the
05 through 10 on the
current
module in slot 300.
scan list.
(@202:207,209,302:308)
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
The instrument must be unsecured in order to reset the cycle
count. See the CALibration:SECure:STATe command for more
information on unsecuring the instrument.
On the RF Multiplexer modules (34905A, 34906A), each bank
consists of two leaf relays and one tree relay (see
DIAGnostic:RELay:CYCLes? command). Clearing the cycle count
on a specific channel will clear the count on all three relays in the
corresponding bank.

Example
The following command clears the cycle count on channels 03 and 13 in
slot 100.
DIAG:REL:CYCL:CLE (@103,113)

See Also
DIAGnostic Subsystem Introduction
CALibration:SECure:STATe
DIAGnostic:RELay:CYCLes?

DISPlay Subsystem Introduction
Command Summary
DISPlay
DISPlay?
DISPlay:TEXT
DISPlay:TEXT?
DISPlay:TEXT:CLEar

DISPlay
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
DISPlay <state>
DISPlay?

Description
This command disables or enables the instrument's front-panel display.
For security reasons or for a slight increase in measurement rates, you
may want to turn off the front-panel display. When disabled, the entire
front-panel display goes dark and all display annunciators except
ERROR are disabled.

Parameters
| Name    | Type    | Range	of     | Default |
| ------- | ------- | ------------ | ------- |
|         |         | Values       | Value   |
| <state> | Boolean | {OFF|0|ON|1} | ON      |

Remarks
All keys except Local are disabled when the display is off.
You can disable the front-panel display from the remote interface
only.
Sending a text message to the display (see DISPlay:TEXT
command) overrides the display state; this means that you can
display a message even if the display is turned off.
The front-panel display is automatically enabled when power is
cycled, after a Factory Reset (*RST command), or after an
Instrument Preset (SYSTem:PRESet command). It is also enabled
when you press the Local key. The OFF state is remembered if
you return to remote.

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command disables the front-panel display.
DISP OFF
The following query returns the front-panel display setting.
DISP?
Typical Response: 0

See Also
DISPlay Subsystem Introduction
DISPlay:TEXT

DISPlay:TEXT
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
DISPlay:TEXT <quoted_string>
DISPlay:TEXT?

Description
This command displays a text message on the instrument's front-panel
display. The instrument can display up to 12 characters on the front
panel; any additional characters are truncated (no error is generated).

Parameters
Name Type Range of Default
Values Value
<quoted_string> Quoted A string This is a
ASCII of up to required
String 12 parameter.
characters
enclosed
in
quotation
marks.
You can
use letters
(A-Z),
numbers
(0-9), and
special
characters
like "@",
"%", "*",
and so on.
Use "#"
character
to display
a degree
symbol
( °).

Remarks
Commas, periods, colons, and semicolons share a display space
with the preceding character, and are not considered individual
characters.
While a message is displayed on the front panel, readings from a
scan or monitor are not sent to the front-panel display.
Sending a text message to the display overrides the display state
(see DISPlay:STATe command); this means that you can display a
message even if the display is turned off.
The display text is not stored as part of the instrument state by the
*SAV command.
The front-panel display is automatically cleared when power is
cycled, after a Factory Reset (*RST command), or after an
Instrument Preset (SYSTem:PRESet command).

Return Format
The query reads the message currently displayed on the front panel and
returns an ASCII string enclosed in double quotes. If no message is
displayed, a null string ( " " ) is returned.

Examples
The following commands display a message on the front panel (the
quotes are not displayed).
DISP:TEXT "SCANNING ..." or DISP:TEXT 'SCANNING
...'
The following query returns the message currently displayed on the front
panel (the quotes are also returned).
DISP:TEXT?
Typical Response: "SCANNING ..."

See Also
DISPlay Subsystem Introduction
DISPlay:TEXT:CLEar

DISPlay:TEXT:CLEar
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
DISPlay:TEXT:CLEar

Description
This command clears the text message displayed on the instrument's
front-panel display (see DISPlay:TEXT command).

Remarks
Clearing the text message does not override the display state (see
DISPlay:STATe command); if the display was disabled prior to
clearing the text message, the display will remain disabled.
The front-panel display is automatically cleared when power is
cycled, after a Factory Reset (*RST command), or after an
Instrument Preset (SYSTem:PRESet command).

Example
The following command clears the text message on the front panel.
DISP:TEXT:CLEAR

See Also
DISPlay Subsystem Introduction
DISPlay
DISPlay:TEXT

FORMat Subsystem Introduction
During a scan, the instrument automatically adds a time stamp to all
readings and stores them in memory. Each reading is also stored with
measurement units, time stamp, channel number, and alarm status
information. You can specify which information you want returned with
the readings (from the front panel, all of the information is available for
viewing). The reading format applies to all readings being removed from
the instrument from a scan; you cannot set the format on a per-channel
basis. The examples below show a reading in relative and absolute
format with all fields enabled.
Note that absolute format shows the time of day with the date, and
relative time shows the time since the start of the scan.
Relative Format (Default):
1 Reading with Units (26.195 3 Channel
°C) Number
2 Elapsed Time (17 ms) 4 Alarm
Limit
Threshold
Crossed (0
= No Alarm,
1 = LO, 2 =
HI)
Absolute Format (Default):

1 Reading with Units (26.195 4 Channel
°C) Number
2 Date (November 21, 2004) 5 Alarm
Limit
Threshold
Crossed (0
= No Alarm,
1 = LO, 2 =
HI)
3 Time of Day (3:30:23.000
PM)
The FORMat commands are valid only with the following
Keysight 34970A/34972A plug-in modules, which can be configured to be
part of a scan. The internal DMM must also be installed and enabled.
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34903A 20 Channel Actuator/GP Switch Module
34904A 4 x 8 Two-Wire Matrix Module
34905A 2 GHz Dual 1:4 RF Mux, 50 Ohm Module
34906A 2 GHz Dual 1:4 RF Mux, 75 Ohm Module
34907A Multifunction Module
34908A 40 Channel Single-Ended Multiplexer Module

Command Summary
FORMat:READing:ALARm
FORMat:READing:ALARm?
FORMat:READing:CHANnel
FORMat:READing:CHANnel?
FORMat:READing:TIME
FORMat:READing:TIME?
FORMat:READing:TIME:TYPE
FORMat:READing:TIME:TYPE?
FORMat:READing:UNIT
FORMat:READing:UNIT?

FORMat:READing:ALARm
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
FORMat:READing:ALARm <state>
FORMat:READing:ALARm?

Description
This command disables or enables the inclusion of alarm information
with data retrieved by the READ? command, the FETCh? command, and
other queries of scan results. This command operates in conjunction with
the other FORMat:READing commands (they are not mutually
exclusive). See Format Subsystem Introduction for examples of fully-
formatted results from a scan.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of | Default	Value |
| ---- | ---- | -------- | ------------- |
Values
| <state> | Boolean | {OFF|0|ON|1} | This	is	a |
| ------- | ------- | ------------ | --------- |
required
parameter.
The	factory
reset	value	is
OFF
(disabled).

Remarks
The reading format applies to all readings being retrieved from the
instrument; you cannot set the format on a per-channel basis.
The CONFigure and MEASure? commands automatically disable
the alarm setting.
The alarm setting is stored in volatile memory and will be disabled
(OFF) when power is turned off or after a Factory Reset (*RST
command).

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command enables the inclusion of alarm information.
FORM:READ:ALAR ON
The following query returns the alarm setting.
FORM:READ:ALAR?
Typical Response: 1

See Also
FORMat Subsystem Introduction
FORMat:READing:CHANnel

FORMat:READing:CHANnel
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
FORMat:READing:CHANnel <mode>
FORMat:READing:CHANnel?

Description
This command disables or enables the inclusion of channel number
information with data retrieved by the READ? command, the FETCh?
command, or other queries of scan results. This command operates in
conjunction with the other FORMat:READing commands (they are not
mutually exclusive). See Format Subsystem Introduction for examples of
fully-formatted results from a scan.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of | Default	Value |
| ---- | ---- | -------- | ------------- |
Values
| <mode> | Boolean | {OFF|0|ON|1} | This	is	a |
| ------ | ------- | ------------ | --------- |
required
parameter.
The	factory
default	value
is	OFF
(disabled).

Remarks
The reading format applies to all readings being retrieved from the
instrument; you cannot set the format on a per-channel basis.
The CONFigure and MEASure? commands automatically disable
the channel setting.
The channel setting is stored in volatile memory and will be
disabled (OFF) when power is turned off or after a Factory Reset
(*RST command).

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command enables the inclusion of channel number
information.
FORM:READ:CHAN ON
The following query returns the channel number setting.
FORM:READ:CHAN?
Typical Response: 1

See Also
FORMat Subsystem Introduction
FORMat:READing:ALARm
FORMat:READing:TIME
FORMat:READing:UNIT

FORMat:READing:TIME
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
FORMat:READing:TIME <mode>
FORMat:READing:TIME?

Description
This command disables or enables the inclusion of a time stamp with
data retrieved by the READ? command, the FETCh? command, or other
queries of scan results. This command operates in conjunction with the
other FORMat:READing commands (they are not mutually exclusive).
See Format Subsystem Introduction for examples of fully-formatted
results from a scan.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of | Default	Value |
| ---- | ---- | -------- | ------------- |
Values
| <mode> | Boolean | {OFF|0|ON|1} | This	is	a	required |
| ------ | ------- | ------------ | ------------------ |
parameter.
The	factory
default	value	is
OFF	(disabled).

Remarks
The reading format applies to all readings being retrieved from the
instrument; you cannot set the format on a per-channel basis.
If enabled, the time stamp information is shown either in absolute
time (time of day with date) or relative time (time in seconds since
start of scan) as set by the FORMat:READing:TIME:TYPE
command.
The CONFigure and MEASure? commands automatically disable
the time stamp setting.
The time stamp setting is stored in volatile memory and will be
disabled (OFF) when power is turned off or after a Factory Reset
(*RST command).

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command enables the inclusion of a time stamp.
FORM:READ:TIME ON
The following query returns the time stamp setting.
FORM:READ:TIME?
Typical Response: 1

See Also
FORMat Subsystem Introduction
FORMat:READing:ALARm
FORMat:READing:CHANnel
FORMat:READing:TIME:TYPE
FORMat:READing:UNIT

FORMat:READing:TIME:TYPE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
FORMat:READing:TIME:TYPE <format>
FORMat:READing:TIME:TYPE?

Description
This command selects the time format for timestamps returned when
FORMat:READing:TIME is ON. You can select absolute time (time of
day with date) or relative time (time in seconds since start of scan). This
command operates in conjunction with the other FORMat:READing
commands (they are not mutually exclusive). See Format Subsystem
Introduction for examples of fully-formatted results from a scan.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <format> | Discrete | {ABSolute|RELative} | This	is	a |
| -------- | -------- | ------------------- | --------- |
required
parameter.
The
factory
default	is
RELative.

Remarks
The reading format applies to all readings being retrieved from the
instrument; you cannot set the format on a per-channel basis.
In terms of reading stored data from memory, the relative format is
considerably faster than the absolute format.
The absolute format is based on the instrument's real-time clock
as set by the SYSTem:DATE and SYSTem:TIME commands.
The time format setting is stored in volatile memory and will be
disabled (OFF) when power is turned off or after a Factory Reset
(*RST command).

Return Format
The query returns ABS or REL.

Examples
The following command enables the absolute time format (readings are
stored with time of day and date information).
FORM:READ:TIME:TYPE ABS FORM:READ:TIME ON
The following query returns the time format setting.
FORM:READ:TIME:TYPE?
Typical Response: ABS

See Also
FORMat Subsystem Introduction
FORMat:READing:TIME
SYSTem:DATE
SYSTem:TIME

FORMat:READing:UNIT
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
FORMat:READing:UNIT <mode>
FORMat:READing:UNIT?

Description
This command disables or enables the inclusion of measurement units
(VAC, VDC, OHM, etc.) with data retrieved by the READ? command, the
FETCh? command, or other queries of scan results. This command
operates in conjunction with the other FORMat:READing commands
(they are not mutually exclusive). See Format Subsystem Introduction for
examples of fully-formatted results from a scan.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of | Default	Value |
| ---- | ---- | -------- | ------------- |
Values
| <mode> | Boolean | {OFF|0|ON|1} | This	is	a	required |
| ------ | ------- | ------------ | ------------------ |
parameter.
The	factory
default	value	is
OFF	(disabled).

Remarks
The reading format applies to all readings being retrieved from the
instrument; you cannot set the format on a per-channel basis.
The CONFigure and MEASure? commands automatically disable
the unit setting.
The unit setting is stored in volatile memory and will be disabled
(OFF) when power is turned off or after a Factory Reset (*RST
command).

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command enables the inclusion of measurement units.
FORM:READ:UNIT ON
The following query returns the measurement units setting.
FORM:READ:UNIT?
Typical Response: 1

See Also
FORMat Subsystem Introduction
FORMat:READing:ALARm
FORMat:READing:CHANnel
FORMat:READing:TIME
FORMat:READing:TIME:TYPE

IEEE-488 Common Commands Introduction
Command Summary
*CLS
*ESE
*ESE?
*ESR?
*IDN?
*OPC
*OPC?
*PSC
*PSC?
*RCL
*RST
*SAV
*SRE
*SRE?
*STB?
*TRG
*TST?
*WAI

*CLS
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
*CLS

Description
This command, whose name derives from CLear Status, clears the event
registers in all register groups. It also clears the error queue and the
alarm queue, but it does not clear the enable registers.

Example
The following command clears the event register bits, alarm queue, and
error queue.
*CLS

See Also
IEEE-488 Common Commands Introduction
*ESR?
STATus:OPERation[:EVENt]?
STATus:QUEStionable[:EVENt]?

*ESE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
*ESE <enable_val>
*ESE?

Description
This command enables bits in the enable register for the Standard Event
Register group. The selected bits are then reported to bit 5 of the Status
Byte Register.
For more information on the Status System for the
instrument, see Status System Introduction.

Parameters
| Name         | Type    | Range	of       | Default    |
| ------------ | ------- | -------------- | ---------- |
|              |         | Values         | Value      |
| <enable_val> | Numeric | The	decimal    | This	is	a  |
|              |         | value	equal	to | required   |
|              |         | the	binary-    | parameter. |
weighted	sum
of	the	bits	in	the
register	(see
table	below).

Remarks
The	following	table	lists	the	bit	definitions	for	the	Standard	Event
Register.
| Bit Bit	Name | Decimal | Definition         |
| ------------ | ------- | ------------------ |
| #            | Value   |                    |
| 0 Operation  | 1       | All	commands	prior |
| Complete     |         | to	and	including   |
*OPC	have	been
executed.
| 1 Not	Used    | Not	Used | 0	is	returned.       |
| ------------- | -------- | -------------------- |
| 2 Query	Error | 4        | The	instrument	tried |
to	read	the	output
buffer	but	it	was
empty.	Or,	a	new
command	line	was
received	before	a
previous	query	has
been	read.	Or,	both
the	input	and	output
buffers	are	full.
| 3 Device	Error | 8   | A	device-specific |
| -------------- | --- | ----------------- |
error	has	been
generated.	For	a
complete	listing	of
the	error	messages,
see	Error	Messages.
| 4 Execution | 16  | An	execution	error    |
| ----------- | --- | --------------------- |
| Error       |     | occurred.	These	error |
codes	are	in	the	range
-100	to	-199.
| 5 Command | 32  |     |
| --------- | --- | --- |

Error A command error
occurred. These
error codes are in
the range -200 to
-299.
6 Not Used Not Used 0 is returned.
7 Power On 128 Power has been
turned off and on
since the last time the
event register was
read or cleared.
Use the <enable_val> parameter to specify which bits will be
enabled. The decimal value specified corresponds to the binary-
weighted sum of the bits you wish to enable in the register. For
example, to enable bit 2 (decimal value = 4), bit 3 (decimal value =
8), and bit 7 (decimal value = 128), the corresponding decimal
value would be 140 (4 + 8 + 128).
The *CLS (clear status) command will not clear the enable register
but it does clear all bits in the event register.

Return Format
The query reads the enable register and returns a decimal value that
corresponds to the binary-weighted sum of all bits set in the register. For
example, if bit 3 (decimal value = 8) and bit 7 (decimal value = 128) are
enabled, the query will return "+136".

Examples
The following command enables bit 4 (decimal value = 16) in the enable
register. If an execution error occurs, this condition will be reported to the
Status Byte Register (bit 4 will be set high).
*ESE 16
The following query returns which bits are enabled in the register.
*ESE?
Typical Response: +16

See Also
IEEE-488 Common Commands Introduction
*ESR?

*ESR?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
*ESR?

Description
This command queries the event register for the Standard Event
Register group. This is a read-destructive register, and the bits are
cleared when you read the register.
For more information on the Status System for the
instrument, see Status System Introduction.

Remarks
The	following	table	lists	the	bit	definitions	for	the	Standard	Event
Register.
| Bit Bit	Name | Decimal | Definition         |
| ------------ | ------- | ------------------ |
| #            | Value   |                    |
| 0 Operation  | 1       | All	commands	prior |
| Complete     |         | to	and	including   |
*OPC	have	been
executed.
| 1 Not	Used    | Not	Used | 0	is	returned.       |
| ------------- | -------- | -------------------- |
| 2 Query	Error | 4        | The	instrument	tried |
to	read	the	output
buffer	but	it	was
empty.	Or,	a	new
command	line	was
received	before	a
previous	query	has
been	read.	Or,	both
the	input	and	output
buffers	are	full.
| 3 Device | 8   | A	device-specific |
| -------- | --- | ----------------- |
| Error    |     | error	has	been    |
generated.	For	a
complete	listing	of
the	error	messages,
see	Error	Messages.
| 4 Execution | 16  | An	execution	error |
| ----------- | --- | ------------------ |
| Error       |     | occurred.	These    |
error	codes	are	in
the	range	-100	to
-199.

| 5 Command | 32  | An	command	error |
| --------- | --- | ---------------- |
| Error     |     | occurred.	These  |
error	codes	are	in
the	range	-200	to
-299.
| 6 Not	Used | Not	Used | 0	is	returned. |
| ---------- | -------- | -------------- |
| 7 Power	On | 128      | Power	has	been |
turned	off	and	on
since	the	last	time
the	event	register
was	read	or	cleared.
In	order	to	be	reported	to	the	Status	Register,	the	corresponding
bits	in	the	event	register	must	be	enabled	using	the	*ESE
command.
Once	a	bit	is	set,	it	remains	set	until	cleared	by	reading	the	event
register	or	execution	of	the	*CLS	(clear	status)	command.

Return Format
The query reads the event register and returns a decimal value which
corresponds to the binary-weighted sum of all bits set in the register (see
table above). For example, if bit 2 (decimal value = 4) and bit 4 (decimal
value = 16) are set (and the corresponding bits are enabled), this
command will return +20.

Example
The following query reads the event register (bits 3 and 4 are set).
*ESR?
Typical Response: +24

See Also
IEEE-488 Common Commands Introduction
*ESE
*CLS

*IDN?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
*IDN?

Description
This query reads the instrument's identification string, which includes the
manufacturer name, the model name and firmware version information.

Return Format
For the 34970A, the query returns a string with the following format:
HEWLETT-PACKARD,34970A,0,XX-Y-Z
where:
XX Measurement processor firmware
version
Y I/O processor firmware version
Z Front panel processor firmware
version
For the 34972A, the query returns a string with the following format:
Keysight Technologies,34972A,<serial#>,i.ii-o.oo-fp-fpga
where:
i.ii I/O processor firmware version
o.oo Measurement processor firmware
version
fp Front panel processor firmware
version

fpga FPGA version

Example
The following query returns the instrument's identification string for a
34972A.
*IDN?
Typical Response: Keysight Technologies,34972A,MY12345678,1.01-
1.00-01-0002
The following query returns the instrument's identification string for a
34970A.
*IDN?
Typical Response: HEWLETT-PACKARD,34970A,0,13-2-2

See Also
IEEE-488 Common Commands Introduction

*OPC
*OPC?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
*OPC
*OPC?

Description
The command form starts the OPC state engine and returns. At the end
of the current scan, bit 0 of the enable register for the Standard Event
Register will be set to 1. The query form returns 1 to the output buffer at
the completion of the current operation.
For more information on the Status System for the
instrument, see Status System Introduction.
For more information on the Standard Event Register,
see *ESE.

Remarks
This command enables you to synchronize your application with
the instrument.
You can configure SRQ interrupts to notify user applications.
Note the difference between the *OPC command and the *OPC?
query. The *OPC? query sets the output buffer to 1 at the
completion of the current operation.

Examples
The following command returns immediately and causes the status
system to set the "Operation Complete" bit at the end of the current
scan.
*OPC
The following query sends "1" to the output buffer when the current
operation completes.
*OPC?
Typical Response: +1

See Also
IEEE-488 Common Commands Introduction
*ESE

*PSC
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
*PSC <state>
*PSC?

Description
Power-On Status Clear. This command enables or disables the clearing
of certain enable registers at power on. With *PSC 0 specified, these
registers are not cleared at power on. With *PSC 1 specified, these
registers are cleared at power on. The following registers are affected:
Register Command
Name
Questionable STATus:QUEStionable:ENABle
Data
Register
Standard STATus:OPERation:ENABle
Operation
Register
Alarm STATus:ALARm:ENABle
Register
Status Byte *SRE (Service Request Enable)
Register
Standard *ESE (Event Status Enable)
Event
Register
The *PSC command does not affect the clearing of the
condition or event registers, just the enable registers. For
more information on the Status System for the instrument,
see Status System Introduction.

Parameters
| Name    | Type    | Range	of     | Default |
| ------- | ------- | ------------ | ------- |
|         |         | Values       | Value   |
| <state> | Boolean | {OFF|0|ON|1} | ON      |

Return Format
The query returns 0 (do not clear at power on) or 1 (clear at power on).

Examples
The following command disables the power-on clearing of the affected
registers.
*PSC 0
The following query returns the power-on status clear setting.
*PSC?
Typical Response: 0

See Also
*SRE
*STB?

*SAV
*RCL
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
*SAV {0|1|2|3|4|5}
*RCL {0|1|2|3|4|5}

Description
These commands store and recall instrument states into the specified
storage location. The *SAV command saves the current instrument state
and overwrites any state previously stored in the same location is
overwritten (no error is generated).

Remarks
The instrument has six storage locations in non-volatile memory to
store instrument states. You can store the instrument state in
location 0, 1, 2, 3, 4, or 5, but you can only recall a state from a
location that contains a previously stored state.
LAN I/O configuration is not stored by a *SAV operation or recalled
by a *RCL. Only instrument configuration is recalled.
When shipped from the factory, all six storage locations are empty.
State 0 is overwritten at power down.
A Factory Reset (*RST command) does not affect the
configurations stored in memory. Once a state is stored, it remains
until it is overwritten.

Example
The following command stores the current instrument state in location 1.
*SAV 1

See Also
IEEE-488 Common Commands Introduction

*RST
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
*RST

Description
This command resets the instrument to the Factory configuration. See
Factory Reset State for a complete listing of the instrument's Factory
configuration.

Remarks
This command does not affect any previously-stored instrument
states (see *SAV command).
This command does not affect I/O settings, such as IP address.
The value of CALibration:SECure:STATe is not affected by *RST.

Example
The following command resets the instrument.
*RST

See Also
IEEE-488 Common Commands Introduction

*SRE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
*SRE <enable_val>
*SRE?

Description
This command enables bits in the enable register for the Status Byte
Register. Once enabled, the corresponding bits may generate a Request
for Service (RQS) in the Status Byte. This RQS event may generate a
"call back" to your application as a type of asynchronous interrupt.
For more information on the Status System for the
instrument, see Status System Introduction.

Parameters
| Name         | Type    | Range	of       | Default    |
| ------------ | ------- | -------------- | ---------- |
|              |         | Values         | Value      |
| <enable_val> | Numeric | A	decimal      | This	is	a  |
|              |         | value	which    | required   |
|              |         | corresponds	to | parameter. |
the	binary-
weighted	sum
of	the	bits	in
the	register
(see	table
below).

Remarks
The	following	table	lists	the	bit	definitions	for	the	Status	Byte
Register.
| Bit Bit	Name | Decimal                           | Definition |
| ------------ | --------------------------------- | ---------- |
| #            | Value                             |            |
| 0 Not	Used   | 1 Always	zero.                    |            |
| 1 Alarm      | 2 One	or	more	bits	are	set	in	the |            |
Summary Alarm	Register	(bits	must	be
enabled).
| 2 Error	Queue | 4 One	or	more	errors	have	been |     |
| ------------- | ------------------------------ | --- |
stored	in	the	Error	Queue.	Use
the	SYSTem:ERRor?	query	to
read	and	delete	errors.
| 3 Questionable | 8 One	or	more	bits	are	set	in	the |     |
| -------------- | --------------------------------- | --- |
Data Questionable	Data	Register	(bits
Summary must	be	enabled,	see
STATus:QUEStionable:ENABle
command).
| 4 Message | 16 Data	is	available	in	the |     |
| --------- | --------------------------- | --- |
Available instrument's	output	buffer.
| 5 Standard | 32 One	or	more	bits	are	set	in	the |     |
| ---------- | ---------------------------------- | --- |
Event Standard	Event	Register	(bits
Summary must	be	enabled,	see	*ESE
command).
| 6 Master | 64 One	or	more	bits	are	set	in	the |     |
| -------- | ---------------------------------- | --- |
Summary Status	Byte	Register	and	may
generate	a	Request	for	Service
(RQS).	Bits	must	be	enabled
using	the	*SRE	command.
| 7 Standard | 128 One	or	more	bits	are	set	in	the |     |
| ---------- | ----------------------------------- | --- |

Operation Standard Operation Register
Summary (bits must be enabled, see
STATus:OPERation:ENABle
command).
Use the <enable_val> parameter to specify which bits will be
enabled. The decimal value specified corresponds to the binary-
weighted sum of the bits you wish to enable in the register. For
example, to enable bit 3 (decimal value = 8) and bit 5 (decimal
value = 32), the corresponding decimal value would be 40 (8 +
32).
The *CLS (clear status) command will not clear the enable register
but it does clear all bits in the event register.
A *CLS or *RST command does not clear the bits in the Status
Byte enable register.
Be sure to send the decimal value of the bit and not the bit
number. For example, to enable bit 4, send *SRE 16, not *SRE 4.

Return Format
The query reads the enable register and returns a decimal value that
corresponds to the binary-weighted sum of all bits set in the register. For
example, if bit 3 (decimal value = 8) and bit 5 (decimal value = 32) are
enabled, the query will return +40.

Examples
The following command enables bit 4 (decimal value = 16) in the enable
register.
*SRE 16
The following query returns which bits are enabled in the register.
*SRE?
Typical Response: +16

See Also
IEEE-488 Common Commands Introduction
*STB?

*STB?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
*STB?

Description
This command queries the condition register for the Status Byte Register
group. This is a read-only register and the bits are not cleared when you
read the register.
For more information on the Status System for the
instrument, see Status System Introduction.

Remarks
The	following	table	lists	the	bit	definitions	for	the	Status	Byte
Register.
| Bit Bit	Name | Decimal                                 | Definition |
| ------------ | --------------------------------------- | ---------- |
| #            | Value                                   |            |
| 0 Not	Used   | 1 Always	zero.                          |            |
| 1 Alarm      | 2 One	or	more	bits	are	set	in	the	Alarm |            |
Summary Register	(bits	must	be	enabled).
| 2 Error	Queue | 4 One	or	more	errors	have	been	stored	in |     |
| ------------- | ---------------------------------------- | --- |
the	Error	Queue.	Use	the
SYSTem:ERRor?	query	to	read	and
delete	errors.
| 3 Questionable | 8 One	or	more	bits	are	set	in	the |     |
| -------------- | --------------------------------- | --- |
Data Questionable	Data	Register	(bits	must
Summary be	enabled,	see
STATus:QUEStionable:ENABle
command).
| 4 Message | 16 Data	is	available	in	the	instrument's |     |
| --------- | ---------------------------------------- | --- |
Available output	buffer.
| 5 Standard | 32 One	or	more	bits	are	set	in	the	Standard |     |
| ---------- | ------------------------------------------- | --- |
Event Event	Register	(bits	must	be	enabled,
Summary see	*ESE	command).
| 6 Master | X One	or	more	bits	are	set	in	the	Status |     |
| -------- | ---------------------------------------- | --- |
Summary Byte	Register	and	may	generate	a
Request	for	Service	(RQS).	Bits	must
be	enabled	using	the	*SRE	command.
| 7 Standard | 128 One	or	more	bits	are	set	in	the	Standard |     |
| ---------- | -------------------------------------------- | --- |
Operation Operation	Register	(bits	must	be
Summary enabled,	see
STATus:OPERation:ENABle

command).
This query returns the same results as a Serial Poll but the
"Master Summary" bit (bit 6) is not cleared if a Serial Poll has
occurred.
Unlike how a reset clears the condition register, a factory reset
(*RST command) does not clear the Status Byte Register.

Return Format
The query reads the condition register and returns a decimal value that
corresponds to the binary-weighted sum of all bits set in the register (see
table above). For example, if bit 3 (decimal value = 8) and bit 5 (decimal
value = 32) are set (and the corresponding bits are enabled), this
command will return "+40".

Example
The following query reads the condition register (bits 3 and 5 are set).
*STB?
Typical Response: +40

See Also
IEEE-488 Common Commands Introduction
*SRE

*TRG
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
*TRG

Description
This command sends a software trigger to the instrument when the
instrument is configured for TRIGger:SOURce BUS.

Remarks
The software trigger operation that this command executes is
accepted by the instrument only when the instrument is acquiring
data (executing INITiate).
After setting the trigger source, you must place the instrument in
the wait-for-trigger state using the INITiate command. Once you
have sent the INITiate command, the instrument will buffer one
software trigger to be applied at the next wait-for-trigger state, so it
is not necessary to verify that the instrument is precisely in the
wait-for-trigger state.
The *TRG command does not work with the READ? command.

Example
The following commands trigger the instrument.
TRIG:SOUR BUS
INIT
*TRG

See Also
IEEE-488 Common Commands Introduction
INITiate

*TST?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
*TST?

Description
This command performs a complete self-test of the instrument and
returns a pass/fail indication. The self-test runs a series of tests and will
take approximately 45 seconds to complete. If all tests pass, you can
have a high confidence that the instrument is operational.

Remarks
When sending the *TST? query, you may need to increase the
timeout period for your IO Library read response time to allow the
command to complete without causing a timeout error.
If one or more tests fail, +1 is returned and one or more errors are
stored in the error queue. For a complete listing of the error
messages related to self-test failures, see Error Messages.
If one or more tests fail, see the Keysight 34970A/34972A Service
Guide for instructions on obtaining service.
Upon completion, *TST? restores the instrument to its factory
reset state.

Return Format
The query returns +0 (all tests passed) or +1 (one or more tests failed).
For details on possible error returned if tests fail, see Error Messages.

Example
The following command performs a self-test and returns a pass/fail
indication. In this case, there are no failures.
*TST?
Typical Response: +0

See Also
IEEE-488 Common Commands Introduction

*WAI
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
*WAI

Description
This command waits for all pending operations to complete before
executing any additional commands over the interface.

Remarks
Function and range changes are considered pending operations.
Therefore, *WAI will wait for these changes to complete.
Because this command stops the command parser from operating,
it is better to use *OPC? for synchronization purposes.

Examples
The following command waits until all pending operations complete.
INIT; *WAI; :ROUT:CLOS(@101) ! Ensures that the
scan started by the INIT finishes
! before the
ROUT:CLOS command is executed.

See Also
IEEE-488 Common Commands Introduction
*OPC

INSTrument Subsystem Introduction
Command Summary
INSTrument:DMM
INSTrument:DMM?
INSTrument:DMM:INSTalled?

INSTrument:DMM
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
INSTrument:DMM <state>
INSTrument:DMM?

Description
This command disables or enables the internal DMM. When you change
the state of the internal DMM, the instrument issues a Factory Reset
(*RST command).

Parameters
| Name    | Type    | Range	of     | Default   |
| ------- | ------- | ------------ | --------- |
|         |         | Values       | Value     |
| <state> | Boolean | {OFF|0|ON|1} | This	is	a |
required
parameter.

Return Format
The query returns the state of the internal DMM as 0 (disabled) or 1
(enabled).

Examples
The following command enables the internal DMM.
INST:DMM ON
The following query returns the state of the DMM, which is ON in this
case.
INST:DMM?
Typical Response: 1

See Also
INSTrument Subsystem Introduction

INSTrument:DMM:INSTalled?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
INSTrument:DMM:INSTalled?

Description
This query determines whether the internal DMM is installed in the
mainframe.

Remarks
The internal DMM is an optional assembly for the
Keysight 34970A/34972A.

Return Format
The query returns 0 (not installed) or 1 (installed).

Example
The following command determines that the internal DMM is present.
INST:DMM:INST?
Typical Response: 1

See Also
INSTrument Subsystem Introduction
INSTrument:DMM

LXI Subsystem Introduction
The following commands support LAN eXtensions for Instrumentation
(LXI) functionality.

Command Summary
LXI:IDENtify:STATe
LXI:IDENtify:STATe?
LXI:RESet
LXI:RESTart

LXI:IDENtify[:STATe]
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
LXI:IDENtify[:STATE] <state>
LXI:IDENtify[:STATE]?

Description
This command turns the LXI Identify Indicator on the front panel display
on or off.

Parameters
| Name    | Type    | Range	of	Values | Default	Value                 |
| ------- | ------- | --------------- | ----------------------------- |
| <state> | Boolean | {OFF|0|ON|1}    | This	is	a	required	parameter. |

Remarks
The LXI Identify Indicator helps you identify which LXI device is
associated with the LAN address you are using.
The instrument turns off the LXI Identify Indicator after a Factory
Reset (*RST command).
You can press the LOCAL key to turn off the LXI Identify Indicator.

Return Format
The query returns the current LXI Identify Indicator state: 0 (OFF) or 1
(ON).

Examples
The following command turns on the LXI Identify Indicator.
LXI:IDEN ON
The following query returns the state of the LXI Identify Indicator.
LXI:IDEN?
Typical Response: 1

See Also
LXI Subsystem Introduction

LXI:RESet
Syntax | Description | Parameters | Remarks | Return Format | Example
This functionality is available on the 34972A
only.

Syntax
LXI:RESet

Description
This command resets the instrument's LAN settings to their default
values.

Example
The following command resets the LAN settings.
LXI:RES

See Also
LXI Subsystem Introduction

LXI:RESTart
Syntax | Description | Parameters | Remarks | Return Format | Example
This functionality is available on the 34972A
only.

Syntax
LXI:RESTart

Description
This command restarts the LAN with the current parameters.

Example
The following command restarts the LAN interface.
LXI:REST

See Also
LXI Subsystem Introduction

MEASure Subsystem Introduction
If you specify a <ch_list> with one of these commands, that <ch_list>
overwrites the current scan list.

Command Summary
MEASure:CURRent:AC?
MEASure:CURRent:DC?
MEASure:DIGital:BYTE?
MEASure:FREQuency?
MEASure:FRESistance?
MEASure:PERiod?
MEASure:RESistance?
MEASure:TEMPerature?
MEASure:TOTalize?
MEASure:VOLTage:AC?
MEASure:VOLTage:DC?

MEASure:CURRent:AC?
MEASure:CURRent:DC?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
MEASure:CURRent:AC? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:CURRent:DC? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)

Description
These commands are equivalent to CONFigure:CURRent:AC or
CONFigure:CURRent:DC followed by a READ?.

See Also
MEASure Subsystem Introduction
CONFigure:CURRent:AC
CONFigure:CURRent:DC
READ?

MEASure:DIGital:BYTE?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
MEASure:DIGital:BYTE? (@<scan_list>)

Description
This command is equivalent to CONFigure:DIGital:BYTE followed by a
READ?.

See Also
MEASure Subsystem Introduction
CONFigure:DIGital:BYTE
READ?

MEASure:FREQuency?
MEASure:PERiod?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
MEASure:FREQuency? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:PERiod? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)

Description
These commands are equivalent to CONFigure:FREQuency or
CONFigure:PERiod followed by a READ?.

See Also
MEASure Subsystem Introduction
CONFigure:FREQuency
CONFigure:PERiod
[SENSe:]FREQuency:RANGe:LOWer
[SENSe:]FREQuency:VOLTage:RANGe
[SENSe:]PERiod:VOLTage:RANGe
READ?

MEASure:RESistance?
MEASure:FRESistance?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
MEASure:RESistance? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:FRESistance? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)

Description
These commands are equivalent to CONFigure:RESistance or
CONFigure:FRESistance followed by a READ?.

See Also
MEASure Subsystem Introduction
CONFigure:RESistance
[SENSe:]RESistance:OCOMpensated
CONFigure:FRESistance
[SENSe:]FRESistance:OCOMpensated
READ?

MEASure:TEMPerature?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
MEASure:TEMPerature? {<probe_type>|DEF},{<type>|DEF}[,1[,
{<resolution>|MIN|MAX|DEF}]] ,(@<scan_list>)

Description
This command is equivalent to CONFigure:TEMPerature followed by a
READ?.

See Also
MEASure Subsystem Introduction
CONFigure:TEMPerature
READ?

MEASure:TOTalize?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
MEASure:TOTalize? <mode>,(@<scan_list>)

Description
This command is equivalent to CONFigure:TOTalize followed by a
READ?.

See Also
MEASure Subsystem Introduction
CONFigure:TOTalize
READ?

MEASure:VOLTage:AC?
MEASure:VOLTage:DC?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
MEASure:VOLTage:AC? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:VOLTage:DC? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)

Description
These commands are equivalent to CONFigure:VOLTage:AC or
CONFigure:VOLTage:DC followed by a READ?.

See Also
MEASure Subsystem Introduction
CONFigure[:VOLTage][:DC]
CONFigure[:VOLTage]:AC
ROUTe:CHANnel:DELay
ROUTe:CHANnel:DELay:AUTO
[SENSe:]VOLTage:AC:BANDwidth
CONFigure:VOLTage:AC
CONFigure:VOLTage:DC
READ?

MEMory Subsystem Introduction
Command Summary
MEMory:NSTates?
MEMory:STATe:DELete
MEMory:STATe:NAME
MEMory:STATe:NAME?
MEMory:STATe:RECall:AUTO
MEMory:STATe:RECall:AUTO?
MEMory:STATe:VALid?

MEMory:NSTates?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
MEMory:NSTates?

Description
This query returns the total number of memory locations available for
state storage. For the 34970A/34972A, this command always returns the
number 6.

Remarks
Location 0 is included, but it is reserved for power-down state
storage.

Return Format
The query returns the number +6.

Example
The following query returns the number of states.
MEMory:NSTates?
Typical Response: +6

See Also
MEMory Subsystem Introduction

MEMory:STATe:DELete
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
MEMory:STATe:DELete <location>

Description
This command deletes the contents of the specified storage location.

Parameters
| Name | Type | Range | Default |
| ---- | ---- | ----- | ------- |
|      |      | of    | Value   |
Values
| <location> | Numeric |         | This	is	a  |
| ---------- | ------- | ------- | ---------- |
|            |         | An      | required   |
|            |         | integer | parameter. |
from	0
to	5

Remarks
Note that you cannot recall the instrument state from a storage
location that was deleted. An error is generated if you attempt to
recall a deleted state (+291,"Not able to recall state: it is empty").

Example
The following command deletes the contents of storage location 1.
MEM:STAT:DEL 1

See Also
MEASure Subsystem Introduction
*SAV
*RCL

MEMory:STATe:NAME
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
MEMory:STATe:NAME <location>[,<name>]
MEMory:STATe:NAME? <location>

Description
This command assigns a name to the specified storage location. You can
name a location from the front panel or over the remote interface but you
can recall a named state only from the front panel. From the remote
interface, you can only recall a stored state using the *RCL command
with a number (0 through 5).

Parameters
| Name | Type | Range	of | Default	Value |
| ---- | ---- | -------- | ------------- |
Values
| <location> | Numeric  | An	integer  | This	is	a       |
| ---------- | -------- | ----------- | --------------- |
|            |          | from	0	to   | required        |
|            |          | 5           | parameter.      |
| <name>     | Unquoted | A           | If	omitted,	the |
|            | ASCII    | unquoted    | default	name	is |
|            | String   | string	of   | used	for	the    |
|            |          | up	to	12    | specified       |
|            |          | characters. | storage         |
|            |          | The	first   | location.       |
character
must	be	a
letter	(A-
Z),	but	the
remaining
11
characters
can	be
letters,
numbers
(0-9),	or
the
underscore
character
("_").
Blank
spaces	are
not
allowed.

Remarks
When shipped from the factory, default names are assigned to
storage locations 1 through 5. The default names are "STATE1",
"STATE2", and so on.
If you omit the <name> parameter, the default name is assigned to
the specified storage location. This provides an easy way to reset
the associated name to its factory default; however, the stored
state is not deleted.
The instrument generates an error if you specify a name with more
than 12 characters.
Deleting the contents of a storage location (see
MEMory:STATe:DELete command) will reset the associated name
to its factory default ("STATE1", "STATE2", etc.).
A Factory Reset (*RST command) does not affect the
configurations stored in memory. Once a state is stored, it remains
until it is overwritten or specifically deleted.

Return Format
The query reads the name assigned to the specified storage location and
returns a quoted ASCII string. If the specified location has no custom
assigned, the default name is returned ("STATE1", "STATE2", etc.).

Examples
The following command assigns the name TEST_RACK_1 to storage
location 1.
MEM:STAT:NAME 1,TEST_RACK_1
The following query returns the name assigned to storage location 1.
MEM:STAT:NAME? 1
Typical Response: "TEST_RACK_1"

See Also
MEMory Subsystem Introduction
*SAV
*RCL

MEMory:STATe:RECall:AUTO
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
MEMory:STATe:RECall:AUTO <mode>
MEMory:STATe:RECall:AUTO?

Description
This command enables or disables (default) the automatic recall of the
power-down state (state 0) when power is turned on. Select "ON" to
automatically recall the power-down state. Select "OFF" to issue a
Factory Reset (*RST) when power is turned on (in this mode, the power-
down state is not automatically recalled).

Parameters
| Name   | Type    | Range	of     | Default   |
| ------ | ------- | ------------ | --------- |
|        |         | Values       | Value     |
| <mode> | Boolean | {OFF|0|ON|1} | This	is	a |
required
parameter.

Remarks
When the instrument is shipped from the factory, the automatic
recall mode is disabled.
State 0 gets stored every time the power is turned off.

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command enables the automatic recall mode.
MEM:STAT:REC:AUTO ON
The following query returns the automatic recall setting.
MEM:STAT:REC:AUTO?
Typical Response: 1

See Also
MEMory Subsystem Introduction
*SAV

MEMory:STATe:VALid?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
MEMory:STATe:VALid? <location>

Description
This command queries the specified storage location to determine
whether a valid state is currently stored in this location. During the
validation process, the instrument verifies that the location is not empty.
You can use this command before sending the *RCL command to
determine whether a state has been previously stored in this location.

Parameters
| Name       | Type    | Range	of | Default   |
| ---------- | ------- | -------- | --------- |
|            |         | Values   | Value     |
| <location> | Numeric |          | This	is	a |
An
required
|     |     | integer | parameter. |
| --- | --- | ------- | ---------- |
from	0	to
5

Remarks
This command does not guarantee that no errors will be generated
when a stored state is recalled using the *RCL command. Even if
this command determines that the specified storage location is
valid, individual modules may still be in states that will generate an
error.

Return Format
The query returns 0 if no state has been stored in the specified location
or if it has been deleted. It returns 1 if a valid state is stored in the
specified location.

Example
The following query returns a 0, indicating that no valid state is currently
stored in location 3.
MEM:STAT:VAL? 3
Typical Response: 0

See Also
MEMory Subsystem Introduction

MMEMory Subsystem Introduction
This functionality is available on the 34972A
only.

Command Summary
MMEMory:EXPort?
MMEMory:FORMat:READing:CSEParator
MMEMory:FORMat:READing:CSEParator?
MMEMory:FORMat:READing:RLIMit
MMEMory:FORMat:READing:RLIMit?
MMEMory:IMPort:CATalog?
MMEMory:IMPort:CONFig?
MMEMory:LOG[:ENABle]
MMEMory:LOG[:ENABle]?

MMEMory:EXPort?
Syntax | Description | Parameters | Remarks | Return Format | Example
This functionality is available on the 34972A
only.

Syntax
MMEMory:EXPort?

Description
This query exports the current contents of reading memory, along with
the instrument configuration, to the default directory on the USB drive:
/34972A/data/<SN>/yyyymmdd_hhmmssmmm
Note than <SN> is the instrument's serial number, yyyymmdd indicates
the current date, and hhmmssmmm indicates the current time in 24-hour
clock format, down to the millisecond.
It waits until the export is complete and returns 0 (no errors) or 1 (export
had errors).

Remarks
A directory named
/34972A/data/MY12345678/20100120_130542169 would indicate
data taken from instrument MY12345678 at the time of 42.169
seconds after 1:05 pm on January 20, 2010.
You can control the field delimiter in the exported files with
MMEMory:FORMat:READing:CSEParator.
Exporting the contents of reading memory can be a lengthy
operation, depending on the number of readings in memory.
For typical USB drives, there is a file system limit of 999 files and
folders per directory. If you receive error message number 410,
"Not enough disk space" while exporting data, check to ensure
that you have not hit the limit of 999 timestamped folders for your
instrument. You may receive error 410 even if additional space is
available on the drive.

Return Format
The query returns 0 (no errors) or 1 (export had errors) when the file
export is complete. If the query returns a 1, use the SYSTem:ERRor?
command to read the errors.

Example
The following query exports the current contents of reading memory,
along with the instrument configuration, to the USB drive.
MMEMory:EXPort?
Typical response: 0

See Also
MMEMory Subsystem Introduction
MMEMory:FORMat:READing:RLIMit
MMEMory:FORMat:READing:CSEParator

MMEMory:FORMat:READing:CSEParator
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
MMEMory:FORMat:READing:CSEParator <column_separator>
MMEMory:FORMat:READing:CSEParator?

Description
This command allows you to specify the character used to separate the
columns in the output data on the USB drive. This enables you to make
the file conform with the application software that you will use for viewing
the file.

Parameters
Name Type Range of Values Default
Value
<column_separator > Discrete This is a
{TAB|COMMa|SEMicolon} required
parameter.
The
factory
default is
COMMa.

Remarks
When the instrument is shipped from the factory, the default state
for <column_separator> is COMMa.
The value of the <state> will be saved in non-volatile memory on
the instrument and will not be affected by *RST or
SYSTem:PRESet.

Return Format
The query returns TAB, COMM or SEM to indicate the value of the
<column_separator>.

Examples
The following command specifies that tabs should be used to separate
the columns in the output data on the USB drive.
MMEMory:FORMat:READing:CSEParator TAB
The following query indicates the character used to separate columns. In
this case, it is tabs.
MMEMory:FORMat:READing:CSEParator?
Typical Response: TAB

See Also
MMEMory Subsystem Introduction

MMEMory:FORMat:READing:RLIMit
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
MMEMory:FORMat:READing:RLIMit <row_limit>
MMEMory:FORMat:READing:RLIMit?

Description
This command allows you to specify whether the maximum number of
sweeps that can be logged to a single USB data file should be limited to
16
one less than 64K (2 - 1 = 65,535). If <row_limit> is ON, sweeps are
stored in files named dat00001.csv, dat00002.csv, dat00003.csv, and so
on, with 65,535 sweeps per file. If <row_limit> is OFF, data logged for the
scan is stored in a single file named dat00001.csv, which is limited by
both the space available on the USB drive and how the drive is
32
formatted, up to a maximum of 2 sweeps (roughly 4.3 billion).

Parameters
| Name        | Type    | Range	of     | Default   |
| ----------- | ------- | ------------ | --------- |
|             |         | Values       | Value     |
| <row_limit> | Boolean | {OFF|0|ON|1} | This	is	a |
required
parameter.
The
factory
default	is
ON.

Remarks
This feature enables you to accommodate certain versions of
common spreadsheet, database and data analysis programs that
have limitations of 64K rows per file.
When the instrument is shipped from the factory, the default state
for <row_limit> is ON.
The value of the <row_limit> will be saved in non-volatile memory
on the instrument and will not be affected by *RST or
SYSTem:PRESet.

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command turns the row limit feature on, causing USB data
files to be split at the 64K - 1 boundary.
MMEMory:FORMat:READing:RLIMit ON
The following query indicates whether the row limit feature is on. In this
case, it is OFF.
MMEMory:FORMat:READing:RLIMit?
Typical Response: 0

See Also
MMEMory Subsystem Introduction
MMEMory:LOG[:ENABle]
MMEMory:FORMat:READing:CSEParator

MMEMory:IMPort:CATalog?
Syntax | Description | Parameters | Remarks | Return Format | Example
This functionality is available on the 34972A
only.

Syntax
MMEMory:IMPort:CATalog?

Description
This query returns a catalog listing all of the Keysight BenchLink
DataLogger configuration (BLCFG) files in the root directory of the
USB drive.

Remarks
If the USB drive is not inserted or contains no files, the query
returns an empty string: "".
This command will only recognize files in the root directory of the
USB drive with a .BLCFG extension.
The command will recognize up to 50 BLCFG files in the root
directory. If more than 50 files are found in the drive's root
directory, the system will recognize only the 50 with the most
recent time stamps.

Return Format
This query returns the catalog as a list of quoted file names, separated
by commas:
"<file_name1>","<file_name2>","<file_name3>", etc.
Note that the file names will include the .BLCFG extension.

Example
The following query returns a list of all BLCFG files in the root directory
of the USB drive. In this case, there are two files.
MMEM:IMP:CAT?
Typical Response: "MyConfig1.BLCFG","PrevConfig.BLCFG"

See Also
MMEMory Subsystem Introduction

MMEMory:IMPort:CONFig?
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
MMEMory:IMPort:CONFig? "<configuration_file>"

Description
This query imports an Keysight BenchLink Data Logger configuration
(BLCFG) file and attempts to configure the instrument according to the
contents of the BLCFG file. It waits until the import is complete and
returns 0 (no errors) or 1 (import had errors).

Parameters
| Name                 | Type     | Range	of | Default   |
| -------------------- | -------- | -------- | --------- |
|                      |          | Values   | Value     |
| <configuration_file> | Filename |          | This	is	a |
Any	file
required
|     |     | name, | parameter. |
| --- | --- | ----- | ---------- |
always
with	a
.BLCFG
extension.

Remarks
The configuration file must reside in the root directory of the USB
drive; hence no path is included in the specification of the "
<configuration_file>."
Only the 50 most recent BLCFG files will be accessible. Files with
names longer than 40 characters will not be accessible.
Possible errors include a card set mismatch between the
instrument and the BLCFG file, or a corrupt file. You should
address errors by diagnosing your BLCFG files with the Keysight
BenchLink Data Logger tool.
Import operations can take several seconds, and the "Busy" status
system bit (bit 14) is asserted during this time. Because this is a
query, no more commands will be processed on the I/O port from
which it was sent until the query completes and returns a 0 or 1.

Return Format
The query returns 0 (no errors) or 1 (import had errors) when the file
import is complete. If the query returns a 1, use the SYSTem:ERRor?
command to read the errors.

Examples
The following query performs the import and then returns a 0 or 1. In this
case, it returns a 1, indicating that the file import had one or more errors.
MMEMory:IMPort:CONFig? "My34972ASetup.BLCFG"
Typical response: 0

See Also
MMEMory Subsystem Introduction

MMEMory:LOG[:ENABle]
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
MMEMory:LOG[:ENABle] <state>
MMEMory:LOG[:ENABle]?

Description
This command allows you to specify whether scanned readings are
logged to the USB drive as they are taken.

Parameters
| Name    | Type    | Range	of     | Default   |
| ------- | ------- | ------------ | --------- |
|         |         | Values       | Value     |
| <state> | Boolean | {OFF|0|ON|1} | This	is	a |
required
parameter.
The	factory
default	state
is	OFF.

Remarks
The value of the <state> will be saved in non-volatile memory on
the instrument and will not be affected by *RST or
SYSTem:PRESet.
For short scans, a READ? or MEASURE? query may take a bit of
extra time to complete if you are also logging to USB.
If you remove the USB drive during logging, logging will stop but
the scan will continue. If you re-attach the USB drive, it will not
cause logging to resume unless you follow the five-step procedure
shown below. Otherwise, logging will resume at the next INITiate.
To replace a USB stick on a system actively logging data to USB:
1. Press the SCAN button for several seconds until the scan stops.
2. Wait until the front panel indicates that the box is again idle. It can
take some time after the scan has been interrupted, for logging to
the USB drive to complete.
3. Once the instrument is idle, remove the USB drive.
4. After the old stick is removed, wait 5 seconds before inserting the
new USB drive.
5. Press the SCAN button again to restart scanning and logging to the
new USB drive.
For typical USB drives, there is a file system limit of 999 files and
folders per directory. If you receive error message number 410,
"Not enough disk space" while logging data, check to ensure that
you have not hit the limit of 999 timestamped folders for your
instrument. You may receive error 410 even if additional space is
available on the drive.

1.

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command specifies that scanned readings are to be
logged to the USB drive as they are taken. Data will also simultaneously
be written to reading memory. To scan data into reading memory without
logging it on the USB drive, you would use MMEM:LOG OFF.
MMEMory:LOG ON
The following query indicates whether scanned readings are to be
logged to the USB drive. In this case, the returned value of 1 indicates
that logging to the USB drive is ON (enabled).
MMEMory:LOG?
Typical Response: 1

See Also
MMEMory Subsystem Introduction

OUTPut Subsystem Introduction
Command Summary
OUTPut:ALARm:CLEar:ALL
OUTPut:ALARm:MODE
OUTPut:ALARm:MODE?
OUTPut:ALARm:SLOPe
OUTPut:ALARm:SLOPe?
OUTPut:ALARm{1|2|3|4}:CLEar
OUTPut:ALARm{1|2|3|4}:SOURce
OUTPut:ALARm{1|2|3|4}:SOURce?

OUTPut:ALARm{1|2|3|4}:CLEar
OUTPut:ALARm:CLEar:ALL
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
OUTPut:ALARm{1|2|3|4}:CLEar
OUTPut:ALARm:CLEar:ALL

Description
The OUTPut:ALARm{1|2|3|4}:CLEar command clears the specified
alarm output line. The OUTPut:ALARm:CLEar:ALL command clears all
four alarm output lines.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input only)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
You can manually clear the output lines at any time (even during a
scan) and the alarm data in memory is not cleared (however, data
is cleared when you initiate a new scan). The alarm outputs are
also cleared when you initiate a new scan.
A Factory Reset (*RST command) clears all four alarm outputs but
does not clear the alarm queue in either configuration.

Examples
The following command clears alarm output line 2.
OUTP:ALAR2:CLE
The following command clears all four alarm output lines.
OUTP:ALAR:CLE:ALL

See Also
OUTPut Subsystem Introduction
OUTPut:ALARm:MODE
OUTPut:ALARm:SLOPe
OUTPut:ALARm{1|2|3|4}:SOURce

OUTPut:ALARm:MODE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
OUTPut:ALARm:MODE <mode>
OUTPut:ALARm:MODE?

Description
This command selects the configuration of the four TTL alarm output
lines (the selected configuration applies to all four alarm output lines).
The four alarm outputs are available from the rear-panel Alarm Output
connector.
Latch Mode: In this mode (default), the corresponding output line is
latched true when the first alarm occurs and remains asserted until you
clear it by initiating a new scan or cycling power. You can manually clear
the output lines at any time (even during a scan) and the alarm data in
memory is not cleared (however, data is cleared when you initiate a new
scan).
Track Mode: In this mode, the corresponding output line is asserted only
while a channel's reading crosses a limit and subsequent readings
remain outside the limit. When a reading returns to within limits, the
output line is automatically cleared. You can manually clear the output
lines at any time (even during a scan) and the alarm data in memory is
not cleared (however, data is cleared when you initiate a new scan). The
alarm outputs are also cleared when you initiate a new scan.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<mode> Discrete This is a
{LATCh|TRACk} required
parameter.
The
factory
default is
LATCh

Remarks
A Factory Reset (*RST command) clears all four alarm outputs but
does not clear the alarm queue in either configuration.

Return Format
The query returns LATC or TRAC. The selected configuration applies to
all four alarm output lines.

Examples
The following command enables the track mode on all four alarm output
lines.
OUTP:ALAR:MODE TRAC
The following query returns the configuration of the four alarm output
lines.
OUTP:ALAR:MODE?
Typical Response: TRAC

See Also
OUTPut Subsystem Introduction
OUTPut:ALARm:SLOPe
OUTPut:ALARm{1|2|3|4}:SOURce
OUTPut:ALARm{1|2|3|4}:CLEar

OUTPut:ALARm:SLOPe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
OUTPut:ALARm:SLOPe <edge>
OUTPut:ALARm:SLOPe?

Description
This command selects the slope of the pulse from the four TTL alarm
outputs (the selected configuration applies to all four alarm output lines).
The four alarm outputs are available from the rear-panel Alarm Output
connector.
If you select the negative/falling edge, 0 V (TTL low) indicates an alarm.
If you select the positive/rising edge, +5V (TTL high) indicates an alarm.
Changing the
slope of the
output lines
may cause
the lines to
change state.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <edge> | Discrete | {NEGative|POSitive} | This	is	a |
| ------ | -------- | ------------------- | --------- |
required
parameter.

The	keyword	NEGative	refers	to	a	falling	edge,	and	the	keyword
POSitive	refers	to	a	rising	edge,	as	shown	below.

Remarks
A Factory Reset (*RST command) resets the slope to the
negative/falling edge.

Return Format
The query returns NEG or POS. The selected configuration applies to all
four alarm output lines.

Examples
The following command selects the positive/rising edge on all four alarm
output lines.
OUTP:ALAR:SLOP POS
The following query returns the slope of the four alarm output lines.
OUTP:ALAR:SLOPE?
Typical Response: POS

See Also
OUTPut Subsystem Introduction
OUTPut:ALARm:MODE
OUTPut:ALARm{1|2|3|4}:SOURce
OUTPut:ALARm{1|2|3|4}:CLEar

OUTPut:ALARm{1|2|3|4}:SOURce
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
OUTPut:ALARm{1|2|3|4}:SOURce (@<ch_list>)
OUTPut:ALARm{1|2|3|4}:SOURce?

Description
This command assigns one of four alarm numbers to report any alarm
conditions on the specified multiplexer or digital channels.
On the digital modules, you can configure the instrument to generate an
alarm when a specific bit pattern or bit pattern change is detected on a
digital input channel or when a specific count is reached on a totalizer
channel. These channels do not have to be part of the active scan list to
generate an alarm.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <ch_list> | Channel |     | This	is	a |
| --------- | ------- | --- | --------- |
One	or	more	channels,
|     | List      |     | required   |
| --- | --------- | --- | ---------- |
|     | as	shown: |     | parameter. |
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
You can assign multiple channels to any of the four available
alarms (numbered 1 through 4, see OUTPut:ALARm<n>:SOURce
command). For example, you can configure the instrument to
generate an alarm on the Alarm 1 output when a limit is exceeded
on any of channels 103, 205, or 310. You cannot, however, assign
alarms on a specific channel to more than one alarm number.
A Factory Reset (*RST command) clears all alarm limits and turns
off all alarms. An Instrument Preset (SYSTem:PRESet command)
or Card Reset (SYSTem:CPON command) does not clear the
alarm limits and does not turn off alarms.

Return Format
The query returns a series of channel numbers in Definite-Length Block
format. The syntax is a pound sign (#) followed by a non-zero digit
representing the number of digits in the decimal integer to follow. This
digit is followed by a decimal integer indicating the number of 8-bit data
bytes to follow. This is followed by a block of data containing the
specified number of bytes.
For example:
An empty scan list (one with no channels selected) will return "#13(@)".

Examples
The following command assigns Alarm 2 to report any alarm conditions
on channels 03 and 13 in slot 100.
OUTP:ALAR2:SOUR (@103,113)
The following query returns the channels assigned to Alarm 2.
OUTP:ALAR2:SOUR?
Typical Response: #210(@103,113)

See Also
OUTPut Subsystem Introduction
CALCulate:LIMit:LOWer
CALCulate:LIMit:UPPer
OUTPut:ALARm:MODE
OUTPut:ALARm:SLOPe
OUTPut:ALARm{1|2|3|4}:CLEar

ROUTe Subsystem Introduction
Command Summary
ROUTe:CHANnel:ADVance:SOURce
ROUTe:CHANnel:ADVance:SOURce?
ROUTe:CHANnel:DELay
ROUTe:CHANnel:DELay?
ROUTe:CHANnel:DELay:AUTO
ROUTe:CHANnel:DELay:AUTO?
ROUTe:CHANnel:FWIRe
ROUTe:CHANnel:FWIRe?
ROUTe:CLOSe
ROUTe:CLOSe?
ROUTe:CLOSe:EXCLusive
ROUTe:DONE?
ROUTe:MONitor
ROUTe:MONitor?
ROUTe:MONitor:DATA?
ROUTe:MONitor:STATe
ROUTe:MONitor:STATe?
ROUTe:OPEN
ROUTe:OPEN?
ROUTe:SCAN
ROUTe:SCAN?
ROUTe:SCAN:SIZE?

ROUTe:CHANnel:ADVance:SOURce
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:CHANnel:ADVance:SOURce <source>
ROUTe:CHANnel:ADVance:SOURce?

Description
This command selects the source to provide the channel advance signal
to the next channel in the scan list for external scanning. When the
channel advance signal is received, the instrument opens the currently
selected channel and closes the next channel in the scan list. The
instrument will accept an external TTL trigger pulse, a software (bus)
command, or an immediate (continuous) scan trigger.
This command is valid only when the internal DMM is
disabled (see INSTrument:DMM command) or
removed from the Keysight 34970A/34972A.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <source> | Discrete | {EXTernal|BUS|IMMediate} | This	is	a |
| -------- | -------- | ------------------------ | --------- |
required
parameter.
The
factory
default	is
EXTernal

Remarks
For the EXTernal source, the 34970A/34972A will accept a
hardware trigger applied to the rear-panel Chan Adv Input line (Pin
6). For an external device such as a DMM, the trigger received by
the 34970A/34972A is normally sourced by the DMM's Voltmeter
Complete output signal. The 34970A/34972A advances to the next
channel in the scan list each time a low-true TTL pulse is received.
For the BUS (software) source, the 34970A/34972A is triggered by
the *TRG command received over the remote interface. The *TRG
command will not be accepted unless the 34970A/34972A is in the
"wait-for-trigger" state (see INITiate command). If the internal
DMM receives an external trigger before the next "waiting for
trigger" state, it will buffer one *TRG command and then ignore
any additional triggers received (no error is generated).
For the IMMediate (continuous) source, the channel advance
signal is always present.
The channel advance signal is ignored unless you have initiated
the scan (INITiate command) and have received a scan trigger
(TRIGger:SOURce command). Although the
ROUTe:CHANnel:ADVance:SOURce command shares some of
the same signals as the TRIGger:SOURce command, they cannot
be set to the same source (except IMMediate). If you attempt to
select the same source, an error is generated and the
TRIGger:SOURce is reset to IMMediate.
When the first trigger is received, the 34970A/34972A closes the
first channel in the scan list without waiting for the specified
channel advance source. If the channel advance source is
EXTernal and the 34970A/34972A receives an event before it is
ready, it will buffer one event and then ignore any additional
events received (no error is generated).

After the final channel in the scan list is closed, one more channel
advance event must be received to complete the scan.
A channel advance signal is not required for digital input or
totalizer channels included in the scan list. Measurements on
these channels are still performed by the 34970A/34972A and do
not require synchronization with the external instrument.

Return Format
The query returns the present channel advance source: "EXT", "BUS", or
"IMM".

Examples
The following program segment configures the 34970A/34972A for
scanning using an external channel advance source. In this
configuration, the 34970A/34972A advances to the next channel in the
scan list each time a low-true TTL pulse is received.
INST:DMM OFF !Disable internal DMM
ROUT:SCAN (@101:120) !Configure scan list
TRIG:SOUR IMM !Set trigger source
TRIG:COUN 5 !Set trigger count
ROUT:CHAN:ADV:SOUR EXT !Set channel advance source
The following query returns the channel advance source currently
selected on the 34970A/34972A.
ROUT:CHAN:ADV:SOUR?
Typical Response: EXT

See Also
ROUTe Subsystem Introduction
INITiate
INSTrument:DMM
ROUTe:CHANnel:FWIRe
TRIGger:SOURce

ROUTe:CHANnel:DELay
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:CHANnel:DELay <seconds>,(@<ch_list>)
ROUTe:CHANnel:DELay? (@<ch_list>)

Description
This command adds a delay between multiplexer channels in the scan
list (useful for high-impedance or high-capacitance circuits). The delay is
inserted between the relay closure and the actual measurement on each
channel, in addition to any delay that will implicitly occur due to relay
settling time. The programmed channel delay overrides the default
channel delay that the instrument automatically adds to each channel.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <seconds> | Numeric | A	number	from	0	to	60, | This	is	a |
| --------- | ------- | ---------------------- | --------- |
|           |         | with	1	ms	resolution.  | required  |
parameter.
| <ch_list> | Channel |                       | 	   |
| --------- | ------- | --------------------- | --- |
|           | List    | One	or	more	channels, |     |
as	shown:
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
You can select a unique delay for each channel on the module.
The default channel delay is automatic; the instrument determines
the delay based on function, range, integration time, and AC filter
setting.
The channel delay is valid only while scanning. If no channels
have been assigned to the scan list (see ROUTe:SCAN
command), the specified channel delay is ignored (no error is
generated).
To ensure you are getting the most accurate measurements
possible, use care when setting the channel delay less than the
default value (Automatic). The default channel delay is designed to
optimize parameters, such as settling time, for the most accurate
measurements.
The CONFigure and MEASure? commands set the channel delay
to Automatic.
The instrument sets the channel delay to Automatic after a Factory
Reset ( *RST command).

Return Format
The query returns the delay in seconds in the form "+1.00000000E+00"
for each channel specified. Multiple responses are separated by
commas.

Examples
The following command adds a 2-second channel delay to channels 03
and 13 in slot 100.
ROUT:CHAN:DEL 2,(@103,113)
The following query returns the channel delay selected on channels 03
and 13 in slot 100.
ROUT:CHAN:DEL? (@103,113)
Typical Response: +2.00000000E+00,+2.00000000E+00

See Also
ROUTe Subsystem Introduction
ROUTe:CHANnel:DELay:AUTO
ROUTe:SCAN

ROUTe:CHANnel:DELay:AUTO
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:CHANnel:DELay:AUTO <state>[,(@<ch_list>)]
ROUTe:CHANnel:DELay:AUTO? [(@<ch_list>)]

Description
This command disables or enables an automatic channel delay on the
specified channels. If enabled, the instrument determines the delay
based on function, range, integration time, and AC filter setting.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<state> Boolean {OFF|0|ON|1} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Selecting a specific channel delay using the
ROUTe:CHANnel:DELay command disables the automatic
channel delay.
The CONFigure and MEASure? commands set the channel delay
to Automatic.
The instrument sets the channel delay to Automatic after a Factory
Reset ( *RST command).

Return Format
The query returns 0 (OFF) or 1 (ON) for each channel specified. Multiple
responses are separated by commas.

Examples
The following command enables an automatic channel delay on
channels 03 and 13 in slot 100.
ROUT:CHAN:DEL:AUTO ON,(@103,113)
The following query returns the automatic channel delay settings on
channels 03 and 13 in slot 100.
ROUT:CHAN:DEL:AUTO? (@103,113)
Typical Response: 1,1

See Also
ROUTe Subsystem Introduction
ROUTe:CHANnel:DELay

ROUTe:CHANnel:FWIRe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:CHANnel:FWIRe <state>[,(@<ch_list>)]
ROUTe:CHANnel:FWIRe? [(@<ch_list>)]

Description
This command configures the specified channels for 4-wire external
scanning without the internal DMM. When enabled, channel n is paired
with channel n+10 (34901A) or n+8 (34902A) to provide source and
sense connections.
This command is valid only when the internal
DMM is disabled (see INSTrument:DMM
command) or removed from the Keysight
34970A/34972A.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module

Parameters
Name Type Range of Values Default
Value
<state> Boolean {OFF|0|ON|1}
<ch_list> Channel If
List One or more channels, <ch_list>
as shown: is
omitted,
(@310) - channel 10 on
this
the module in slot 300.
command
applies to
(@305:310) - channels
the
05 through 10 on the
current
module in slot 300.
scan list.
(@202:207,209,302:308)
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
The ROUTe:CLOSe, ROUTe:CLOSe:EXCLusive, and
ROUTe:OPEN commands ignore the current
ROUTe:CHANnel:FWIRe setting (if no channels are in the scan
list).

Return Format
The query returns 0 (OFF) or 1 (ON) for each channel specified. Multiple
responses are separated by commas.

Examples
The following command configures channels 03 and 05 in slot 100 for 4-
wire external scanning.
INST:DMM OFF !Disable internal DMM
ROUT:CHAN:FWIR ON,(@103,105) !Enable 4-wire
configuration
The following query returns the 4-wire configuration selected on
channels 03 and 05 in slot 100.
ROUT:CHAN:FWIR? (@103,105)
Typical Response: 1,1

See Also
ROUTe Subsystem Introduction
INSTrument:DMM
ROUTe:CHANnel:ADVance:SOURce

ROUTe:CLOSe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:CLOSe (@<ch_list>)
ROUTe:CLOSe? (@<ch_list>)

Description
This command closes the specified channels on a multiplexer or switch
module. On the multiplexer modules, if any channel on the module is
defined to be part of the scan list, attempting to send this command will
result in an error.
Used With:
All modules except 34907A

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <ch_list> | Channel |     | This	is	a |
| --------- | ------- | --- | --------- |
One	or	more	channels,
|     | List      |     | required   |
| --- | --------- | --- | ---------- |
|     | as	shown: |     | parameter. |
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
For the matrix module (34904A), the channel number represents
the intersection of the desired row and column. For example,
channel 234 represents the intersection of row 3 and column 4 on
the module in slot 200 (assumes two-wire mode). For more
information, see the simplified schematics.
The RF Multiplexer modules (34905A, 34906A) will not respond to
the ROUTe:OPEN command (an error is generated). To "open" a
channel on these modules, send the ROUTe:CLOSe command to
a different channel in the same bank.
As part of the scan setup, the ROUTe:SCAN command examines
the scan list and determines which channel relays and Analog Bus
relays will be impacted by the scan. The following rules will apply
once the scan is initiated and will impact what relays can be
manually opened and closed.
a. When the scan is initiated, the instrument will open all channels in
modules that contain one or more channels in the scan list.
b. While the scan is running, the instrument prohibits use of all
channels in modules that contain one or more channels in the
specified <ch_list> (these channels are dedicated to the scan).

Return Format
The query returns 1 if the specified channel is closed or 0 if the specified
channel is open. Multiple responses are separated by commas.

Examples
The following command closes channels 03 and 13 in slot 100 (no
Analog Bus connections are made).
ROUT:CLOS (@103,113)
The following command closes channel 03 on the matrix module in slot
300.
ROUT:CLOS (@303)
The following query reads the state of channels 03 and 13 in slot 100
(1 = closed; 0 = open).
ROUT:CLOS? (@103,113)
Typical Response:1,1

See Also
ROUTe Subsystem Introduction
DIAGnostic:RELay:CYCLes?
ROUTe:CLOSe:EXCLusive
ROUTe:OPEN

ROUTe:CLOSe:EXCLusive
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
ROUTe:CLOSe:EXCLusive (@<ch_list>)

Description
This command opens all channels on a multiplexer or switch module and
then closes the specified channels. On the multiplexer modules, if any
channel on the module is defined to be part of the scan list, attempting to
send this command will result in an error.
Used With:
All modules except 34907A

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <ch_list> | Channel |     | This	is	a |
| --------- | ------- | --- | --------- |
One	or	more	channels,
|     | List      |     | required   |
| --- | --------- | --- | ---------- |
|     | as	shown: |     | parameter. |
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
For the matrix modules (34904A), the channel number represents
the intersection of the desired row and column. For example,
channel 234 represents the intersection of row 3 and column 4 on
the module in slot 200 (assumes two-wire mode). For more
information, see the simplified schematics.
This command opens all channels first, and then closes the
channels in the <ch_list>, one at a time. Before it closes each
channel, it opens all previous channels.
The RF Multiplexer modules (34905A, 34906A) will not respond to
the ROUTe:OPEN command (an error is generated). To "open" a
channel on these modules, send the ROUTe:CLOSe:EXCLusive
command to a different channel in the same bank.

Example
The following command opens all channels and then closes channel 03
on the matrix module in slot 300.
ROUT:CLOS:EXCL (@303)

See Also
ROUTe Subsystem Introduction
ROUTe:CLOSe
ROUTe:OPEN

ROUTe:DONE?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
ROUTe:DONE?

Description
This queries the status of all relay operations on cards not involved in the
scan and returns a 1 when all relay operations are finished (even during
a scan).

Return Format
The query returns a 1.

Example
The following query returns a 1 when all relay operations are finished.
ROUT:DONE?
Typical Response: 1

See Also
ROUTe Subsystem Introduction

ROUTe:MONitor
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:MONitor (@<channel>)
ROUTe:MONitor?

Description
This command/query selects the channel to be displayed on the front
panel. Only one channel can be monitored at a time.

Parameters
Name Type Range of Default Value
Values
<channel> Channel This is a
A single required
channel, parameter.
specified
as in the
following
examples.
(@310) -
channel 10
on the
module in
slot 300.
(@214) -
channel14
on the
module in
slot 200.

Remarks
Channels must be configured for a measurement in order to be
monitored (see CONFigure and SENSe commands). Configuring a
channel for a measurement makes it monitorable and makes it
part of the scan list.
A scan always has priority over the Monitor function (see
ROUTe:SCAN command).
Any channel that can be "read" by the instrument can be
monitored. This includes any combination of temperature, voltage,
resistance, current, frequency, or period measurements on
multiplexer channels. You can also monitor a digital input channel
or the totalizer count on the digital modules.
Mx+B scaling and alarm limits are applied to the selected channel
during a Monitor and all alarm data is stored in the alarm queue
(which will be cleared if power fails).
For monitor operations using a multiplexer module, no
measurements are taken if the internal DMM is disabled (see
INSTrument:DMM command) or not installed in the mainframe.
The internal DMM is not required for monitor operations on the
digital modules.
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 (34901A) or n+8
(34902A) to provide the source and sense connections.
The count on a totalizer channel is not reset when it is being
monitored (the Monitor ignores the totalizer reset mode).

Return Format
The query returns the Monitor channel in Definite-Length Block format.
The syntax is a pound sign (#) followed by a non-zero digit representing
the number of characters to follow. This digit is followed by a decimal
integer indicating the number of data bytes to follow. This is followed by
a block of data containing the specified number of bytes. The query
always returns the channel currently displayed on the front panel.
For example:

Examples
The following program segment configures channel 3 in slot 100 for DC
voltage measurements, enables monitoring on the channel, and turns on
the Monitor mode.
CONF:VOLT:DC (@103)
ROUT:MON:CHAN (@103)
ROUT:MON:STAT ON
The following command queries the channel currently selected as the
Monitor channel.
ROUT:MON:CHAN?
Typical Response: #16(@103)

See Also
ROUTe Subsystem Introduction
ROUTe:MONitor:STATe

ROUTe:MONitor:DATA?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:MONitor:DATA?

Description
This query reads the monitor data from the selected channel. It returns
the reading only; the units, time, channel, and alarm information are not
returned (the FORMat:READing commands do not apply to monitor
readings).

Remarks
If the Monitor mode is not currently enabled, this query returns an
error indicating that it is unable to perform the requested
operation.
Readings acquired during a Monitor are not stored in memory but
they are displayed on the front panel; however, all readings from a
scan in progress at the same time are stored in memory.

Return Format
The query returns one reading for the Monitor channel, in the format
+1.12345678E+01. If no data is available for the specified channel,
instrument waits for data to become available.

Examples
The following query returns one reading from the Monitor channel.
ROUT:MON:DATA?
Typical Response: +1.84280000E-05

See Also
ROUTe Subsystem Introduction
ROUTe:MONitor
ROUTe:MONitor:STATe

ROUTe:MONitor:STATe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:MONitor:STATe <mode>
ROUTe:MONitor:STATe?

Description
This command disables or enables the Monitor mode. The Monitor mode
is equivalent to making continuous measurements on a single channel
with an infinite scan count. Only one channel can be monitored at a time
but you can change the channel being monitored at any time. This
feature is useful for troubleshooting your system before a test or for
watching an important signal.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of | Default	Value |
| ---- | ---- | -------- | ------------- |
Values
| <mode> | Boolean | {OFF|0|ON|1} | This	is	a |
| ------ | ------- | ------------ | --------- |
required
parameter.

Remarks
Channels must be configured for a measurement in order to be
monitored (see CONFigure and SENSe commands). Configuring a
channel for a measurement makes it monitorable and makes it
part of the scan list.
The Monitor mode is automatically enabled on all channels that
are part of the active scan list (see ROUTe:SCAN command).
A scan always has priority over the Monitor function (see
ROUTe:SCAN command).
The Monitor mode ignores all trigger settings (see
TRIGger:SOURce command) and takes continuous readings on
the selected channel using the IMMediate (continuous) source.
Any channel that can be "read" by the instrument can be
monitored. This includes any combination of temperature, voltage,
resistance, current, frequency, or period measurements on
multiplexer channels. You can also monitor a digital input channel
or the totalizer count on the digital modules.
Mx+B scaling and alarm limits are applied to the selected channel
during a Monitor and all alarm data is stored in the alarm queue
(which will be cleared if power fails).
For monitor operations using a multiplexer module, no
measurements are taken if the internal DMM is disabled (see
INSTrument:DMM command) or not installed in the mainframe.
The internal DMM is not required for monitor operations on the
digital modules.
The count on a totalizer channel is not reset when it is being
monitored (the Monitor ignores the totalizer reset mode).
Readings acquired during a Monitor are not stored in memory but

they are displayed on the front panel; however, all readings from a
scan in progress at the same time are stored in memory.

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following program segment configures channel 3 in slot 100 for DC
voltage measurements, enables monitoring on the channel, and turns on
the Monitor mode.
CONF:VOLT:DC (@103)
ROUT:MON:CHAN (@103)
ROUT:MON:STAT ON
The following query returns the state of the Monitor mode.
ROUT:MON:STAT?
Typical Response: 1

See Also
ROUTe Subsystem Introduction
ROUTe:CLOSe
ROUTe:MONitor:DATA?
ROUTe:OPEN

ROUTe:OPEN
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:OPEN (@<ch_list>)
ROUTe:OPEN? (@<ch_list>)

Description
This command opens the specified channels on a multiplexer or switch
module.
Used With:
All modules except 34907A

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <ch_list> | Channel |     | This	is	a |
| --------- | ------- | --- | --------- |
One	or	more	channels,
|     | List      |     | required   |
| --- | --------- | --- | ---------- |
|     | as	shown: |     | parameter. |
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
For the matrix modules, the channel number represents the
intersection of the desired row and column. For example, channel
234 represents the intersection of row 3 and column 4 on the
module in slot 200 (assumes two-wire mode). For more
information, see the simplified schematics.
The RF Multiplexer modules (34905A, 34906A) will not respond to
the ROUTe:OPEN command (an error is generated). To "open" a
channel on these modules, send the ROUTe:CLOSe command to
a different channel in the same bank.
As part of the scan setup, the ROUTe:SCAN command examines
the scan list and determines which channel relays and Analog Bus
relays will be impacted by the scan. The following rules will apply
once the scan is initiated and will impact what relays can be
manually opened and closed.
a. When the scan is initiated, the instrument will open all channels in
modules that contain one or more channels in the scan list.
b. While the scan is running, the instrument prohibits use of all
channels in modules that contain one or more channels in the
specified <ch_list> (these channels are dedicated to the scan).

Return Format
The query returns 1 if the specified channel is open or 0 if the specified
channel is closed. Multiple responses are separated by commas.

Examples
The following command opens channels 03 and 13 in slot 100.
ROUT:OPEN (@103,113)
The following command opens channel 03 on the matrix module in slot
300.
ROUT:OPEN (@303)
The following command opens channels 01 through 08 on the matrix
module in slot 300.
ROUT:OPEN (@301:308)
The following query reads the state of channels 03 and 06 in slot 100
(1 = open; 0 = closed).
ROUT:OPEN? (@103,106)
Typical Response: 1,1

See Also
ROUTe Subsystem Introduction
ROUTe:CLOSe

ROUTe:SCAN
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
ROUTe:SCAN (@<scan_list>)
ROUTe:SCAN?

Description
This command selects the channels to be included in the scan list. This
command is used in conjunction with the CONFigure commands to set
up an automated scan. The specified channels supersede any channels
previously defined to be part of the scan list. To start the scan, use the
INITiate or READ? command.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer)
34908A 40 Channel Single-Ended Multiplexer Module
To remove all channels from the
present scan list, send
"ROUT:SCAN (@)".

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <scan_list> | Scan |     | This	is	a |
| ----------- | ---- | --- | --------- |
One	or	more	channels,
|     | List      |     | required   |
| --- | --------- | --- | ---------- |
|     | as	shown: |     | parameter. |
(@310)	-	channel	10	on
the	module	in	slot	300.
(@305:310)	-	channels
05	through	10	on	the
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
To remove all channels from the scan list, issue the command
ROUT:SCAN (@).
The instrument scans the list of channels in ascending order from
slot 100 through slot 300 (channels are re-ordered as
needed).When you specify a range of channels in the <scan_list>,
the channels are always sorted in ascending order. Therefore,
(@109:101) will always be interpreted as 101, 102, 103, etc.
You can use either the internal DMM or an external instrument to
make measurements of your configured channels. However, the
34970A/34972A allows only one scan list at a time; you cannot
scan some channels using the internal DMM and others using an
external instrument. Readings are stored in 34970A/34972A
memory only when the internal DMM is used, except for digital
input and totalizer channels.
You can store at least 50,000 readings in memory and all readings
are automatically time stamped. If memory overflows, the new
readings will overwrite the first (oldest) readings stored; the most
recent readings are always preserved. You can read the contents
of memory at any time, even during a scan. Reading memory is
not cleared when you read it.
Each time you start a new scan, the instrument clears all readings
(including alarm data) stored in reading memory from the previous
measurement. Therefore, the contents of memory are always from
the most recent measurement.
If you abort a scan that is running (see ABORt command), the
instrument will terminate any reading in progress (readings are not
cleared from memory). If a scan is in progress when the command
is received, the scan will not be completed and you cannot resume
the scan from where it left off. Note that if you initiate a new scan,

all readings are cleared from memory.
The CONFigure and MEASure? commands overwrite the scan list.
The present scan list is stored in non-volatile memory and will be
retained when power is turned off.

Return Format
The query returns a list of channel numbers in Definite-Length Block
format. The syntax is a pound sign (#) followed by a non-zero digit
representing the number of characters to follow. This digit is followed by
a decimal integer indicating the number of data bytes to follow. This is
followed by a block of data containing the specified number of bytes. An
empty scan list (one with no channels selected) will indicated by
"#13(@)"
For example:

Examples
The following program segment shows how to use the CONFigure
command to configure two channels for DC voltage measurements. The
ROUTe:SCAN command puts the two channels into the scan list (and
redefines the scan list). The INITiate command places the instrument in
the "wait-for-trigger" state and then sends the readings to memory. The
FETCh? command transfers the readings from memory to the
instrument's output buffer.
CONF:VOLT:DC 10,0.003,(@103,108)
ROUT:SCAN (@103,108)
INIT
FETC?
Typical Response: +4.27150000E-03,+1.32130000E-03
The following command clears the present scan list.
ROUT:SCAN (@)
The following query returns a list of channels in the present scan list.
ROUT:SCAN?
Typical Response: #210(@103,108)

See Also
ROUTe Subsystem Introduction
ABORt
INITiate
READ?
ROUTe:SCAN:SIZE?

ROUTe:SCAN:SIZE?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
ROUTe:SCAN:SIZE?

Description
This query returns the number of channels in the scan list.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
The present scan list is stored in non-volatile memory and will be
retained when power is turned off.

Return Format
The query returns the number of channels as a signed integer from 0 to
120.

Example
The following query returns the number of channels in the scan list.
ROUT:SCAN (@101:120)
ROUT:SCAN:SIZE?
Typical Response: +20

See Also
ROUTe Subsystem Introduction
ROUTe:SCAN

SENSe Subsystem Introduction
If you specify a <ch_list> with one of these commands, that <ch_list>
overwrites the current scan list.

Command Summary
AC Current
[SENSe:]CURRent:AC:BANDwidth
[SENSe:]CURRent:AC:BANDwidth?
[SENSe:]CURRent:AC:RANGe
[SENSe:]CURRent:AC:RANGe?
[SENSe:]CURRent:AC:RANGe:AUTO
[SENSe:]CURRent:AC:RANGe:AUTO
[SENSe:]CURRent:AC:RESolution
[SENSe:]CURRent:AC:RESolution?
DC Current
[SENSe:]CURRent:DC:APERture
[SENSe:]CURRent:DC:APERture?
[SENSe:]CURRent:DC:NPLC
[SENSe:]CURRent:DC:NPLC?
[SENSe:]CURRent:DC:RANGe
[SENSe:]CURRent:DC:RANGe?
[SENSe:]CURRent:DC:RANGe:AUTO
[SENSe:]CURRent:DC:RANGe:AUTO
[SENSe:]CURRent:DC:RESolution
[SENSe:]CURRent:DC:RESolution?
AC Voltage

[SENSe:]VOLTage:AC:RANGe
[SENSe:]VOLTage:AC:RANGe?
[SENSe:]VOLTage:AC:RANGe:AUTO
[SENSe:]VOLTage:AC:RANGe:AUTO?
[SENSe:]VOLTage:AC:BANDwidth
[SENSe:]VOLTage:AC:BANDwidth?
DC Current
[SENSe:]VOLTage:DC:APERture
[SENSe:]VOLTage:DC:APERture?
[SENSe:]VOLTage:DC:NPLC
[SENSe:]VOLTage:DC:NPLC?
[SENSe:]VOLTage:DC:RANGe
[SENSe:]VOLTage:DC:RANGe?
[SENSe:]VOLTage:DC:RANGe:AUTO
[SENSe:]VOLTage:DC:RANGe:AUTO?
[SENSe:]VOLTage:DC:RESolution
[SENSe:]VOLTage:DC:RESolution?
2-Wire Resistance
[SENSe:]RESistance:APERture
[SENSe:]RESistance:APERture?
[SENSe:]RESistance:NPLC
[SENSe:]RESistance:NPLC?
[SENSe:]RESistance:OCOMpensated
[SENSe:]RESistance:OCOMpensated?

[SENSe:]RESistance:RANGe
[SENSe:]RESistance:RANGe?
[SENSe:]RESistance:RANGe:AUTO
[SENSe:]RESistance:RANGe:AUTO?
[SENSe:]RESistance:RESolution
[SENSe:]RESistance:RESolution?
4-Wire Resistance
[SENSe:]FRESistance:APERture
[SENSe:]FRESistance:APERture?
[SENSe:]FRESistance:NPLC
[SENSe:]FRESistance:NPLC?
[SENSe:]FRESistance:OCOMpensated
[SENSe:]FRESistance:OCOMpensated?
[SENSe:]FRESistance:RANGe
[SENSe:]FRESistance:RANGe?
[SENSe:]FRESistance:RANGe:AUTO
[SENSe:]FRESistance:RANGe:AUTO?
[SENSe:]FRESistance:RESolution
[SENSe:]FRESistance:RESolution?
Frequency
[SENSe:]FREQuency:APERture
[SENSe:]FREQuency:APERture?
[SENSe:]FREQuency:RANGe:LOWer
[SENSe:]FREQuency:RANGe:LOWer?

[SENSe:]FREQuency:VOLTage:RANGe
[SENSe:]FREQuency:VOLTage:RANGe?
[SENSe:]FREQuency:VOLTage:RANGe:AUTO
[SENSe:]FREQuency:VOLTage:RANGe:AUTO?
Period
[SENSe:]PERiod:APERture
[SENSe:]PERiod:APERture?
[SENSe:]PERiod:VOLTage:RANGe
[SENSe:]PERiod:VOLTage:RANGe?
[SENSe:]PERiod:VOLTage:RANGe:AUTO
[SENSe:]PERiod:VOLTage:RANGe:AUTO?
Temperature
[SENSe:]TEMPerature:APERture
[SENSe:]TEMPerature:APERture?
[SENSe:]TEMPerature:NPLC
[SENSe:]TEMPerature:NPLC?
[SENSe:]TEMPerature:RJUNction?
[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated
[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated?
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]?
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE?
[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated

[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated?
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]?
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE?
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk?
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction?
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE?
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE?
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE?
[SENSe:]TEMPerature:TRANsducer:TYPE
[SENSe:]TEMPerature:TRANsducer:TYPE?
Digital I/O and Totalizer
[SENSe:]DIGital:DATA:{BYTE|WORD}?
[SENSe:]TOTalize:CLEar:IMMediate
[SENSe:]TOTalize:DATA?
[SENSe:]TOTalize:SLOPe
[SENSe:]TOTalize:SLOPe?
[SENSe:]TOTalize:STARt[:IMMediate]
[SENSe:]TOTalize:STOP[:IMMediate]

[SENSe:]TOTalize:TYPE
[SENSe:]TOTalize:TYPE?
Miscellaneous
[SENSe:]FUNCtion
[SENSe:]FUNCtion?
[SENSe:]ZERO:AUTO
[SENSe:]ZERO:AUTO?

[SENSe:]CURRent:AC:BANDwidth
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]CURRent:AC:BANDwidth {<filter>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:AC:BANDwidth? [{(@<ch_list>)|MIN|MAX}]

Description
The instrument uses three different AC filters which enable you to either
optimize low frequency accuracy or achieve faster AC settling times. The
instrument selects the slow (3 Hz), medium (20 Hz), or fast (200 Hz) filter
based on the input frequency that you specify with this command for the
selected channels. If you omit the optional <ch_list> parameter, this
command applies to the currently defined scan list.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module (channels 21
and 22 only)

Parameters
Name Type Range of Values Default
Value
<filter> Discrete {3|20|200} 20
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@321) - channel 21 on
parameter,
the module in slot 300.
this
command
(@221:222) - channels
applies to
21 through 22 on the
the
module in slot 200.
currently
defined
(@121:122,222,321:322)
scan list.
- channels 21 and 22 on
the module in slot 100,
channel 22 on the
module in slot 200, and
channels 21-22 on the
module in slot 300.
Note that the channels
must be of the form s21
and s22, where s is the
first digit of the slot
number.

Remarks
This	command	applies	to	AC	current	measurements	only.
For	the	<filter>	parameter,	specify	the	lowest	frequency	expected
in	the	input	signal	on	the	specified	channels.	The	instrument
selects	the	appropriate	filter	based	on	the	frequency	you	specify.
| Input     | Default  | Minimum        |
| --------- | -------- | -------------- |
| Frequency | Settling | Settling	Delay |
Delay
| 3	Hz	to	300	kHz  | 7	seconds	/    | 1.5	seconds |
| ---------------- | -------------- | ----------- |
| (Slow)           | reading        |             |
| 20	Hz	to	300	kHz | 1	second	/     | 200	ms      |
| (Medium)         | reading        |             |
| 200	Hz	to	300    | 0.12	seconds	/ | 20	ms       |
| kHz	(Fast)       | reading        |             |
The	CONFigure	and	MEASure?	commands	automatically	select
the	default	20	Hz	(medium)	filter.
The	instrument	selects	the	default	20	Hz	(medium)	filter	after	a
Factory	Reset	(*RST	command).	An	Instrument	Preset
(SYSTem:PRESet	command)	or	Card	Reset	(SYSTem:CPON
command)	does	not	change	the	setting.
The	settling	delay	is	controlled	by	the	ROUTe:CHANnel:DELay
command.	You	get	the	default	delay	with
ROUTe:CHANnel:DELay:AUTO	ON.

Return Format
The query returns 3 (slow), 20 (medium), or 200 (fast) for each channel
specified. Multiple responses are separated by commas.

Examples
The following command selects the slow filter (3 Hz) on channels 21 and
22 in slot 100.
CURR:AC:BAND 3,(@121,122)
The following query returns the AC filter settings on channels 21 and 22
in slot 100.
CURR:AC:BAND? (@121,122)
Typical Response: 3,3

See Also
SENSe Subsystem Introduction
[SENSe:]CURRent:AC:RANGe
CONFigure:CURRent:AC

[SENSe:]CURRent:AC:RANGe
[SENSe:]CURRent:DC:RANGe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]CURRent:AC:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:AC:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]CURRent:DC:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:DC:RANGe? [{(@<ch_list>)|MIN|MAX}]

Description
These commands select the measurement range for AC and DC current
measurements on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module (channels 21
and 22 only)

Parameters
Name Type Range of Values Default
Value
<range> Discrete This is a
Expected value in amps required
(ranges shown below). parameter.
10 mA (MIN)
100 mA
1 A (MAX)
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@321) - channel 21 on
parameter,
the module in slot 300.
this
command
(@221:222) - channels
applies to
21 through 22 on the
the
module in slot 200.
currently
defined
(@121:122,222,321:322)
scan list.
- channels 21 and 22 on
the module in slot 100,
channel 22 on the
module in slot 200, and
channels 21-22 on the
module in slot 300.
Note that the channels
must be of the form s21
and s22, where s is the
first digit of the slot

number.

Remarks
Selecting a discrete range will disable autoranging on the specified
channels (see [SENSe:]CURRent:AC:RANGe:AUTO and
[SENSe:]CURRent:DC:RANGe:AUTO commands).
The CONFigure and MEASure? commands automatically enable
autoranging if the first parameter is AUTO, DEF or omitted.
If the input signal is greater than can be measured on the selected
range (manual ranging), the instrument gives an overload
indication: "±OVLD" from the front panel or "±9.9E+37" from the
remote interface.
The instrument selects autoranging after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns the range in the form "+1.00000000E-01" for each
channel specified. Multiple responses are separated by commas.

Examples
The following command selects the 100 mA range on channels 21 and
22 in slot 100.
CURR:AC:RANG 0.1,(@121,122)
The following query returns the range selected on channels 21 and 22 in
slot 100.
CURR:AC:RANG? (@121,122)
Typical Response: +1.00000000E-01,+1.00000000E-01

See Also
SENSe Subsystem Introduction
CONFigure:CURRent:AC
CONFigure:CURRent:DC
[SENSe:]CURRent:AC:RANGe:AUTO
[SENSe:]CURRent:DC:RANGe:AUTO

[SENSe:]CURRent:AC:RANGe:AUTO
[SENSe:]CURRent:DC:RANGe:AUTO
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]CURRent:AC:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]CURRent:AC:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]CURRent:DC:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]CURRent:DC:RANGe:AUTO? [(@<ch_list>)]

Description
These commands disable or enable autoranging for AC and DC current
measurements on the specified channels. Autoranging is convenient
because the instrument automatically selects the range for each
measurement based on the input signal detected.If you omit the optional
<ch_list> parameter, this command applies to the currently defined scan
list.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module (channels 21
and 22 only)

Parameters
Name Type Range of Values Default
Value
<mode> Boolean {OFF|0|ON|1} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@321) - channel 21 on
parameter,
the module in slot 300.
this
command
(@221:222) - channels
applies to
21 through 22 on the
the
module in slot 200.
currently
defined
(@121:122,222,321:322)
scan list.
- channels 21 and 22 on
the module in slot 100,
channel 22 on the
module in slot 200, and
channels 21-22 on the
module in slot 300.
Note that the channels
must be of the form s21
and s22, where s is the
first digit of the slot
number.

Remarks
Autorange thresholds:
Down range at: <10% of range
Up range at: >120% of range
With autoranging enabled, the instrument selects one of the
following ranges based on the input signal detected:
10 mA
100 mA
1 A
Selecting a discrete range (see [SENSe:]CURRent:AC:RANGe
command) will disable autoranging on the specified channels.
The CONFigure and MEASure? commands automatically enable
autoranging if the first parameter is AUTO, DEF or omitted.
The instrument enables autoranging after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns 0 (OFF) or 1 (ON) for each channel in the <ch_list>.
Multiple values are separated by commas.

Examples
In these examples, you could substitute the node name DC for AC.
The following command turns on AC current measurement autoranging
for two channels.
CURR:AC:RANG:AUTO 1, (@221:222)
The following query returns the value of autoranging for three channels.
CURR:AC:RANG:AUTO? (@221,321,322)
Typical Response: 1,0,1

See Also
SENSe Subsystem Introduction

[SENSe:]CURRent:AC:RESolution
[SENSe:]CURRent:DC:RESolution
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]CURRent:AC:RESolution {<resolution>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]CURRent:AC:RESolution? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]CURRent:DC:RESolution {<resolution>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]CURRent:DC:RESolution? [{(@<ch_list>)|MIN|MAX}]

Description
This command selects the measurement resolution for current
measurements on the specified channels. The instrument clears all
readings from memory when a new scan is initiated, when any
measurement parameters are changed (CONFigure and SENSe
commands), and when the triggering configuration is changed (TRIGger
commands).If you omit the optional <ch_list> parameter, this command
applies to the currently defined scan list.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module (channels 21
and 22 only)

Parameters
Name Type Range of Values Default
Value
<resolution> Numeric Desired resolution in amps. 0.000003
x Range
(1 PLC)
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@321) - channel 21 on
parameter,
the module in slot 300.
this
command
(@221:222) - channels
applies to
21 through 22 on the
the
module in slot 200.
currently
defined
(@121:122,222,321:322)
scan list.
- channels 21 and 22 on
the module in slot 100,
channel 22 on the
module in slot 200, and
channels 21-22 on the
module in slot 300.
Note that the channels
must be of the form s21
and s22, where s is the
first digit of the slot
number.

Remarks
For	the	<resolution>	parameter,	you	can	substitute	MIN	or	MAX	for
a	numeric	value.	MIN	selects	the	smallest	value	accepted,	which
gives	the	highest	resolution;	MAX	selects	the	largest	value
accepted,	which	gives	the	least	resolution.
The	instrument	will	dispatch	a	settings	conflict	error	if	you	issue
this	command	when[SENSe:]CURRent:AC:RANGe:AUTO	(AC
resolution)	or	[SENSe:]CURRent:DC:RANGe:AUTO	(DC
resolution)	is	ON	for	one	or	more	of	the	specified	channels.
Setting	the	resolution	also	sets	the	integration	time	for	the
measurement.	The	following	table	shows	the	relationship	between
integration	time,	measurement	resolution,	number	of	digits,	and
number	of	bits.
| Integration | Resolution | Digits Bits |
| ----------- | ---------- | ----------- |
Time
| 0.02	PLC | <0.0001	x   | 4½ 15  |
| -------- | ----------- | ------ |
|          | Range       | Digits |
| 0.2	PLC  | <0.00001	x  | 5½ 18  |
|          | Range       | Digits |
| 1	PLC    | <0.000003	x | 5½ 20  |
|          | Range       | Digits |
| 2	PLC    | <0.0000022  | 6½ 21  |
|          | x	Range     | Digits |
| 10	PLC   | <0.000001	x | 6½ 24  |
|          | Range       | Digits |
| 20	PLC   | <0.0000008  | 6½ 25  |
|          | x	Range     | Digits |
| 100	PLC  | <0.0000003  | 6½ 26  |
|          | x	Range     | Digits |

200 PLC <0.00000022 6½ 26
x Range Digits
You can also set the integration time by specifying an aperture
time (see [SENSe:]CURRent[:DC]:APERture command). However,
note that specifying integration time using NPLCs executes faster
and offers better noise rejection characteristics for values of NPLC
greater than 1.
The CONFigure, MEASure?, [SENSe:]CURRent[:DC]:NPLC, and
[SENSe:]CURRent[:DC]:RESolution commands automatically
disable the aperture mode (these commands select an integration
time in NPLCs).
The instrument sets the resolution to 1 PLC after a Factory Reset
(*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns the resolution in the form "+1.00000000E-04" for each
channel specified. Multiple responses are separated by commas.

Examples
The following command sets the measurement resolution to 0.01 mA on
channels 21 and 22 in slot 100.
CURR:DC:RES 0.00001,(@121,122)
The following query returns the resolution selected on channels 21 and
22 in slot 100.
CURR:DC:RES? (@121,122)
CURR:DC:APER:ENAB? !Verify that aperture mode is
disabled ("0")
Typical Response: +1.00000000E-04,+1.00000000E-04

See Also
SENSe Subsystem Introduction
CONFigure:CURRent:AC
CONFigure:CURRent:DC
[SENSe:]CURRent:AC:RANGe:AUTO
[SENSe:]CURRent:DC:RANGe:AUTO
[SENSe:]CURRent:DC:APERture
[SENSe:]CURRent:DC:NPLC

[SENSe:]CURRent:DC:APERture
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]CURRent:DC:APERture {<time>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:DC:APERture? [{(@<ch_list>)|MIN|MAX}]

Description
This command enables the aperture mode and sets the integration time
in seconds (called aperture time) for DC current measurements on the
specified channels. If you omit the optional <ch_list> parameter, this
command applies to the currently defined scan list.
You should use this command only when you want
precise control of the integration time of the internal
DMM. Otherwise, specifying integration time using
NPLC (see [SENSe:]CURRent[:DC]:NPLC command)
executes faster and offers better power line noise
rejection characteristics for values of NPLC greater
than 1.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module (channels 21
and 22 only)

Parameters
Name Type Range of Values Default
Value
<time> Numeric Desired aperture time in Aperture
seconds between 400 µs disabled.
and 1 second, with 4 µs
resolution. MIN = 400 µs,
MAX = 1 second
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@321) - channel 21 on
parameter,
the module in slot 300.
this
command
(@221:222) - channels
applies to
21 through 22 on the
the
module in slot 200.
currently
defined
(@121:122,222,321:322)
scan list.
- channels 21 and 22 on
the module in slot 100,
channel 22 on the
module in slot 200, and
channels 21-22 on the
module in slot 300.
Note that the channels
must be of the form s21
and s22, where s is the
first digit of the slot
number.

Remarks
For the <seconds> parameter, you can substitute MIN or MAX for
a numeric value. MIN selects the smallest value accepted, which
gives the lowest resolution; MAX selects the largest value
accepted, which gives the highest resolution.
Only the integral number of power line cycles (1, 2, 10, 20, 100, or
200 PLCs) provide normal mode (line frequency noise) rejection.
The CONFigure, MEASure?, [SENSe:]CURRent[:DC]:NPLC,
[SENSe:]CURRent[:DC]:RESolution commands automatically
disable the aperture mode (these commands select an integration
time in NPLCs).
The aperture mode is disabled after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns the aperture time in the form "+1.00000000E-01" for
each channel specified. Multiple responses are separated by commas.

Examples
The following command enables the aperture mode and sets the
aperture time to 300 ms on channels 21 and 22 in slot 100.
CURR:DC:APER 300E-03,(@121,122)
The following query returns the aperture time selected on channels 21
and 22 in slot 100.
CURR:DC:APER? (@121,12) CURR:DC:APER:ENAB? !Verify
that aperture mode is enabled ("1")
Typical Response: +3.00000000E-01,+3.00000000E-01

See Also
SENSe Subsystem Introduction
CONFigure:CURRent:DC
[SENSe:]CURRent:DC:NPLC

[SENSe:]CURRent:DC:NPLC
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]CURRent:DC:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:DC:NPLC? [{(@<ch_list>)|MIN|MAX}]

Description
This command sets the integration time in number of power line cycles
(PLCs) on the specified channels.Integration time affects the
measurement resolution (for better resolution, use a longer integration
time) and measurement speed (for faster measurements, use a shorter
integration time).If you omit the optional <ch_list> parameter, this
command applies to the currently defined scan list.

Parameters
Name Type Range of Values Default
Value
<PLCs> Discrete 0.02|0.2|1|2|10|20|100|200} 1 PLC
MIN = 0.02 PLC, MAX =
200 PLC
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@321) - channel 21 on
parameter,
the module in slot 300.
this
command
(@221:222) - channels
applies to
21 through 22 on the
the
module in slot 200.
currently
defined
(@121:122,222,321:322)
scan list.
- channels 21 and 22 on
the module in slot 100,
channel 22 on the
module in slot 200, and
channels 21-22 on the
module in slot 300.
Note that the channels
must be of the form s21
and s22, where s is the
first digit of the slot
number.

Remarks
Only	the	integral	number	of	power	line	cycles	(1,	2,	10,	20,	100,	or
200	PLCs)	provide	normal	mode	(line	frequency	noise)	rejection.
Setting	the	resolution	also	sets	the	integration	time	for	the
measurement.	The	following	table	shows	the	relationship	between
integration	time,	measurement	resolution,	number	of	digits,	and
number	of	bits.
| Integration | Resolution | Digits Bits |
| ----------- | ---------- | ----------- |
Time
| 0.02	PLC | <0.0001	x   | 4½ 15  |
| -------- | ----------- | ------ |
|          | Range       | Digits |
| 0.2	PLC  | <0.00001	x  | 5½ 18  |
|          | Range       | Digits |
| 1	PLC    | <0.000003	x | 5½ 20  |
|          | Range       | Digits |
| 2	PLC    | <0.0000022  | 6½ 21  |
|          | x	Range     | Digits |
| 10	PLC   | <0.000001	x | 6½ 24  |
|          | Range       | Digits |
| 20	PLC   | <0.0000008  | 6½ 25  |
|          | x	Range     | Digits |
| 100	PLC  | <0.0000003  | 6½ 26  |
|          | x	Range     | Digits |
| 200	PLC  | <0.00000022 | 6½ 26  |
|          | x	Range     | Digits |
The	NPLC	command	automatically	specifies
[SENSe:]ZERO:AUTO	as	OFF	for	0.02	to	0.2	PLCs	and	as	ON	for
1	PLC	or	more.

The specified integration time is used for all measurements on the
selected channels. If you have applied Mx+B scaling or have
assigned alarms to the selected channel, those measurements are
also made using the specified integration time. Measurements
taken during the Monitor function also use the specified integration
time.
You can also set the integration time by specifying an aperture
time (see [SENSe:]CURRent[:DC]:APERture command). However,
note that specifying integration time using NPLCs executes faster
and offers better noise rejection characteristics for values of NPLC
greater than 1.
The CONFigure, MEASure?, [SENSe:]CURRent[:DC]:NPLC,
[SENSe:]CURRent[:DC]:RESolution commands automatically
disable the aperture mode (these commands select an integration
time in NPLCs).
The instrument sets the integration time to 1 PLC after a Factory
Reset (*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns the integration time in the form "+1.00000000E+00"
for each channel specified. Multiple responses are separated by
commas.

Examples
The following command set the integration time to 0.2 PLCs on channels
21 and 22 in slot 100.
CURR:DC:NPLC 0.2,(@121,122)
The following query returns the integration time settings on channels 21
and 22 in slot 100.
CURR:DC:NPLC? (@121,122)
Typical Response: +2.00000000E-01,+2.00000000E-01

See Also
SENSe Subsystem Introduction
CONFigure:CURRent:DC
[SENSe:]CURRent:DC:APERture
[SENSe:]CURRent:DC:RESolution

[SENSe:]DIGital:DATA:{BYTE|WORD}?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]DIGital:DATA:{BYTE|WORD}? (@<ch_list>)

Description
This query configures the specified channels as inputs and reads an 8-
bit byte or a 16-bit word digital pattern from the specified digital input
channels.

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <ch_list> | Channel |     | This	is	a |
| --------- | ------- | --- | --------- |
One	or	more	digital
|     | List |                  | required   |
| --- | ---- | ---------------- | ---------- |
|     |      | I/O	channels,	as | parameter. |
shown:
(@301)	-	channel	01
on	the	module	in	slot
300.
(@101:102,201,302)
-	channels	01	and
02	on	the	modules
on	slot	100,	channel
01	on	the	module	in
slot	200,	and
channel	02	on	the
module	in	slot	300.

Remarks
To read both ports simultaneously (WORD), you must send the
command to port 01 (LSB) and neither port can be included in the
scan list.
The digital input channels are numbered "s01" (LSB) and "s02"
(MSB), where s is the first digit of the slot number.

Return Format
The output from this command is affected by the FORMat:READing
commands.

Examples
The following command reads the value on channel 02 of the module in
slot 100.
[SENSe:]DIGital:DATA:BYTE? (@102)
Typical Response: +100
The following command reads the value on channels 01 and 02 of the
module in slot 200.
[SENSe:]DIGital:DATA:WORD? (@201)
Typical Response: +32103

See Also
SENSe Subsystem Introduction

[SENSe:]FREQuency:APERture
[SENSe:]PERiod:APERture
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]FREQuency:APERture {<seconds>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]FREQuency:APERture? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]PERiod:APERture {<seconds>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]PERiod:APERture? [{(@<ch_list>)|MIN|MAX}]

Description
These commands select the aperture time (also called gate time) for
frequency and period measurements on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<seconds> Discrete 100 ms
Desired gate time in
seconds:
10 ms (4½ digits, MIN)
100 ms (5½ digits)
1 second (6½ digits,
MAX)
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
For the <seconds> parameter, you can substitute MIN or MAX for
a numeric value. MIN selects the smallest value accepted, which
gives the lowest resolution; MAX selects the largest value
accepted, which gives the highest resolution.
Because frequency and period are related functions, changing a
measurement parameter for one function will also change the
corresponding parameter for the other function.
The instrument sets the aperture time to 100 ms after a Factory
Reset (*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns the aperture time in the form "+1.00000000E-01" for
each channel specified. Multiple responses are separated by commas.

Examples
The following command sets the gate time to 10 ms on channels 03 and
13 in slot 100.
You can substitute the node name PERiod where the node name FREQ
appears below.
FREQ:APER 10E-03,(@103,113)
The following query returns the gate time selected on channels 03 and
13 in slot 100.
FREQ:APER? (@103,113)
Typical Response: +1.00000000E-02,+1.00000000E-02

See Also
SENSe Subsystem Introduction
CONFigure:FREQuency
CONFigure:PERiod

[SENSe:]FREQuency:RANGe:LOWer
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]FREQuency:RANGe:LOWer {<frequency>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]FREQuency:RANGe:LOWer? [{(@<ch_list>)|MIN|MAX}]

Description
The instrument uses three different timeout ranges for frequency
measurements. The instrument selects the slow (3 Hz), medium (20 Hz),
or fast (200 Hz) measurement timeout based on the input frequency that
you specify with this command for the selected channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <frequency> | Numeric | An	integer	from	3	to | This	is	a |
| ----------- | ------- | -------------------- | --------- |
|             |         | 300,000.             | required  |
parameter.
| <ch_list> | Channel |                       | If	you   |
| --------- | ------- | --------------------- | -------- |
|           | List    | One	or	more	channels, | omit	the |
as	shown:
optional
<ch_list>
|     |     | (@310)	-	channel	10	on | parameter, |
| --- | --- | ---------------------- | ---------- |
the	module	in	slot	300.
this
command
(@305:310)	-	channels
applies	to
05	through	10	on	the
the
module	in	slot	300.
currently
defined
(@202:207,209,302:308)
scan	list.
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
Applies to frequency measurements only.
For the <frequency> parameter, specify the lowest frequency
expected in the input signal on the specified channels. The
instrument selects the appropriate measurement timeout based on
the frequency you specify. Attempts to measure frequencies below
the specified limit may falsely return a value of 0.
Input Frequency Timeout
3 Hz to 300 kHz 1 second
(Slow)
20 Hz to 300 kHz 100 ms
(Medium)
200 Hz to 300 kHz 10 ms
(Fast)
The CONFigure and MEASure? commands automatically select
the 20 Hz (medium) timeout.
The instrument selects the medium timeout (20 Hz) after a Factory
Reset (*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns 3.0000000 (slow), 2.0000000E+1 (medium), or
2.0000000E+2 (fast).

Examples
For each of the commands shown below, you could use the node name
PERiod in place of the FREQ node name.
The following command selects the slow filter (3 Hz).
FREQ:RANG:LOW 3
The following query returns the timeout setting.
FREQ:RANG:LOW?
Typical Response: 3.0000000

See Also
SENSe Subsystem Introduction
CONFigure:FREQuency
CONFigure:PERiod

[SENSe:]FREQuency:VOLTage:RANGe
[SENSe:]PERiod:VOLTage:RANGe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]FREQuency:VOLTage:RANGe {<range>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]FREQuency:VOLTage:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]PERiod:VOLTage:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]PERiod:VOLTage:RANGe? [{(@<ch_list>)|MIN|MAX}]

Description
These commands select the voltage range for frequency and period
measurements on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<range> Discrete This is a
Desired range in volts: required
parameter.
100 mV (MIN)
1 V
10 V
100 V
1000 V (MAX)
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Selecting a discrete range will disable autoranging on the specified
channels.
If the input signal is greater than can be measured on the selected
range (manual ranging), the instrument gives an overload
indication: "±OVLD" from the front panel or "±9.9E+37" from the
remote interface.
The CONFigure and MEASure? commands automatically enable
autoranging if the first parameter is AUTO, DEF or omitted.
Because frequency and period are related functions, changing a
measurement parameter for one function will also change the
corresponding parameter for the other function.
The instrument enables autoranging after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns the voltage range in the form "+1.00000000E+01".

Examples
The following command selects the 10 volt range for frequency
measurements.
FREQ:VOLT:RANG 10
The following query returns the voltage range selected.
FREQ:VOLT:RANG?
Typical Response: +1.00000000E+01

See Also
SENSe Subsystem Introduction
CONFigure:FREQuency
CONFigure:PERiod
[SENSe:]FREQuency:VOLTage:RANGe:AUTO
[SENSe:]PERiod:VOLTage:RANGe:AUTO

[SENSe:]FREQuency:VOLTage:RANGe:AUTO
[SENSe:]PERiod:VOLTage:RANGe:AUTO
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]FREQuency:VOLTage:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]FREQuency:VOLTage:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]PERiod:VOLTage:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]PERiod:VOLTage:RANGe:AUTO? [(@<ch_list>)]

Description
These commands disable or enable voltage autoranging for frequency
and period measurements on the specified channels. Autoranging is
convenient because the instrument automatically selects the range for
each measurement based on the input signal detected.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<mode> Boolean {OFF|0|ON|1} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Autorange thresholds:
Down range at: <10% of range
Up range at: >120% of range
With autoranging enabled, the instrument selects one of the
following ranges based on the input signal detected:
100mV
1 V
10 V
100 V
300 V
Selecting a discrete range (see
[SENSe:]FREQuency:VOLTage:RANGe command) will disable
autoranging on the specified channels.
The CONFigure and MEASure? commands automatically enable
autoranging if the first parameter is AUTO, DEF or omitted.
Because frequency and period are related functions, changing a
measurement parameter for one function will also change the
corresponding parameter for the other function
The instrument enables autoranging after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command disables autoranging.
FREQ:VOLT:RANG:AUTO OFF
The following query returns the autoranging setting.
FREQ:VOLT:RANG:AUTO?
Typical Response: 0

See Also
SENSe Subsystem Introduction
CONFigure:FREQuency
CONFigure:PERiod
[SENSe:]FREQuency:VOLTage:RANGe
[SENSe:]PERiod:VOLTage:RANGe

[SENSe:]RESistance:APERture
[SENSe:]FRESistance:APERture
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]RESistance:APERture {<time>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]RESistance:APERture? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FRESistance:APERture {<time>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]FRESistance:APERture? [{(@<ch_list>)|MIN|MAX}]

Description
These commands enable the aperture mode and set the integration time
(<aperture_time>) in seconds for 2-wire (RESistance) and 4-wire
(FRESistance) resistance measurements on the specified channels.
You should use this command only when you want precise
control of the integration time of the internal DMM.
Otherwise, specifying integration time using NPLC (see
[SENSe:]RESistance:NPLC command) executes faster and
offers better power line noise rejection characteristics for
values of NPLC greater than 1.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module
(RESistance only; not FRESistance)

Parameters
| Name            | Type    | Range	of	Values           | Default	Value |
| --------------- | ------- | ------------------------- | ------------- |
| <aperture_time> | Numeric | A	number	of	seconds,	from | This	is	a     |
|                 |         | 0.0004	to	4.              | required      |
parameter.You
must	specify
the	time,	or
MIN	or	MAX.
| <ch_list> | Channel |                       | If	you	omit  |
| --------- | ------- | --------------------- | ------------ |
|           | List    | One	or	more	channels, | the	optional |
|           |         | as	shown:             | <ch_list>    |
parameter,	this
(@310)	-	channel	10	on
command
the	module	in	slot	300.
applies	to	the
currently
(@305:310)	-	channels
defined	scan
05	through	10	on	the
list.
module	in	slot	300.
(@202:207,209,302:308)
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
For the <seconds> parameter, you can substitute MIN or MAX for
a numeric value. MIN selects the smallest value accepted, which
gives the lowest resolution; MAX selects the largest value
accepted, which gives the highest resolution.
Because 2-wire and 4-wire resistance are related functions,
changing a measurement parameter for one function will also
change the corresponding parameter for the other function (see
[SENSe:]FRESistance:APERture command).
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
Only the integral number of power line cycles (1, 2, 10, 20, 100, or
200 PLCs) provide normal mode (line frequency noise) rejection.
The CONFigure, MEASure?, [SENSe:]RESistance:NPLC,
[SENSe:]RESistance:RESolution, [SENSe:]FRESistance:NPLC,
and [SENSe:]FRESistance:RESolution commands disable the
aperture mode (these commands select an integration time in
number of power line cycles).
The aperture mode is disabled after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns the aperture time in the form "+1.00000000E-01" for
each channel specified. Multiple responses are separated by commas.

Examples
In each of the following examples, you could replace the node name
FRES with RESistance.
The following command enables the aperture mode and sets the
aperture time to 300 ms on channels 03 and 13 in slot 100. For this 4-
wire measurement, the instrument automatically pairs these channels in
Bank 1 with the corresponding channels in Bank 2.
FRES:APER 300E-03,(@103,113)
The following query returns the aperture time selected on channels 03
and 13 in slot 100.
FRES:APER? (@103,113)
FRES:APER:ENAB? !Verify that aperture mode is
enabled ("1")
Typical Response: +3.00000000E-01,+3.00000000E-01

See Also
SENSe Subsystem Introduction
CONFigure:FRESistance
CONFigure:RESistance
[SENSe:]FRESistance:NPLC
[SENSe:]RESistance:NPLC

[SENSe:]RESistance:NPLC
[SENSe:]FRESistance:NPLC
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]RESistance:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]RESistance:NPLC? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FRESistance:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]FRESistance:NPLC? [{(@<ch_list>)|MIN|MAX}]

Description
These commands set the integration time in number of power line cycles
(PLCs) on the specified channels. Integration time affects the
measurement resolution (for better resolution, use a longer integration
time) and measurement speed (for faster measurements, use a shorter
integration time).
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module
(RESistance only; not FRESistance)

Parameters
Name Type Range of Values Default
Value
<PLCs> Discrete {0.02|0.2|1|2|10|20|100|200|MIN|MAX} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, as shown: omit the
optional
(@310) - channel 10 on the module
<ch_list>
in slot 300.
parameter,
this
(@305:310) - channels 05 through
command
10 on the module in slot 300.
applies to
the
(@202:207,209,302:308) - channels
currently
02 through 07 and 09 on the
defined
module in slot 200 and channels 02
scan list.
through 08 on the module in slot
300.

Remarks
Only	the	integral	number	of	power	line	cycles	(1,	2,	10,	20,	100,	or
200	PLCs)	provide	normal	mode	(line	frequency	noise)	rejection.
Because	2-wire	and	4-wire	resistance	are	related	functions,
changing	a	measurement	parameter	for	one	function	will	also
change	the	corresponding	parameter	for	the	other	function	.
For	4-wire	resistance	measurements,	the	instrument	automatically
pairs	channel	n	in	Bank	1	with	channel	n+10	in	Bank	2	(34901A)
or	n+8	(34902A)	to	provide	the	source	and	sense	connections.	For
example,	make	the	source	connections	to	the	HI	and	LO	terminals
on	channel	02	in	Bank	1	and	the	sense	connections	to	the	HI	and
LO	terminals	on	channel	12	(34901A)	or	10	(34902A)	in	Bank
2.Specify	the	paired	channel	in	Bank	1	(source)	as	the	<ch_list>
channel	(channels	in	Bank	2	are	not	allowed	in	the	<ch_list>).
Setting	the	resolution	also	sets	the	integration	time	for	the
measurement.	The	following	table	shows	the	relationship	between
integration	time,	measurement	resolution,	number	of	digits,	and
number	of	bits.
| Integration | Resolution | Digits Bits |
| ----------- | ---------- | ----------- |
Time
| 0.02	PLC | <0.0001	x   | 4½ 15  |
| -------- | ----------- | ------ |
|          | Range       | Digits |
| 0.2	PLC  | <0.00001	x  | 5½ 18  |
|          | Range       | Digits |
| 1	PLC    | <0.000003	x | 5½ 20  |
|          | Range       | Digits |
| 2	PLC    | <0.0000022  | 6½ 21  |
|          | x	Range     | Digits |
| 10	PLC   | <0.000001	x | 6½ 24  |

|         | Range       | Digits |
| ------- | ----------- | ------ |
| 20	PLC  | <0.0000008  | 6½ 25  |
|         | x	Range     | Digits |
| 100	PLC | <0.0000003  | 6½ 26  |
|         | x	Range     | Digits |
| 200	PLC | <0.00000022 | 6½ 26  |
|         | x	Range     | Digits |
The	specified	integration	time	is	used	for	all	measurements	on	the
selected	channels.	If	you	have	applied	Mx+B	scaling	or	have
assigned	alarms	to	the	selected	channel,	those	measurements	are
also	made	using	the	specified	integration	time.	Measurements
taken	during	the	Monitor	function	also	use	the	specified	integration
time.
You	can	also	set	the	integration	time	by	specifying	an	aperture
time	(see	[SENSe:]RESistance:APERture	command).	However,
note	that	specifying	integration	time	using	NPLCs	executes	faster
and	offers	better	noise	rejection	characteristics	for	values	of	NPLC
greater	than	1.
The	CONFigure,	MEASure?,	[SENSe:]RESistance:NPLC,
[SENSe:]FRESistance:NPLC,	[SENSe:]RESistance:RESolution,
and	[SENSe:]FRESistance:RESolution	commands	disable	the
aperture	mode	(these	commands	select	an	integration	time	in
number	of	power	line	cycles).
The	instrument	sets	the	integration	time	to	1	PLC	after	a	Factory
Reset	(*RST	command).	An	Instrument	Preset	(SYSTem:PRESet
command)	or	Card	Reset	(SYSTem:CPON	command)	does	not
change	the	setting.

Return Format
The query returns the integration time in the form "+1.00000000E+00"
for each channel specified. Multiple responses are separated by
commas.

Examples
In each of the following examples, you could replace the node name
FRES with RESistance.
The following command set the integration time to 0.2 PLCs on channels
03 and 13 in slot 100. For this 4-wire measurement, the instrument
automatically pairs these channels in Bank 1 with the corresponding
channels in Bank 2.
FRES:NPLC 0.2,(@103,113)
The following query returns the integration time settings on channels 03
and 13 in slot 100.
FRES:NPLC? (@103,113)
FRES:APER:ENAB? !Verify that aperture mode is
disabled ("0")
Typical Response: +2.00000000E-01,+2.00000000E-01

See Also
SENSe Subsystem Introduction
[SENSe:]RESistance:APERture
[SENSe:]FRESistance:APERture
[SENSe:]RESistance:RESolution
[SENSe:]FRESistance:RESolution

[SENSe:]RESistance:OCOMpensated
[SENSe:]FRESistance:OCOMpensated
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
[SENSe:]RESistance:OCOMpensated <state>[,(@<ch_list>)]
[SENSe:]RESistance:OCOMpensated? [(@<ch_list>)]
[SENSe:]FRESistance:OCOMpensated <state>[,(@<ch_list>)]
[SENSe:]FRESistance:OCOMpensated? [(@<ch_list>)]

Description
Offset compensation removes the effects of any DC voltages in the
circuit being measured. The technique involves taking the difference
between two resistance measurements on the specified channels, one
with the current source turned on and one with the current source turned
off.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module
(RESistance only; not FRESistance)

Parameters
Name Type Range of Values Default
Value
<state> Boolean {OFF|0|ON|1} This is a
required
parameter.
The
factory
default
value is
OFF.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Turning offset compensation on will double measurement time.
Once enabled, offset compensation is applied to both 2-wire and
4-wire resistance measurements on the specified channels.
Because 2-wire and 4-wire resistance are related functions,
changing a measurement parameter for one function will also
change the corresponding parameter for the other function .
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
The CONFigure and MEASure? commands automatically disable
offset compensation.
The instrument disables offset compensation after a Factory Reset
(*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns 0 (OFF) or 1 (ON) for each channel specified. Multiple
responses are separated by commas.

Examples
In each of the following examples, you can replace the node name
RES with FRES.
The following command enables offset compensation on channels 3 and
13 in slot 100.
RES:OCOM ON,(@103,113)
The following query returns the offset compensation settings on channels
03 and 13 in slot 100.
RES:OCOM? (@103,113)
Typical Response: 1,1

See Also
SENSe Subsystem Introduction
CONFigure:RESistance
CONFigure:RESistance

[SENSe:]RESistance:RANGe
[SENSe:]FRESistance:RANGe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]RESistance:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]RESistance:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FRESistance:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]FRESistance:RANGe? [{(@<ch_list>)|MIN|MAX}]

Description
This command selects the measurement range for 2-wire (RESistance)
and 4-wire (FRESistance) resistance measurements on the specified
channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module
(RESistance only; not FRESistance)

Parameters
Name Type Range of Values Default
Value
<range> Discrete This is a
Desired range in ohms: required
parameter.
100Ω (MIN)
1 kΩ
10 kΩ
100 kΩ
1 MΩ
10 MΩ
100 MΩ (MAX)
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Selecting a discrete range will disable autoranging on the specified
channels (see [SENSe:]RESistance:RANGe:AUTO command).
Because 2-wire and 4-wire resistance are related functions,
changing a measurement parameter for one function will also
change the corresponding parameter for the other function (see
[SENSe:]RESistance:RANGe command).
The CONFigure and MEASure? commands automatically enable
autoranging if the first parameter is AUTO, DEF or omitted.
If the input signal is greater than can be measured on the selected
range (manual ranging), the instrument gives an overload
indication: "±OVLD" from the front panel or "±9.9E+37" from the
remote interface.
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
The instrument enables autoranging after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns the range in the form "+1.00000000E+03" for each
channel specified. Multiple responses are separated by commas.

Examples
In the following examples, you can susbstitute the node name RES for
FRES.
The following command selects the 10 kΩ range on channels 03 and 13
in slot 100. For this 4-wire measurement, the instrument automatically
pairs these channels in Bank 1 with the corresponding channels in Bank
2.
FRES:RANG 10E+3,(@103,113)
The following query returns the range selected on channels 03 and 13 in
slot 100.
FRES:RANG? (@103,113)
Typical Response: +1.00000000E+04,+1.00000000E+04

See Also
SENSe Subsystem Introduction
CONFigure:FRESistance
CONFigure:RESistance
[SENSe:]FRESistance:RANGe:AUTO
[SENSe:]RESistance:RANGe:AUTO

[SENSe:]RESistance:RANGe:AUTO
[SENSe:]FRESistance:RANGe:AUTO
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]RESistance:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]RESistance:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]FRESistance:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]FRESistance:RANGe:AUTO? [(@<ch_list>)]

Description
This command disables or enables autoranging for 2-wire (RESistance)
or 4-wire (FRESistance) resistance measurements on the specified
channels. Autoranging is convenient because the instrument
automatically selects the range for each measurement based on the
input signal detected.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module
(RESistance only; not FRESistance)

Parameters
Name Type Range of Values Default
Value
<state> Boolean {OFF|0|ON|1} This is a
required
parameter.
The
factory
default
value is
ON.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
Because 2-wire and 4-wire resistance are related functions,
changing a measurement parameter for one function will also
change the corresponding parameter for the other function .
Autorange thresholds:
Down range at: <10% of range
Up range at: >120% of range
With autoranging enabled, the instrument selects one of the
following ranges based on the input signal detected:
100Ω
1 kΩ
10 kΩ
100 kΩ
1 MΩ
10 MΩ
100 MΩ
Selecting a discrete range (see [SENSe:]RESistance:RANGe
command) will disable autoranging on the specified channels.
The CONFigure and MEASure? commands automatically enable
autoranging if the first parameter is AUTO, DEF or omitted.
The instrument enables autoranging after a Factory Reset (*RST

command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns 0 (OFF) or 1 (ON) for each channel specified. Multiple
responses are separated by commas.

Examples
In the following examples, you can substitute the node name RES for
FRES.
The following command disables autoranging on channels 03 and 13 in
slot 100. For this 4-wire measurement, the instrument automatically pairs
these channels in Bank 1 with the corresponding channels in Bank 2.
FRES:RANG:AUTO OFF,(@103,113)
The following query returns the autoranging settings on channels 03 and
13 in slot 100.
FRES:RANG:AUTO? (@103,113)
Typical Response: 0,0

See Also
SENSe Subsystem Introduction
CONFigure:FRESistance
CONFigure:RESistance
[SENSe:]FRESistance:RANGe
[SENSe:]RESistance:RANGe

[SENSe:]RESistance:RESolution
[SENSe:]FRESistance:RESolution
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]RESistance:RESolution {<resolution>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]RESistance:RESolution? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FRESistance:RESolution {<resolution>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]FRESistance:RESolution? [{(@<ch_list>)|MIN|MAX}]

Description
These commands select the measurement resolution for 2-wire
(RESistance) and 4-wire (FRESistance) resistance measurements on
the specified channels. Specify the resolution in the same units as the
selected measurement function, not in number of digits.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module
(RESistance only; not FRESistance)

Parameters
Name Type Range of Values Default
Value
<resolution> Numeric Desired resolution in ohms 0.000003
x Range
(1 PLC)
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
For the <resolution> parameter, you can substitute MIN or MAX for
a numeric value. MIN selects the smallest value accepted, which
gives the highest resolution; MAX selects the largest value
accepted, which gives the least resolution.
The instrument will dispatch a settings conflict error if you issue
this command when[SENSe:]CURRent:DC:RANGe:AUTO is ON
for one or more of the specified channels.
Because 2-wire and 4-wire resistance are related functions,
changing a measurement parameter for one function will also
change the corresponding parameter for the other function.
Setting the resolution also sets the integration time for the
measurement. The following table shows the relationship between
integration time, measurement resolution, number of digits, and
number of bits.
Integration Resolution Digits Bits
Time
0.02 PLC <0.0001 x 4½ 15
Range Digits
0.2 PLC <0.00001 x 5½ 18
Range Digits

| 1	PLC   | <0.000003	x | 5½ 20  |
| ------- | ----------- | ------ |
|         | Range       | Digits |
| 2	PLC   | <0.0000022  | 6½ 21  |
|         | x	Range     | Digits |
| 10	PLC  | <0.000001	x | 6½ 24  |
|         | Range       | Digits |
| 20	PLC  | <0.0000008  | 6½ 25  |
|         | x	Range     | Digits |
| 100	PLC | <0.0000003  | 6½ 26  |
|         | x	Range     | Digits |
| 200	PLC | <0.00000022 | 6½ 26  |
|         | x	Range     | Digits |
You	can	also	set	the	integration	time	by	specifying	an	aperture
time	(see	[SENSe:]RESistance:APERture	command).	However,
note	that	specifying	integration	time	using	NPLCs	executes	faster
and	offers	better	noise	rejection	characteristics	for	values	of	NPLC
greater	than	1.
The	CONFigure,	MEASure?,	[SENSe:]RESistance:NPLC,
[SENSe:]RESistance:NPLC,	[SENSe:]RESistance:RESolution,
and	[SENSe:]FRESistance:RESolution	commands	disable	the
aperture	mode	(these	commands	select	an	integration	time	in
number	of	power	line	cycles).
The	instrument	sets	the	resolution	to	1	PLC	after	a	Factory	Reset
(*RST	command).	An	Instrument	Preset	(SYSTem:PRESet
command)	or	Card	Reset	(SYSTem:CPON	command)	does	not
change	the	setting.

Return Format
The query returns the resolution in the form "+1.00000000E+02" for each
channel specified. Multiple responses are separated by commas.

Examples
In the following commands, you can substitute the node name
RES:FRES for RES:RES.
The following command sets the measurement resolution to 100Ω on
channels 03 and 13 in slot 100.
RES:RES 100,(@103,113)
The following query returns the resolution selected on channels 03 and
13 in slot 100.
RES:RES? (@103,113)
RES:APER:ENAB? !Verify that aperture mode is
disabled ("0")
Typical Response: +1.00000000E+02,+1.00000000E+02

See Also
SENSe Subsystem Introduction
CONFigure:FRESistance
CONFigure:RESistance
[SENSe:]FRESistance:APERture
[SENSe:]RESistance:APERture
[SENSe:]FRESistance:NPLC
[SENSe:]RESistance:NPLC

[SENSe:]FUNCtion
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]FUNCtion "<function>"[,(@<ch_list>)]
[SENSe:]FUNCtion? [(@<ch_list>)]

Description
Select the measurement function on the specified channels. The function
name must be enclosed in quotes in the command string (for example,
FUNC "VOLT:DC").

Parameters
Name Type Range of Values Default
Value
<function> Discrete This is a
{TEMPerature | required
VOLTage[:DC] | parameter.
VOLTage:AC |
RESistance |
FRESistance |
CURRent[:DC] |
CURRent:AC |
FREQuency | PERiod}
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
This command is not available on digital cards.
Note that when you change the measurement function on a
channel, all of the other measurement attributes (range, resolution,
etc.) are set to their default values.
You cannot set any function-specific measurement attributes
unless the channel is already configured for that function. For
example, you cannot set the AC filter unless that channel is
already configured for AC voltage or AC current measurements.

Return Format
The query returns a quoted string indicating the short form of the function
name (example: "VOLT") on each channel. Multiple channels are
separated by commas.

Examples
The following commands specify functions for the channels shown.
FUNC "TEMPerature",(@301)
FUNC "FREQuency",(@204)
The following query returns the functions specified for the channels
shown.
FUNC? (@204,301)
Typical response: "FREQ","TEMP"

See Also
SENSe Subsystem Introduction

[SENSe:]TEMPerature:APERture
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:APERture {<seconds>|MIN|MAX|DEF} [,
(@<ch_list>)]
[SENSe:]TEMPerature:APERture? [{(@<ch_list>)|MIN|MAX}]

Description
This	command	enables	the	aperture	mode	and	sets	the	integration	time
in	seconds	(called	aperture	time)	for	temperature	measurements	on	the
specified	channels.
You	should	use	this	command	only
when	you	want	precise	control	of	the
integration	time	of	the	internal	DMM.
Otherwise,	specifying	integration	time
using	NPLC	(see
[SENSe:]TEMPerature:NPLC
command)	executes	faster	and	offers
better	noise	rejection	characteristics
for	values	of	NPLC	greater	than	1.

The	following	table	shows	which	temperature	transducers	are	supported
by	each	of	the	multiplexer	modules.
| Module | Thermocouple | RTD RTD | Thermistor |
| ------ | ------------ | ------- | ---------- |
|        |              | 2- 4-   |            |
Wire Wire
|     | Yes | Yes Yes | Yes |
| --- | --- | ------- | --- |
34901A
Armature
Multiplexer
| 34902A | Yes | Yes Yes | Yes |
| ------ | --- | ------- | --- |
Reed
Multiplexer
| 34908A   | Not          | Yes No | Yes |
| -------- | ------------ | ------ | --- |
| Armature | Recommended1 |        |     |

Multiplexer
(1-Wire)
1
With a one-wire multiplexer, even very small ground currents can
introduce substantial measurement error.

Parameters
| Name      | Type    | Range	of | Default   |
| --------- | ------- | -------- | --------- |
|           |         | Values   | Value     |
| <seconds> | Numeric | Desired  | Aperture  |
|           |         | aperture | disabled. |
time	in
seconds
between
400	µs	and
1	second,
with	4	µs
resolution.
MIN	=
400	µs,
MAX	=	1
second
| <ch_list> | Numeric | One	or	more | If	<ch_list> |
| --------- | ------- | ----------- | ------------ |
|           |         | channels	in | is	omitted,  |
|           |         | the	form    | this         |
|           |         | (@scc).     | command      |
applies	to
the	current
scan	list.

Remarks
For the <seconds> parameter, you can substitute MIN or MAX for
a numeric value. MIN selects the smallest value accepted, which
gives the lowest resolution; MAX selects the largest value
accepted, which gives the highest resolution.
Only the integral number of power line cycles (1, 2, 10, 20, 100, or
200 PLCs) provide normal mode (line frequency noise) rejection.
The CONFigure, MEASure?, and [SENSe:]TEMPerature:NPLC
commands disable the aperture mode (these commands select an
integration time in number of power line cycles).
The aperture mode is disabled after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query command returns the aperture time in the form
"+1.00000000E-01" for each channel specified. Multiple responses are
separated by commas.

Examples
The following command enables the aperture mode and sets the
aperture time to 400 ms on channels 03 and 13 in slot 100.
TEMP:APER 400E-03,(@103,113)
The following query returns the aperture time selected on channels 03
and 13 in slot 100.
TEMP:APER? (@103,113)
Typical response: +4.00000000E-01,+4.00000000E-01

See Also
SENSe Subsystem Introduction
CONFigure:TEMPerature
[SENSe:]TEMPerature:NPLC

[SENSe:]TEMPerature:NPLC
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]TEMPerature:NPLC? [{(@<ch_list>)|MIN|MAX}]

Description
This	command	sets	the	integration	time	in	number	of	power	line	cycles
(PLCs)	on	the	specified	channels.Integration	time	affects	the
measurement	resolution	(for	better	resolution,	use	a	longer	integration
time)	and	measurement	speed	(for	faster	measurements,	use	a	shorter
integration	time).
The	following	table	shows	which	temperature	transducers	are	supported
by	each	of	the	multiplexer	modules.
| Module | Thermocouple | RTD RTD | Thermistor |
| ------ | ------------ | ------- | ---------- |
|        |              | 2- 4-   |            |
Wire Wire
|     | Yes | Yes Yes | Yes |
| --- | --- | ------- | --- |
34901A
Armature
Multiplexer
| 34902A | Yes | Yes Yes | Yes |
| ------ | --- | ------- | --- |
Reed
Multiplexer
| 34908A   | Not          | Yes No | Yes |
| -------- | ------------ | ------ | --- |
| Armature | Recommended1 |        |     |
Multiplexer
(1-Wire)
1
With	a	one-wire	multiplexer,	even	very	small	ground	currents	can
introduce	substantial	measurement	error.

Parameters
Name Type Range of Values Default
Value
<PLCs> Discrete {0.02|0.2|1|2|10|20|100|200} 1 PLC
MIN = 0.02 PLC, MAX =
200 PLC
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the module
in slot 300.

Remarks
Only	the	integral	number	of	power	line	cycles	(1,	2,	10,	20,	100,	or
200	PLCs)	provide	normal	mode	(line	frequency	noise)	rejection.
Setting	the	resolution	also	sets	the	integration	time	for	the
measurement.	The	following	table	shows	the	relationship	between
integration	time,	measurement	resolution,	number	of	digits,	and
number	of	bits.
| Integration | Resolution | Digits Bits |
| ----------- | ---------- | ----------- |
Time
| 0.02	PLC | <0.0001	x   | 4½ 15  |
| -------- | ----------- | ------ |
|          | Range       | Digits |
| 0.2	PLC  | <0.00001	x  | 5½ 18  |
|          | Range       | Digits |
| 1	PLC    | <0.000003	x | 5½ 20  |
|          | Range       | Digits |
| 2	PLC    | <0.0000022  | 6½ 21  |
|          | x	Range     | Digits |
| 10	PLC   | <0.000001	x | 6½ 24  |
|          | Range       | Digits |
| 20	PLC   | <0.0000008  | 6½ 25  |
|          | x	Range     | Digits |
| 100	PLC  | <0.0000003  | 6½ 26  |
|          | x	Range     | Digits |
| 200	PLC  | <0.00000022 | 6½ 26  |
|          | x	Range     | Digits |
The	specified	integration	time	is	used	for	all	measurements	on	the
selected	channels.	If	you	have	applied	Mx+B	scaling	or	have
assigned	alarms	to	the	selected	channel,	those	measurements	are

also made using the specified integration time. Measurements
taken during the Monitor function also use the specified integration
time.
You can also set the integration time by specifying an aperture
time (see [SENSe:]TEMPerature:APERture command). However,
note that specifying integration time using NPLCs executes faster
and offers better noise rejection characteristics for values of NPLC
greater than 1.
The CONFigure, MEASure?, and [SENSe:]TEMPerature:NPLC
commands disable the aperture mode (these commands select an
integration time in number of power line cycles).
The instrument sets the integration time to 1 PLC after a Factory
Reset (*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns the integration time in the form "+1.00000000E+00"
for each channel specified. Multiple responses are separated by
commas.

Examples
The following command set the integration time to 0.2 PLCs on channels
03 and 13 in slot 100.
TEMP:NPLC 0.2,(@103,113)
The following query returns the integration time settings on channels 03
and 13 in slot 100.
TEMP:NPLC? (@103,113)
TEMP:APER:ENAB? !Verify that aperture mode is
disabled ("0")
Typical Response: +2.00000000E-01,+2.00000000E-01

See Also
SENSe Subsystem Introduction
CONFigure:TEMPerature

[SENSe:]TEMPerature:RJUNction?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
[SENSe:]TEMPerature:RJUNction? [(@<ch_list>)]

Description
This query returns he internal reference junction temperature on the
specified channels. This is useful only for an internal reference source).

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
This query returns the reference temperature in degrees Celsius,
regardless of the temperature units currently selected (see
UNIT:TEMPerature command).

Return Format
The query returns a number in the form +2.89753100E+01.

Example
The following query returns the temperature of the internal reference
junction on channels 03, 04, and 05 in slot 200.
TEMP:RJUN? (@203:205) !Always returns result in
degrees Celsius
Typical Response:
+2.35212231E+01,+2.37701293E+01,+2.38291321E+01

See Also
SENSe Subsystem Introduction

[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated
[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated
Syntax| Description | Parameters | Remarks | Return Format | Examples

Syntax
Syntax
[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated <mode> [,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated?
[(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated <mode> [,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated?
[(@<ch_list>)]

Description
Offset compensation removes the effects of any DC voltages in the
circuit being measured. The technique involves taking the difference
between two resistance measurements on the specified channels, one
with the current source turned on and one with the current source turned
off.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module (RTD
only; not FRTD)

Parameters
Name Type Range of Values Default
Value
<mode> Boolean {OFF|0|ON|1} OFF|0
<ch_list> Numeric If
One or more channels,
<ch_list>
as shown:
is
omitted,
(@310) - channel 10 on
this
the module in slot 300.
command
applies to
(@305:310) - channels
the
05 through 10 on the
current
module in slot 300.
scan list.
(@202:207,209,302:308)
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
This command applies only to 2-wire and 4-wire RTD
measurements on the 100Ω, 1 kΩ, and 10 kΩ ranges. Once
enabled, offset compensation is applied to both 2-wire and 4-wire
RTD measurements on the specified channels.
Because 2-wire and 4-wire resistance are related functions,
changing a measurement parameter for one function will also
change the corresponding parameter for the other function.
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
The instrument disables offset compensation after a Factory Reset
(*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query command returns "0" (OFF) or "1" (ON) for each channel
specified. Multiple responses are separated by commas.

Examples
The following command enables offset compensation on channels 3 and
13 in slot 1. For this 4-wire measurement, the instrument automatically
pairs these channels in Bank 1 with the corresponding channels in Bank
2.
TEMP:TRAN:FRTD:OCOM ON,(@103,113)
The following query returns the offset compensation settings on channels
03 and 13 in slot 100.
TEMP:TRAN:FRTD:OCOM? (@103,113)
Typical Response: 1,1

See Also
SENSe Subsystem Introduction
CONFigure:TEMPerature

[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]
<reference>[,(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]?
[(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]
<reference>[,(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]?
[(@<ch_list>)]

Description
The resistance of an RTD is nominal at 0 °C and is referred to as Ro.
These commands select the nominal resistance (Ro) for 2-wire (RTD) or
4-wire (FRTD) measurements on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module (RTD
only; not FRTD)

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <reference> | Numeric | A	number	(of	ohms) | 100 |
| ----------- | ------- | ------------------ | --- |
between	49	and	2100.
| <ch_list> | Channel |                       | If	you   |
| --------- | ------- | --------------------- | -------- |
|           | List    | One	or	more	channels, | omit	the |
|           |         | as	shown:             | optional |
<ch_list>
(@310)	-	channel	10	on
parameter,
|     |     | the	module	in	slot	300. | this |
| --- | --- | ----------------------- | ---- |
command
(@305:310)	-	channels
applies	to
05	through	10	on	the
the
module	in	slot	300.
currently
defined
(@202:207,209,302:308)
scan	list.
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
Because 2-wire and 4-wire resistance are related functions,
changing a measurement parameter for one function will also
change the corresponding parameter for the other function.
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
The instrument sets the nominal resistance to 100Ω after a
Factory Reset (*RST command). An Instrument Preset
(SYSTem:PRESet command) or Card Reset (SYSTem:CPON
command) does not change the setting.

Return Format
The query returns the nominal resistance a value of the form
+1.00000000E+02. Multiple values are separated by commas.

Examples
In each of the following examples, you could substitute the node name
FRTD for RTD.
The following command sets the nominal resistance to 75Ω on channels
01 through 04 in slot 200.
TEMP:TRAN:RTD:RES:REF 75,(@201:204)
The following query returns the reference resistance for the four
channels shown.
TEMP:TRAN:RTD:RES:REF? (@201:204)
Typical Response:
7.50000000E+01,7.50000000E+01,7.50000000E+01,7.50000000E+01

See Also
SENSe Subsystem Introduction

[SENSe:]TEMPerature:TRANsducer:RTD:TYPE
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE <type>[,(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE? [(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE <type>[,(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE? [(@<ch_list>)]

Description
This command selects the RTD type for 2-wire (RTD) or 4-wire (FRTD)
temperature measurements on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module (RTD
only; not FRTD)

Parameters
Name Type Range of Values Default
Value
<type> Discrete {85|91} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
The instrument supports RTDs with Alpha = 0.00385 (DIN/IEC
751) using ITS-90 software conversions or Alpha = 0.00391 using
IPTS-68 software conversions.
"PT100" is a special label that is sometimes used to refer to an
RTD with Alpha = 0.00385 and Ro = 100Ω.
The instrument sets the RTD type to "85" after a Factory Reset
(*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns +85 or +91. Multiple results are separated by
commas.

Examples
In the following examples, you could substitute the node name FRTD for
the node name RTD.
The following command sets the transducer type to 85 on the channels
shown.
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE 85,
(@301:305)
The following query returns the transducer type on the channels shown.
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE?
(@202,204,301:305,308)
Typical Response: +85,+91,+85,+85,+85,+85,+85,+91

See Also
SENSe Subsystem Introduction

[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk <state>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk? [(@<ch_list>)]

Description
This command disables or enables the thermocouple check feature to
verify that your thermocouples are properly connected for
measurements. If you enable this feature, the instrument measures the
channel resistance after each thermocouple measurement to ensure a
proper connection. If an open connection is detected (greater than 5 kΩ
on the 10 kΩ range), the instrument reports an overload condition for that
channel's temperature reading.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<state> Boolean {OFF|0|ON|1} This is a
required
parameter.
The
factory
default is
OFF.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
The instrument disables the thermocouple check feature after a
Factory Reset (*RST command). An Instrument Preset
(SYSTem:PRESet command) or Card Reset (SYSTem:CPON
command) does not change the setting.

Return Format
The query returns 0 (disabled) or 1 (enabled) to indicate the status of
each thermocouple check for the channel list.

Examples
The following command enables the thermocouple check feature for six
channels.
TEMP:TRAN:TCouple:CHEC ON,(@103,104,205-208)
The following query returns the status of the thermocouple check feature
for each of the following channels.
TEMP:TRAN:TCouple:CHEC? (@103,105,203-205,301)
Typical Response: 1,0,0,0,1,0

See Also
SENSe Subsystem Introduction

[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction
{<temperature>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction? [(@<ch_list>)]

Description
This command sets the fixed reference junction temperature in degrees
Celsius for thermocouple measurements on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <temperature> | Numeric | A	number	representing	the | This	is	a  |
| ------------- | ------- | ------------------------- | ---------- |
|               |         | temperature	in	degrees    | required   |
|               |         | Celsius,	from	-20	to	+80. | parameter. |
The
factory
default
value	is	0.
| <ch_list> | Channel |     | If	you |
| --------- | ------- | --- | ------ |
One	or	more	channels,
|     | List |           | omit	the |
| --- | ---- | --------- | -------- |
|     |      | as	shown: | optional |
<ch_list>
(@310)	-	channel	10	on
parameter,
the	module	in	slot	300.
this
command
(@305:310)	-	channels
applies	to
05	through	10	on	the
the
module	in	slot	300.
currently
defined
(@202:207,209,302:308)
scan	list.
-	channels	02	through	07
and	09	on	the	module	in
slot	200	and	channels	02
through	08	on	the
module	in	slot	300.

Remarks
For this command, you must always specify the temperature in
degrees Celsius regardless of the temperature units currently
selected (see UNIT:TEMPerature command).
The instrument sets the thermocouple junction to 0 °C after a
Factory Reset (*RST command). An Instrument Preset
(SYSTem:PRESet command) or Card Reset (SYSTem:CPON
command) does not change the setting.

Return Format
The query returns the fixed reference junction temperature in degrees
Celsius in the form +1.12345678E+01.

Examples
The following command sets the fixed junction temperature in degrees
Celsius for thermocouple measurements on channels 01 through 03 in
slot 100.
TEMPerature:TRANsducer:TCouple:RJUNction 27.3
(@301:303)
The following query returns the fixed junction temperature in degrees
Celsius on the specified channels.
TEMP:TRAN:TC:RJUN? (@301:303)
Typical Response: 2.73000000E+01,2.73000000E+01,2.73000000E+01

See Also
SENSe Subsystem Introduction

[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE <type>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE?
[(@<ch_list>)]

Description
Thermocouple measurements require a reference junction temperature.
For the reference junction temperature, you can use an internal
measurement on the module's terminal block, an external thermistor or
RTD measurement, or a known fixed junction temperature. This
command selects the reference junction source for thermocouple
measurements on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module
(RTD only; not FRTD)

Parameters
Name Type Range of Values Default
Value
<type> Discrete {INTernal|EXTernal|FIXed} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the module
in slot 300.

Remarks
The accuracy of the measurement is highly dependent upon the
thermocouple connections and the type of reference junction used.
Use a fixed temperature reference for the highest accuracy
measurements (you must maintain the known junction
temperature). The internal isothermal block reference requires no
external wiring but provides lower accuracy measurements than a
fixed reference.
To store a reference temperature, first configure channel 1 on a
multiplexer card for an RTD or thermistor measurement (see
CONFigure:TEMPerature command). Then assign the
measurement from that channel as the external reference using
one of the following commands:
[SENSe:]TEMPerature:TRANsducer:FRTD:REFerence
[SENSe:]TEMPerature:TRANsducer:RTD:REFerence
When you initiate a measurement on an external reference
channel (see INITiate or READ? command), subsequent
thermocouple measurements use the stored temperature as their
reference. The temperature is used for all subsequent
thermocouple measurements on that card.
If you select a fixed reference junction source, you can specify a
value between -20 °C and +80 °C using the
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction
command. You must always specify the temperature in degrees
Celsius regardless of the temperature units currently selected (see
UNIT:TEMPerature command).
The instrument selects the fixed source after a Factory Reset
(*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns INT, EXT or FIX for each channel in the <chan_list>.
Multiple channels are separated by commas.

Examples
The following command sets the reference junction type to an external
thermistor on channels 01 through 04 in slot 200.
TEMP:TRAN:TC:RJUN:TYPE EXT,(@201:204)
The following query returns the reference junction type for the four
channels shown.
TEMP:TRAN:TC:RJUN:TYPE? (@201:204)
Typical Response: EXT,EXT,EXT,EXT

See Also
SENSe Subsystem Introduction

[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE <type>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE? [(@<ch_list>)]

Description
This command selects the thermocouple type to use for measurements
on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<type> Discrete {B|E|J|K|N|R|S|T} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Thermocouple measurements require a reference junction
temperature (see
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE
command). For the reference junction temperature, you can use
an internal measurement on the module's terminal block (34901A
only), an external thermistor or RTD measurement, or a known
fixed junction temperature. By default, a fixed reference junction
temperature of 0.0 °C is used.
The instrument sets the thermocouple type to "J" after a Factory
Reset (*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns the thermocouple type as a quoted letter for each
channel in the list. Multiple channels are separated by commas.

Examples
The following command sets the thermocouple to J for the channels
shown.
TEMP:TRAN:TCouple:TYPE J,(@201:204)
The following query returns the thermocouple type for the channels
shown.
TEMP:TRAN:TC:TYPE? (@101,103,202:204,301)
Typical Response: B,R,J,J,J,K

See Also
SENSe Subsystem Introduction

[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE <type>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE? [(@<ch_list>)]

Description
This command selects the thermistor type for temperature
measurements on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<type> Discrete {2252|5000|10000} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
The instrument supports 2.2 kΩ (YSI 44004 Series), 5 kΩ (YSI
44007 Series), and 10 kΩ (YSI 44006 Series) thermistors.
The instrument sets the thermistor type to "5000" after a Factory
Reset (*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns 2252,5000 or 10000 for each channel in the list.
Multiple values are separated by commas.

Examples
The following command sets the thermocouple type to 5000 for the
channels shown.
TEMP:TRAN:THER:TYPE 5000,(@201,202,301)
The following query returns the thermocouple type for each of the
following channels.
TEMP:TRAN:THER:TYPE? (@201:203,301:303)
Typical Response: 5000,5000,2252,5000,10000,2252

See Also
SENSe Subsystem Introduction

[SENSe:]TEMPerature:TRANsducer:TYPE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TEMPerature:TRANsducer:TYPE
{TCouple|RTD|FRTD|THERmistor|DEF}[,(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TYPE? [(@<ch_list>)]

Description
This	command	selects	the	temperature	transducer	probe	type	to	use	for
measurements	on	the	specified	channels.
The	following	table	shows	which	temperature	transducers	are	supported
by	each	of	the	multiplexer	modules.

| Module | Thermocouple | RTD RTD | Thermistor |
| ------ | ------------ | ------- | ---------- |
|        |              | 2- 4-   |            |
Wire Wire
|     | Yes | Yes Yes | Yes |
| --- | --- | ------- | --- |
34901A
Armature
Multiplexer
| 34902A | Yes | Yes Yes | Yes |
| ------ | --- | ------- | --- |
Reed
Multiplexer
| 34908A   | Not          | Yes No1 | Yes |
| -------- | ------------ | ------- | --- |
| Armature | Recommended1 |         |     |
Multiplexer
(1-Wire)
1
With	a	one-wire	multiplexer,	even	very	small	ground	currents	can
introduce	substantial	measurement	error.

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Choosing the type DEF is equivalent to choosing TC.
For 4-wire resistance measurements, the instrument automatically
pairs channel n in Bank 1 with channel n+10 in Bank 2 (34901A)
or n+8 (34902A) to provide the source and sense connections. For
example, make the source connections to the HI and LO terminals
on channel 02 in Bank 1 and the sense connections to the HI and
LO terminals on channel 12 (34901A) or 10 (34902A) in Bank
2.Specify the paired channel in Bank 1 (source) as the <ch_list>
channel (channels in Bank 2 are not allowed in the <ch_list>).
The instrument selects thermocouple as the probe type after a
Factory Reset (*RST command). An Instrument Preset
(SYSTem:PRESet command) or Card Reset (SYSTem:CPON
command) does not change the setting.

Return Format
The query returns TC, RTD, FRTD, or THER. Multiple channels are
separated by commas.

Examples
The following command sets the temperature transducer type to FRTD
for the channels shown.
TEMP:TRAN:TYPE FRTD,(@201:205)
The following query returns the temperature transducer type for the
channels shown.
TEMP:TRAN:TYPE? (@201:208)
Typical Response: FRTD,FRTD,FRTD,FRTD,FRTD,RTD,TC,THER

See Also
SENSe Subsystem Introduction

[SENSe:]TOTalize:CLEar:IMMediate
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
[SENSe:]TOTalize:CLEar:IMMediate [(@<ch_list>)]

Description
This command immediately clears the count on the specified
counter/totalizer channels.
Used With:
34907A Multifunction Module (totalizer channel only)

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you omit
List One or more the
totalizer optional
channels, as <ch_list>
shown: parameter,
this
(@303) -
command
channel 03 on
applies to
the module in
the
slot 300.
currently
defined
(@103,203,303)
scan list.
- channel 03 on
the modules on
slot 100, 200,
and 300.

Example
The following command clears the count on totalizer channel 03 on the
module in slot 200.
TOT:CLEAR:IMM (@203)

See Also
SENSe Subsystem Introduction
[SENSe:]TOTalize:DATA?

[SENSe:]TOTalize:DATA?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
[SENSe:]TOTalize:DATA? [(@<ch_list>)]

Description
This query reads the count on the specified totalizer channels. If you
have configured the count to be reset when it is read (see
CONFigure:TOTalize and [SENSe:]TOTalize:TYPE commands), then this
command will reset the count to 0 after it is read. The count is reset
regardless of whether the specified channels are in a scan list or even
whether a scan is in progress.
Used With:
34907A Multifunction Module (totalizer channel only)

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you omit
List One or more the
totalizer optional
channels, as <ch_list>
shown: parameter,
this
(@303) -
command
channel 03 on
applies to
the module in
the
slot 300.
currently
defined
(@103,203,303)
scan list.
- channel 03 on
the modules on
slot 100, 200,
and 300.

Remarks
The maximum count is 67,108,863 (226 - 1). The count rolls over
to 0 after reaching the maximum allowed value.
The output from this command is affected by the settings of the
FORMat:READing commands. Depending on the formats
selected, each reading may or may not be stored with
measurement units, time stamp, channel number, and alarm
status information.

Return Format
The query returns an unsigned decimal value representing the count on
each totalizer channel specified (a full 32-bit count is returned). Multiple
responses are separated by commas.

Example
The following query reads the count on totalizer channel 03 on the
module in slot 3.
TOT:DATA? (@303)
Typical Response: 1.32130000E+03

See Also
SENSe Subsystem Introduction
CONFigure:TOTalize
[SENSe:]TOTalize:TYPE

[SENSe:]TOTalize:SLOPe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TOTalize:SLOPe <edge>[,(@<ch_list>)]
[SENSe:]TOTalize:SLOPe? [(@<ch_list>)]

Description
This command configures the specified totalizer channels to count on the
rising edge (positive) or falling edge (negative) of the input signal.
Used With:
34907A Multifunction Module (totalizer channel only)

Parameters
Name Type Range of Values Default
Value
<edge> Discrete {NEGative|POSitive} This is a
required
parameter.
<ch_list> Channel If you
List One or more omit the
totalizer channels, optional
as shown: <ch_list>
parameter,
(@303) - channel
this
03 on the module in
command
slot 300.
applies to
the
(@103,203,303) -
currently
channel 03 on the
defined
modules on slot
scan list.
100, 200, and 300.

Remarks
The selected slope is stored in volatile memory and will be set to
"POS" when power is turned off or after a Factory Reset (*RST
command).

Return Format
The query returns NEG or POS for the specified channels. Multiple
responses are separated by commas .

Examples
The following command configures totalizer channel 03 on the module in
slot 300 to count on the negative edge (falling) of the input signal.
TOT:SLOP NEG,(@303)
The following query returns the edge setting on totalizer channel 3 on the
modules in slots 1 and 3.
TOT:SLOP? (@103,303)
Typical Response: NEG,NEG

See Also
SENSe Subsystem Introduction

[SENSe:]TOTalize:STARt[:IMMediate]
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
[SENSe:]TOTalize:STARt:IMMediate [(@<ch_list>)]

Description
This command immediately starts totalizing on the specified
counter/totalizer channels.
Used With:
34907A Multifunction Module (totalizer channel only)

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you omit
List One or more the
totalizer optional
channels, as <ch_list>
shown: parameter,
this
(@303) -
command
channel 03 on
applies to
the module in
the
slot 300.
currently
defined
(@103,203,303)
scan list.
- channel 03 on
the modules on
slot 100, 200,
and 300.

Example
The following command starts totalizing on totalizer channel 03 on the
module in slot 200.
TOT:STARt:IMM (@203)

See Also
SENSe Subsystem Introduction
[SENSe:]TOTalize:DATA?
[SENSe:]TOTalize:STOP[:IMMediate]

[SENSe:]TOTalize:STOP[:IMMediate]
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
[SENSe:]TOTalize:STOP[:IMMediate] [(@<ch_list>)]

Description
This command immediately stops totalizing on the specified
counter/totalizer channels.
Used With:
34907A Multifunction Module (totalizer channel only)

Parameters
Name Type Range of Values Default
Value
<ch_list> Channel If you
List One or more omit the
totalizer optional
channels, as <ch_list>
shown: parameter,
this
(@303) -
command
channel 03 on
applies to
the module in
the
slot 300.
currently
defined
(@103,203,303)
scan list.
- channel 03 on
the modules on
slot 100, 200,
and 300.

Example
The following command stops totalizing on totalizer channel 03 on the
module in slot 200.
TOT:STOP:IMM (@203)

See Also
SENSe Subsystem Introduction
[SENSe:]TOTalize:DATA?
[SENSe:]TOTalize:STARt[:IMMediate]

[SENSe:]TOTalize:TYPE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]TOTalize:TYPE <mode>[,(@<ch_list>)]
[SENSe:]TOTalize:TYPE? [(@<ch_list>)]

Description
This command enables or disables an automatic reset of the count on
the specified totalizer channels. To read the totalizer during a scan
without resetting the count, select the READ parameter. To read the
totalizer during a scan and reset the count to 0 after it is read, select the
RRESet parameter (this means "read and reset").
Used With:
34907A Multifunction Module (totalizer channel only)

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <mode> | Discrete | {READ|RRESet} | This	is	a |
| ------ | -------- | ------------- | --------- |
required
parameter.
| <ch_list> | Channel |             | If	you	omit |
| --------- | ------- | ----------- | ----------- |
|           | List    | One	or	more | the         |
totalizer
optional
|     |     | channels,	as | <ch_list>  |
| --- | --- | ------------ | ---------- |
|     |     | shown:       | parameter, |
this
(@303)	-
command
channel	03	on
applies	to
the	module	in
the
slot	300.
currently
defined
(@103,203,303)
scan	list.
-	channel	03	on
the	modules	on
slot	100,	200,
and	300.

Remarks
The maximum count is 67,108,863 (226 - 1). The count rolls over
to 0 after reaching the maximum allowed value.

Return Format
The query returns READ or RRES for the specified channels. Multiple
responses are separated by commas.

Examples
The following command configures totalizer channel 03 on the module in
slot 300 to be read without resetting its count.
TOT:TYPE READ,(@303)
The following query returns the totalizer setting on totalizer channel 03
on the modules in slots 200 and 300.
TOT:TYPE? (@203,303)
Typical Response: READ,READ

See Also
SENSe Subsystem Introduction
[SENSe:]TOTalize:DATA?

[SENSe:]VOLTage:AC:BANDwidth
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]VOLTage:AC:BANDwidth {<filter>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]VOLTage:AC:BANDwidth? [{(@<ch_list>)|MIN|MAX}]

Description
The instrument uses three different AC filters which enable you to either
optimize low-frequency accuracy or achieve faster AC settling times. The
instrument selects the slow (3 Hz), medium (20 Hz), or fast (300 Hz) filter
based on the input frequency that you specify with this command for the
selected channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<filter> Discrete {3|20|200} 20
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
This	command	applies	to	AC	voltage	measurements	only.
For	the	<filter>	parameter,	specify	the	lowest	frequency	expected	in
the	input	signal	on	the	specified	channels.	The	instrument	selects
the	appropriate	filter	based	on	the	frequency	you	specify.
| Input	Frequency  | Default        | Minimum        |
| ---------------- | -------------- | -------------- |
|                  | Settling	Delay | Settling	Delay |
| 3	Hz	to	300	kHz  | 7	seconds	/    | 1.5	seconds    |
| (Slow)           | reading        |                |
| 20	Hz	to	300	kHz | 1	second	/     | 200	ms         |
| (Medium)         | reading        |                |
| 200	Hz	to	300    | 0.12	seconds	/ | 20	ms          |
| kHz	(Fast)       | reading        |                |
The	CONFigure	and	MEASure?	commands	automatically	select
the	default	20	Hz	(medium)	filter.
The	instrument	selects	the	default	20	Hz	(medium)	filter	after	a
Factory	Reset	(*RST	command).	An	Instrument	Preset
(SYSTem:PRESet	command)	or	Card	Reset	(SYSTem:CPON
command)	does	not	change	the	setting.
The	settling	delay	is	controlled	by	the	ROUTe:CHANnel:DELay
command.	You	get	the	default	delay	with
ROUTe:CHANnel:DELay:AUTO	ON.

Return Format
The query returns 3 (slow), 20 (medium), or 200 (fast) for each channel
specified. Multiple responses are separated by commas.

Examples
The following command selects the slow filter (3 Hz) on channels 03 and
13 in slot 100.
VOLT:AC:BAND 3,(@103,113)
The following query returns the ac filter settings on channels 03 and 13
in slot 100.
VOLT:AC:BAND? (@103,113)
Typical Response: 3,3

See Also
SENSe Subsystem Introduction
CONFigure:VOLTage:AC

[SENSe:]VOLTage:AC:RANGe
[SENSe:]VOLTage:DC:RANGe
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]VOLTage:AC:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]VOLTage:AC:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]VOLTage:DC:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]VOLTage:DC:RANGe? [{(@<ch_list>)|MIN|MAX}]

Description
These commands selects the measurement range for AC and DC
voltage measurements on the specified channels.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<range> Discrete This is a
Desired range in volts: required
parameter.
100 mV (MIN)
1 V
10 V
100 V
300 V (MAX)
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Selecting a discrete range will disable autoranging on the specified
channels (see [SENSe:]VOLTage:AC:RANGe:AUTO command).
The CONFigure and MEASure? commands automatically enable
autoranging if the first parameter is AUTO, DEF or omitted.
If the input signal is greater than can be measured on the selected
range (manual ranging), the instrument gives an overload
indication: "±OVLD" from the front panel or "±9.9E+37" from the
remote interface.
The instrument enables autoranging after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns the range in the form "+1.00000000E+01" for each
channel specified. Multiple responses are separated by commas.

Examples
In the following examples, you can substitute the node name AC for DC.
The following command selects the 10 volt range on channels 03 and 13
in slot 100.
VOLT:DC:RANG 10,(@103,113)
The following query returns the range selected on channels 03 and 13 in
slot 100.
VOLT:DC:RANG? (@103,113)
Typical Response: +1.00000000E+01,+1.00000000E+01

See Also
SENSe Subsystem Introduction
CONFigure:VOLTage:AC
CONFigure:VOLTage:DC
[SENSe:]VOLTage:AC:RANGe:AUTO
[SENSe:]VOLTage:DC:RANGe:AUTO

[SENSe:]VOLTage:AC:RANGe:AUTO
[SENSe:]VOLTage:DC:RANGe:AUTO
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]VOLTage:AC:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]VOLTage:AC:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]VOLTage:DC:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]VOLTage:DC:RANGe:AUTO? [(@<ch_list>)]

Description
These commands disable or enable autoranging for AC and DC voltage
measurements on the specified channels. Autoranging is convenient
because the instrument automatically selects the range for each
measurement based on the input signal detected.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<state> Boolean {OFF|0|ON|1} This is a
required
parameter.
The
factory
default is
ON.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
Autorange thresholds:
Down range at: <10% of range
Up range at: >120% of range
With autoranging enabled, the instrument selects one of the
following ranges based on the input signal detected:
100mV
1 V
10 V
100 V
300 V
Selecting a discrete range (see [SENSe:]VOLTage:AC:RANGe
command) will disable autoranging on the specified channels.
The CONFigure and MEASure? commands automatically enable
autoranging if the first parameter is AUTO, DEF or omitted.
The instrument enables autoranging after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns 0 (OFF) or 1 (ON) for each channel specified. Multiple
responses are separated by commas.

Examples
In each of the following examples, you can replace the node name AC
with DC.
The following command disables autoranging on channels 03 and 13 in
slot 100.
VOLT:AC:RANG:AUTO OFF,(@103,113)
The following query returns the autoranging settings on channels 03 and
13 in slot 100.
VOLT:AC:RANG:AUTO? (@103,113)
Typical Response: 0,0

See Also
SENSe Subsystem Introduction
CONFigure:VOLTage:AC
CONFigure:VOLTage:DC
[SENSe:]VOLTage:AC:RANGe
[SENSe:]VOLTage:DC:RANGe

[SENSe:]VOLTage:DC:APERture
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]VOLTage:DC:APERture {<time>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]VOLTage:DC:APERture? [{(@<ch_list>)|MIN|MAX}]

Description
This command enables the aperture mode and sets the integration time
in seconds (called aperture time) for DC voltage measurements on the
specified channels.
You should use this command only when you
want precise control of the integration time of
the internal DMM. Otherwise, specifying
integration time using NPLC (see
[SENSe:]VOLTage[:DC]:NPLC command)
executes faster and offers better power line
noise rejection characteristics for values of
NPLC greater than 1.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<time> Numeric Desired aperture time in Aperture
seconds between 300 µs disabled.
and 1 second, with 4 µs
resolution. MIN = 300 µs,
MAX = 1 second
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
For the <seconds> parameter, you can substitute MIN or MAX for
a numeric value. MIN selects the smallest value accepted, which
gives the lowest resolution; MAX selects the largest value
accepted, which gives the highest resolution.
Only the integral number of power line cycles (1, 2, 10, 20, 100, or
200 PLCs) provide normal mode (line frequency noise) rejection.
The CONFigure, MEASure?, [SENSe:]VOLTage[:DC]:NPLC, and
[SENSe:]VOLTage[:DC]:RESolution commands disable the
aperture time mode (these commands select an integration time in
number of power line cycles).
The aperture mode is disabled after a Factory Reset (*RST
command). An Instrument Preset (SYSTem:PRESet command) or
Card Reset (SYSTem:CPON command) does not change the
setting.

Return Format
The query returns the aperture time in the form "+1.00000000E-01" for
each channel specified. Multiple responses are separated by commas.

Examples
The following command enables the aperture mode and sets the
aperture time to 300 ms on channels 03 and 13 in slot 100.
VOLT:DC:APER 300E-03,(@103,113)
The following query returns the aperture time selected on channels 03
and 13 in slot 100.
VOLT:DC:APER? (@103,113) VOLT:DC:APER:ENAB? !Verify
that aperture mode is enabled ("1")
Typical Response: +3.00000000E-01,+3.00000000E-01

See Also
SENSe Subsystem Introduction
CONFigure:VOLTage:DC
[SENSe:]VOLTage:DC:NPLC

[SENSe:]VOLTage:DC:NPLC
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]VOLTage:DC:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]VOLTage:DC:NPLC? [{(@<ch_list>)|MIN|MAX}]

Description
This command sets the integration time in number of power line cycles
(PLCs) on the specified channels.Integration time affects the
measurement resolution (for better resolution, use a longer integration
time) and measurement speed (for faster measurements, use a shorter
integration time).
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<PLCs> Discrete {0.02|0.2|1|2|10|20|100|200|MIN|MAX} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, as shown: omit the
optional
(@310) - channel 10 on the module
<ch_list>
in slot 300.
parameter,
this
(@305:310) - channels 05 through
command
10 on the module in slot 300.
applies to
the
(@202:207,209,302:308) - channels
currently
02 through 07 and 09 on the
defined
module in slot 200 and channels 02
scan list.
through 08 on the module in slot
300.

Remarks
Only	the	integral	number	of	power	line	cycles	(1,	2,	10,	20,	100,	or
200	PLCs)	provide	normal	mode	(line	frequency	noise)	rejection.
Setting	the	resolution	also	sets	the	integration	time	for	the
measurement.	The	following	table	shows	the	relationship	between
integration	time,	measurement	resolution,	number	of	digits,	and
number	of	bits.
| Integration | Resolution | Digits Bits |
| ----------- | ---------- | ----------- |
Time
| 0.02	PLC | <0.0001	x   | 4½ 15  |
| -------- | ----------- | ------ |
|          | Range       | Digits |
| 0.2	PLC  | <0.00001	x  | 5½ 18  |
|          | Range       | Digits |
| 1	PLC    | <0.000003	x | 5½ 20  |
|          | Range       | Digits |
| 2	PLC    | <0.0000022  | 6½ 21  |
|          | x	Range     | Digits |
| 10	PLC   | <0.000001	x | 6½ 24  |
|          | Range       | Digits |
| 20	PLC   | <0.0000008  | 6½ 25  |
|          | x	Range     | Digits |
| 100	PLC  | <0.0000003  | 6½ 26  |
|          | x	Range     | Digits |
| 200	PLC  | <0.00000022 | 6½ 26  |
|          | x	Range     | Digits |
The	specified	integration	time	is	used	for	all	measurements	on	the
selected	channels.	If	you	have	applied	Mx+B	scaling	or	have
assigned	alarms	to	the	selected	channel,	those	measurements	are

also made using the specified integration time. Measurements
taken during the Monitor function also use the specified integration
time.
You can also set the integration time by specifying an aperture
time (see [SENSe:]VOLTage[:DC]:APERture command). However,
note that specifying integration time using NPLCs executes faster
and offers better noise rejection characteristics for values of NPLC
greater than 1.
The CONFigure, MEASure?, [SENSe:]VOLTage[:DC]:NPLC, and
[SENSe:]VOLTage[:DC]:RESolution commands disable the
aperture time mode (these commands select an integration time in
number of power line cycles).
The instrument sets the integration time to 1 PLC after a Factory
Reset (*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns the integration time in power line cycles for each
channel in the form +1.12345678E+01.

Examples
The following command sets the integration time to 20 PLCs on
channels 03 through 06 in slot 200.
VOLT:DC:NPLC 20,(@203:206)
The following query returns the integration time on the same channels.
VOLT:DC:NPLC? (@203:206)
Typical Response:
+2.00000000E+01,+2.00000000E+01,+2.00000000E+01,+2.00000000E+01

See Also
SENSe Subsystem Introduction

[SENSe:]VOLTage:DC:RESolution
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]VOLTage:DC:RESolution {<resolution>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]VOLTage:DC:RESolution? [{(@<ch_list>)|MIN|MAX}]

Description
This command selects the measurement resolution for DC voltage
measurements on the specified channels. The instrument clears all
readings from memory when a new scan is initiated, when any
measurement parameters are changed (CONFigure and SENSe
commands), and when the triggering configuration is changed (TRIGger
commands).
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<resolution> Numeric Desired resolution in volts. This is a
required
field. You
must specify
a numeric
<resolution>
or specify
MIN or
MAX to
select the
smallest or
largest
<resolution>.
<ch_list> Channel If you omit
List One or more channels, the optional
as shown: <ch_list>
parameter,
(@310) - channel 10 on
this
the module in slot 300.
command
applies to the
(@305:310) - channels
currently
05 through 10 on the
defined scan
module in slot 300.
list.
(@202:207,209,302:308)
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
For	the	<resolution>	parameter,	you	can	substitute	MIN	or	MAX	for
a	numeric	value.	MIN	selects	the	smallest	value	accepted,	which
gives	the	highest	resolution;	MAX	selects	the	largest	value
accepted,	which	gives	the	least	resolution.
The	instrument	will	dispatch	a	settings	conflict	error	if	you	issue
this	command	when	[SENSe:]VOLTage:DC:RANGe:AUTO	is	ON
for	one	or	more	of	the	specified	channels.
Setting	the	resolution	also	sets	the	integration	time	for	the
measurement.	The	following	table	shows	the	relationship	between
integration	time,	measurement	resolution,	number	of	digits,	and
number	of	bits.
| Integration | Resolution | Digits Bits |
| ----------- | ---------- | ----------- |
Time
| 0.02	PLC | <0.0001	x   | 4½ 15  |
| -------- | ----------- | ------ |
|          | Range       | Digits |
| 0.2	PLC  | <0.00001	x  | 5½ 18  |
|          | Range       | Digits |
| 1	PLC    | <0.000003	x | 5½ 20  |
|          | Range       | Digits |
| 2	PLC    | <0.0000022  | 6½ 21  |
|          | x	Range     | Digits |
| 10	PLC   | <0.000001	x | 6½ 24  |
|          | Range       | Digits |
| 20	PLC   | <0.0000008  | 6½ 25  |
|          | x	Range     | Digits |
| 100	PLC  | <0.0000003  | 6½ 26  |
|          | x	Range     | Digits |

200 PLC <0.00000022 6½ 26
x Range Digits
You can also set the integration time by specifying an aperture
time (see [SENSe:]VOLTage[:DC]:APERture command). However,
note that specifying integration time using NPLCs executes faster
and offers better noise rejection characteristics for values of NPLC
greater than 1.
The CONFigure, MEASure?, [SENSe:]VOLTage[:DC]:NPLC, and
[SENSe:]VOLTage[:DC]:RESolution commands disable the
aperture time mode (these commands select an integration time in
number of power line cycles).
The instrument sets the resolution to 1 PLC after a Factory Reset
(*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns the resolution in the form +1.12345678E+01 for each
channel in the <ch_list>. Multiple channels are separated by commas.

Examples
The following command sets the <resolution> to 50 microvolts for the
channels shown.
VOLT:DC:RES 0.00005,(@201:204)
The following query returns the <resolution> for channels 01 through 04
on slot 200.
VOLT:DC:RES? (@201:204)
Typical Response:
+1.00000000E+01,+1.00000000E+01,+1.00000000E+01,+1.00000000E+01

See Also
SENSe Subsystem Introduction

[SENSe:]ZERO:AUTO
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
[SENSe:]ZERO:AUTO <mode>[,(@<ch_list>)]
[SENSe:]ZERO:AUTO? [(@<ch_list>)]

Description
This command enables (default) or disables the autozero mode on the
specified channels.

Parameters
Name Type Range of Values Default
Value
<mode> Discrete {OFF|ONCE|ON} This is a
required
parameter.
<ch_list> Channel If you
List One or more channels, omit the
as shown: optional
<ch_list>
(@310) - channel 10 on
parameter,
the module in slot 300.
this
command
(@305:310) - channels
applies to
05 through 10 on the
the
module in slot 300.
currently
defined
(@202:207,209,302:308)
scan list.
- channels 02 through 07
and 09 on the module in
slot 200 and channels 02
through 08 on the
module in slot 300.

Remarks
The OFF and ONCE parameters have the same effect.
The CONFigure, MEASure and NPLC commands automatically
specify ZERO:AUTO as OFF for 0.02 to 0.2 PLCs and as ON for 1
PLC or more.

Return Format
The query form returns 0 (OFF or ONCE) or 1.

Examples
The following command turns the autozero mode OFF (@301:305).
ZERO:AUTO OFF (@301:305)
The following query returns the state of the autozero mode, which in this
case is OFF. Multiple responses are separated by commas.
ZERO:AUTO? (@301:305)
Typical response: 0,0,0,0,0

See Also
SENSe Subsystem Introduction

SOURce Subsystem Introduction
Command Summary
SOURce:DIGital:DATA[:{BYTE|WORD}]
SOURce:DIGital:DATA[:{BYTE|WORD}]?
SOURce:DIGital:STATe?
SOURce:VOLTage
SOURce:VOLTage?

SOURce:DIGital:DATA[:{BYTE|WORD}]
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
SOURce:DIGital:DATA[:{BYTE|WORD}] <data>,(@<ch_list>)
SOURce:DIGital:DATA[:{BYTE|WORD}]? (@<ch_list>)

Description
This command outputs a digital pattern as an 8-bit byte or 16-bit word to
the specified digital output channels.

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <data>    | Numeric | An	integer	from	0	to | This	is	a  |
| --------- | ------- | -------------------- | ---------- |
|           |         | 255	(:BYTE)	or       | required   |
|           |         | 65,535	(:WORD).      | parameter. |
| <ch_list> | Channel |                      | This	is	a  |
|           | List    | One	or	more	digital  | required   |
I/O	channels,	as
parameter.
shown:
(@301)	-	channel	01
on	the	module	in	slot
300.
(@101:102,201,302)
-	channels	01	and
02	on	the	modules
on	slot	100,	channel
01	on	the	module	in
slot	200,	and
channel	02	on	the
module	in	slot	300.

Remarks
Note that you cannot configure a port for output operations if that
port is already configured to be part of the scan list (digital input).
You must specify an integer value, either as a decimal number
(213), a binary number (#b11010101) or a hexadecimal number
(#hD5).
The digital output channels are numbered "s01" (lower byte) and
"s02" (upper byte), where s represents the slot number.
If you are going to write to both ports simultaneously (WORD), you
must send the command to channel 01.

Return Format
The :BYTE? (or :WORD?) query returns the last byte or word sent to the
specified digital output channel as a decimal number in the form +255.

Examples
The following commands all output the number 12345 to channel 01 on
the module in slot 200.
SOUR:DIGital:DATA:WORD 12345,(@201) !
decimal integer 12345
SOUR:DIGital:DATA:WORD #b0011000000111001,(@201) !
binary equivalent of decimal integer 12345
SOUR:DIGital:DATA:WORD #h3039,(@201) !
hexadecimal equivalent of decimal integer 12345
The following command reads the number on channel 01 on the module
in slot 200.
SOUR:DIG:DATA:WORD? (@201)
Typical Response: +12345

See Also
SOURce Subsystem Introduction

SOURce:DIGital:STATe?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
SOURce:DIGital:STATe? (@<ch_list>)

Description
This command returns the status (input or output) of the specified digital
channels.
Used With:
34907A Multifunction Module (digital I/O channels only)

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <ch_list> | Channel |     | This	is	a |
| --------- | ------- | --- | --------- |
One	or	more	digital
|     | List |                  | required   |
| --- | ---- | ---------------- | ---------- |
|     |      | I/O	channels,	as | parameter. |
shown:
(@301)	-	channel	01
on	the	module	in	slot
300.
(@101:102,201,302)
-	channels	01	and
02	on	the	modules
on	slot	100,	channel
01	on	the	module	in
slot	200,	and
channel	02	on	the
module	in	slot	300.

Remarks
A channel is set as an output channel when you send a
SOURce:DIGital:DATA[:{BYTE|WORD}] command.
A channel is set as an input channel when you place it in a scan
list or send a [SENSe:]DIGital:DATA:{BYTE|WORD}? command.

Return Format
The query returns 0 if the specified channel is an input channel or 1 if the
channel is an output channel. Multiple responses are separated by
commas.

Example
The following query returns the input/output state of channels 01 and 02
on the module in slot 300. In this case, both channels are configured for
output.
SOUR:DIG:STAT? (@301,302)
Typical Response: 1,1

See Also
SOURce Subsystem Introduction
SOURce:VOLTage

SOURce:VOLTage
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
SOURce:VOLTage <voltage>,(@<ch_list>)
SOURce:VOLTage? (@<ch_list>)

Description
This command sets the output voltage level for the specified DAC
channels on the 34907A Multifunction Module.
This command outputs a DC voltage level.

Parameters
Name Type Range of Values Default
Value
<voltage> Numeric 0 Vdc
A number of volts
from -12 to +12, in
resolution of 0.001
V.
<ch_list> Channel This is a
List One or more required
DAC channels, as parameter.
shown:
(@304) - channel 04
on the module in slot
300.
(@104:105,204,305)
- channels 04 and
05 on the modules
on slot 100, channel
04 on the module in
slot 200, and
channel 05 on the
module in slot 300.

Remarks
The DAC channels are numbered "s04" and "s05", where s
represents the slot number.
Each DAC channel is capable of 10 mA maximum output current.
A Factory Reset (*RST command), Instrument Preset
(SYSTem:PRESet command), and Card Reset (SYSTem:CPON
command) will reset the DAC outputs to 0 Vdc.

Return Format
The query returns the output voltage in the form +1.00000000E+00 for
each DAC channel specified. Multiple responses are separated by
commas.

Examples
The following command outputs +2.5 Vdc on DAC channels 04 and 05 in
slot 200.
SOUR:VOLT 2.5,(@204,205) OUTP:STAT ON,(@204,205)
The following query returns the voltage outputs on DAC channels 04 and
05 in slot 200.
SOUR:VOLT? (@204,205)
Typical Response: +2.50000000E+00,+2.50000000E+00

See Also
SOURce Subsystem Introduction

STATus Subsystem Introduction
Keysight 34970A/34972A Status System Diagram
Printable PDF Version
STATus:PRESet

Command Summary
*ESE
*ESE?
*ESR?
*SRE
*STB?
STATus:ALARm:CONDition?
STATus:ALARm:ENABle
STATus:ALARm:ENABle?
STATus:ALARm[:EVENt]?
STATus:OPERation:CONDition?
STATus:OPERation:ENABle
STATus:OPERation:ENABle?
STATus:OPERation[:EVENt]?
STATus:PRESet
STATus:QUEStionable:CONDition?
STATus:QUEStionable:ENABle
STATus:QUEStionable:ENABle?
STATus:QUEStionable[:EVENt]?

STATus:ALARm:CONDition?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
STATus:ALARm:CONDition?

Description
This command queries the condition register for the Alarm Register
group (note that this condition register uses only bit 4). This is a read-
only register and the bits are not cleared when you read the register.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
The	following	table	lists	the	bit	definitions	for	the	alarm	enable
register.
| Bit	# | Bit	Name | Decimal | Definition |
| ----- | -------- | ------- | ---------- |
Value
| 0-3 Not	Used |     | 1-8       | 0	is	returned.         |
| ------------ | --- | --------- | ---------------------- |
| 4 Queue	Not  |     | 16        | The	alarm	queue	is	not |
| Empty        |     |           | empty.                 |
| 5 Not	Used   |     | 32        | 0	is	returned.         |
| 6 Alarm	1    |     | 64        | Alarm	1	is	triggered.  |
| 7 Alarm	2    |     | 128       | Alarm	2	is	triggered.  |
| 8 Alarm	3    |     | 256       | Alarm	3	is	triggered.  |
| 9 Alarm	4    |     | 512       | Alarm	4	is	triggered.  |
| 10- Not	Used |     | 1024-2048 | 0	is	returned.         |
11
| 12 Lower	Limit |     | 4096 |     |
| -------------- | --- | ---- | --- |
A	lower	limit	alarm	has
occurred.
| 13 Upper	Limit |     | 8192 | An	upper	limit	alarm	has |
| -------------- | --- | ---- | ------------------------ |
occurred.
| 14- Not	Used |     | 16384- | 0	is	returned. |
| ------------ | --- | ------ | -------------- |
| 15           |     | 32768  |                |
A	Factory	Reset	(*RST	command)	will	clear	the	"Queue	Empty"	bit
(bit	4)	in	the	condition	register.

Return Format
The query reads the condition register and returns a decimal value which
corresponds to the binary-weighted sum of all bits set in the register (see
table above). For example, if bits 6 - 8 are set, this command will return
+448.

Examples
The following query reads the condition register (bits 6 and 9 are set).
STAT:ALAR:COND?
Typical Response: +576

See Also
STATus Subsystem Introduction
STATus:ALARm:ENABle
STATus:ALARm[:EVENt]?
SYSTem:ALARm?

STATus:ALARm:ENABle
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
STATus:ALARm:ENABle <enable_val>
STATus:ALARm:ENABle?

Description
This command enables bits in the enable register for the Alarm Register
group. The selected bits are then reported to the Status Byte.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name         | Type    | Range	of   | Default    |
| ------------ | ------- | ---------- | ---------- |
|              |         | Values     | Value      |
| <enable_val> | Numeric | An	integer | This	is	a  |
|              |         | from	0	to  | required   |
|              |         | 65535,     | parameter. |
specifying
the	alarms	to
enable	as	a
bit	sum.

Remarks
The	following	table	lists	the	bit	definitions	for	the	alarm	enable
register.
| Bit	# | Bit	Name | Decimal | Definition |
| ----- | -------- | ------- | ---------- |
Value
| 0 Alarm	1 |     | 1   | An	event	has	occurred	on |
| --------- | --- | --- | ------------------------ |
Alarm	1.
| 1 Alarm	2 |     | 2   | An	event	has	occurred	on |
| --------- | --- | --- | ------------------------ |
Alarm	2.
| 2 Alarm	3 |     | 4   | An	event	has	occurred	on |
| --------- | --- | --- | ------------------------ |
Alarm	3.
| 3 Alarm	4 |     | 8   | An	event	has	occurred	on |
| --------- | --- | --- | ------------------------ |
Alarm	4.
| 4 Queue	Not      |     | 16  | The	alarm	queue	is	not |
| ---------------- | --- | --- | ---------------------- |
| Empty            |     |     | empty.                 |
| 5 Queue	Overflow |     | 32  |                        |
An	alarm	queue
overflow	event	has
occurred.
| 6 Alarm	1    |     | 64        | Alarm	1	is	triggered. |
| ------------ | --- | --------- | --------------------- |
| 7 Alarm	2    |     | 128       | Alarm	2	is	triggered. |
| 8 Alarm	3    |     | 256       | Alarm	3	is	triggered. |
| 9 Alarm	4    |     | 512       | Alarm	4	is	triggered. |
| 10- Not	Used |     | 1024-2048 | 0	is	returned.        |
11
| 12 Lower	Limit |     | 4096 |     |
| -------------- | --- | ---- | --- |
A	lower	limit	alarm	has
occurred.

| 13 Upper	Limit | 8192 | An	upper	limit	alarm	has |
| -------------- | ---- | ------------------------ |
occurred.
| 14- Not	Used | 16384- | 0	is	returned. |
| ------------ | ------ | -------------- |
| 15           | 32768  |                |

Return Format
The query reads the enable register and returns a decimal value that
corresponds to the binary-weighted sum of all bits set in the register. For
example, if bit 1 (decimal value = 2) and bit 2 (decimal value = 4) are
enabled, the query will return +6.

Examples
The following command enables alarm registers 0 through 3.
STAT:ALAR:ENAB 15
The following query returns a the binary sum equivalent to the enabled
registers.
STAT:ALAR:ENAB?
Typical Response: +15

See Also
STATus Subsystem Introduction

STATus:ALARm[:EVENt]?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
STATus:ALARm[:EVENt]?

Description
This command queries the event register for the Alarm Register group.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
The	following	table	lists	the	bit	definitions	for	the	alarm	event
register.
| Bit	# | Bit	Name | Decimal | Definition |
| ----- | -------- | ------- | ---------- |
Value
| 0 Alarm	1 |     | 1   | An	event	has	occurred	on |
| --------- | --- | --- | ------------------------ |
Alarm	1.
| 1 Alarm	2 |     | 2   | An	event	has	occurred	on |
| --------- | --- | --- | ------------------------ |
Alarm	2.
| 2 Alarm	3 |     | 4   | An	event	has	occurred	on |
| --------- | --- | --- | ------------------------ |
Alarm	3.
| 3 Alarm	4 |     | 8   | An	event	has	occurred	on |
| --------- | --- | --- | ------------------------ |
Alarm	4.
| 4 Queue	Not      |     | 16  | The	alarm	queue	is	not |
| ---------------- | --- | --- | ---------------------- |
| Empty            |     |     | empty.                 |
| 5 Queue	Overflow |     | 32  |                        |
An	alarm	queue
overflow	event	has
occurred.
| 6 Alarm	1      |     | 64        | Alarm	1	is	triggered. |
| -------------- | --- | --------- | --------------------- |
| 7 Alarm	2      |     | 128       | Alarm	2	is	triggered. |
| 8 Alarm	3      |     | 256       | Alarm	3	is	triggered. |
| 9 Alarm	4      |     | 512       | Alarm	4	is	triggered. |
| 10-11 Not	Used |     | 1024-2048 | 0	is	returned.        |
| 12 Lower	Limit |     | 4096      |                       |
A	lower	limit	alarm	has
occurred.

| 13 Upper	Limit | 8192 | An	upper	limit	alarm	has |
| -------------- | ---- | ------------------------ |
occurred.
| 14-15 Not	Used | 16384- | 0	is	returned. |
| -------------- | ------ | -------------- |
32768
Note	that	if	any	of	bits	0	through	3	are	set,	bit	4	will	also	be	set	to
indicate	that	the	Alarm	Queue	is	not	empty.
Once	a	bit	is	set,	it	remains	set	until	cleared	by	reading	the	event
register	or	the	*CLS	(clear	status)	command.

Return Format
The query reads the event register and returns a decimal value which
corresponds to the binary-weighted sum of all bits set in the register (see
table above). For example, if bit 1 (decimal value = 2) and bit 2 (decimal
value = 4) are set, this command will return +6.

Examples
The following query indicates that alarm events have occurred on alarms
1 and 3.
STAT:ALAR:EVENt?
Typical Response: +5

See Also
STATus Subsystem Introduction
STATus:ALARm:CONDition?
STATus:ALARm:ENABle

STATus:OPERation:CONDition?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
STATus:OPERation:CONDition?

Description
This command queries the condition register for the Standard Operation
Register group. This is a read-only register and the bits are not cleared
when you read the register.
For more information on the Status System for the
instrument, see Status System Introduction.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
The	condition	register	bits	reflect	the	current	condition.	If	a
condition	is	no	longer	true,	the	corresponding	bit	is	cleared	in	the
condition	register.
The	following	table	lists	the	bit	definitions	for	the	Standard
Operation	Register.
| Bit Bit	Name  | Decimal |                                 | Definition |
| ------------- | ------- | ------------------------------- | ---------- |
| #             | Value   |                                 |            |
| 0 Calibrating | 1       | The	instrument	is	calibrating.  |            |
| 1 Self	Test   | 2       | The	instrument	is	doing	a	self- |            |
test.
| 2 Not	Used | 4   | (Always	returns	0)              |     |
| ---------- | --- | ------------------------------- | --- |
| 3 Not	Used | 8   | (Always	returns	0)              |     |
| 4 Scanning | 16  | The	instrument	is	scanning.     |     |
| 5 WFT      | 32  | The	instrument	is	waiting	for	a |     |
trigger.
| 6 Not	Used    | 64   | (Always	returns	0)             |     |
| ------------- | ---- | ------------------------------ | --- |
| 7 USB	MSD     | 128  | A	USB	mass	storage	device      |     |
| detected      |      | (USB	drive)	has	been	detected. |     |
| 8 Config      | 256  | The	instrument	configuration   |     |
| Changed       |      | has	changed.                   |     |
| 9 Not	Used    | 512  | (Always	returns	0)             |     |
| 10 Instrument | 1024 | The	instrument	is	locked.      |     |
Locked
| 11 Not	Used | 2048 | (Always	returns	0) |     |
| ----------- | ---- | ------------------ | --- |
| 12 Not	Used | 4096 | (Always	returns	0) |     |

| 13 Global	Error | 8192 | An	error	is	in	the	global	error |
| --------------- | ---- | ------------------------------- |
queue.
| 14 Busy     | 16384 | The	instrument	is	busy. |
| ----------- | ----- | ----------------------- |
| 15 Not	Used | 32768 |                         |
(Always	returns	0)

Bit	14,	the	Busy	bit,	will	be	set	while	the	instrument	is	performing
long	commands,	such	as	MMEMory:IMPort:CONFig?.
A	Factory	Reset	(*RST	command)	will	set	the	"Configuration
Change"	bit	(bit	8)	in	the	condition	register.

Return Format
The query reads the condition register and returns a decimal value that
corresponds to the binary-weighted sum of all bits set in the register (see
table above). For example, if bit 4 (decimal value = 16) and bit 8 (decimal
value = 256) are set, this command will return "+272".

Examples
The following command reads the condition register (bit 8 is set).
STAT:OPER:COND?
Typical Response: +256

See Also
STATus Subsystem Introduction
STATus:OPERation:ENABle
STATus:OPERation[:EVENt]?

STATus:OPERation:ENABle
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
STATus:OPERation:ENABle <enable_val>
STATus:OPERation:ENABle?

Description
This command enables bits in the enable register for the Standard
Operation Register group. The selected bits are then reported to the
Status Byte.
For more information on the
Status System for the instrument,
see Status System Introduction.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name         | Type    | Range	of   | Default    |
| ------------ | ------- | ---------- | ---------- |
|              |         | Values     | Value      |
| <enable_val> | Numeric | An	integer | This	is	a  |
|              |         | from	0	to  | required   |
|              |         | 65535,     | parameter. |
specifying
the	bits	to
enable	as
a	bit	sum.

Remarks
The	following	table	lists	the	bit	definitions	for	the	Standard
Operation	Register.
| Bit Bit	Name  | Decimal |                                      | Definition |
| ------------- | ------- | ------------------------------------ | ---------- |
| #             | Value   |                                      |            |
| 0 Calibrating | 1       | The	instrument	is	calibrating.       |            |
| 1 Self	Test   | 2       | The	instrument	is	doing	a	self-test. |            |
| 2 Not	Used    | 4       | (Always	returns	0)                   |            |
| 3 Not	Used    | 8       | (Always	returns	0)                   |            |
| 4 Scanning    | 16      | The	instrument	is	scanning.          |            |
| 5 WFT         | 32      | The	instrument	is	waiting	for	a      |            |
trigger.
| 6 Not	Used | 64  | (Always	returns	0)                |     |
| ---------- | --- | --------------------------------- | --- |
| 7 USB	MSD  | 128 | A	USB	mass	storage	device         |     |
| detected   |     | (USB	drive)	has	been	detected.    |     |
| 8 Config   | 256 | The	instrument	configuration	has  |     |
| Changed    |     | changed.                          |     |
| 9 Mem      | 512 | The	number	of	readings	in	memory  |     |
| Threshold  |     | has	exceeded	the	memory	threshold |     |
setting	(see
DATA:POINts:EVENt:THReshold).
| 10 Instrument | 1024 | The	instrument	is	locked. |     |
| ------------- | ---- | ------------------------- | --- |
Locked
| 11 Settings     | 2048 | The	instrument's	settings	have         |     |
| --------------- | ---- | -------------------------------------- | --- |
| Changed         |      | changed.                               |     |
| 12 Not	Used     | 4096 | (Always	returns	0)                     |     |
| 13 Global	Error | 8192 | An	error	is	in	the	global	error	queue. |     |

14 Busy 16384 The instrument is busy.
15 Not Used 32768
(Always returns 0)
Use the <enable_value> parameter to specify which bits will be
reported to the Status Byte. The decimal value specified
corresponds to the binary-weighted sum of the bits you wish to
enable in the register. For example, to enable bit 0 (decimal value
= 1) and bit 10 (decimal value = 1024), the corresponding decimal
value would be 1024 (1 + 1024).
Bit 14, the Busy bit, will be set while the instrument is performing
long commands, such as MMEMory:IMPort:CONFig?.

Return Format
The query command reads the enable register and returns a decimal
value corresponding to the binary-weighted sum of all bits set in the
register. For example, if bit 0 (decimal value = 1) and bit 10 (decimal
value = 1024) are enabled, the query command will return +1025.

Examples
The following command enables bit 9 (decimal value = 512) in the
enable register.
STAT:OPER:ENAB 512
The following query returns which bits are enabled in the register.
STAT:OPER:ENAB?
Typical Response: +512

See Also
STATus Subsystem Introduction
STATus:OPERation:CONDition?
STATus:OPERation[:EVENt]?

STATus:OPERation[:EVENt]?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
STATus:OPERation[:EVENt]?

Description
This command queries the condition register for the Standard Operation
Register group. This is a read-destructive register and the bits are
cleared when you read the register.
For more information on the Status System for the
instrument, see Status System Introduction.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
The	following	table	lists	the	bit	definitions	for	the	Standard
Operation	Register.
| Bit Bit	Name  | Decimal |                                      | Definition |
| ------------- | ------- | ------------------------------------ | ---------- |
| #             | Value   |                                      |            |
| 0 Calibrating | 1       | The	instrument	is	calibrating.       |            |
| 1 Self	Test   | 2       | The	instrument	is	doing	a	self-test. |            |
| 2 Not	Used    | 4       | (Always	returns	0)                   |            |
| 3 Not	Used    | 8       | (Always	returns	0)                   |            |
| 4 Scanning    | 16      | The	instrument	is	scanning.          |            |
| 5 WFT         | 32      | The	instrument	is	waiting	for	a      |            |
trigger.
| 6 Not	Used | 64  | (Always	returns	0)                |     |
| ---------- | --- | --------------------------------- | --- |
| 7 USB	MSD  | 128 | A	USB	mass	storage	device         |     |
| detected   |     | (USB	drive)	has	been	detected.    |     |
| 8 Config   | 256 | The	instrument	configuration	has  |     |
| Changed    |     | changed.                          |     |
| 9 Mem      | 512 | The	number	of	readings	in	memory  |     |
| Threshold  |     | has	exceeded	the	memory	threshold |     |
setting	(see
DATA:POINts:EVENt:THReshold).
| 10 Instrument | 1024 | The	instrument	is	locked. |     |
| ------------- | ---- | ------------------------- | --- |
Locked
| 11 Settings     | 2048 | The	instrument's	settings	have         |     |
| --------------- | ---- | -------------------------------------- | --- |
| Changed         |      | changed.                               |     |
| 12 Not	Used     | 4096 | (Always	returns	0)                     |     |
| 13 Global	Error | 8192 | An	error	is	in	the	global	error	queue. |     |

| 14 Busy     | 16384 | The	instrument	is	busy. |
| ----------- | ----- | ----------------------- |
| 15 Not	Used | 32768 |                         |
(Always	returns	0)

Bit	14,	the	Busy	bit,	will	be	set	while	the	instrument	is	performing
long	commands,	such	as	MMEMory:IMPort:CONFig?.
This	register	is	cleared	when	it	is	read,	or	when	you	issue	a	*CLS
command.

Return Format
The query reads the operation event register and returns a decimal value
which corresponds to the binary-weighted sum of all bits set in the
register (see table above). For example, if bit 1 (decimal value = 2) and
bit 9 (decimal value = 512) are set, this command will return "+514".

Examples
The following command reads the questionable event register (bits 1 and
9 are set).
STAT:OPER?
Typical Response: +514

See Also
STATus Subsystem Introduction
STATus:OPERation:CONDition?
STATus:OPERation:ENABle

STATus:PRESet
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
STATus:PRESet

Description
This command clears all bits in the Questionable Data enable register,
the Alarm enable register, and the Standard Operation enable register.

Example
The following command clears all bits in the registers listed above.
STATus:PRESet

See Also
STATus Subsystem Introduction

STATus:QUEStionable:CONDition?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
STATus:QUEStionable:CONDition?

Description
This command queries the condition register for the Questionable Data
Register group. This is a read-only register and the bits are not cleared
when you read the register.
For more information on the Status System for the
instrument, see Status System Introduction.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
The	condition	register	bits	reflect	the	current	condition.	If	a
condition	is	no	longer	true,	the	corresponding	bit	is	cleared	in	the
condition	register.
The	following	table	lists	the	bit	definitions	for	the	Questionable
Data	Register.
| Bit	# | Bit	Name | Decimal | Definition |
| ----- | -------- | ------- | ---------- |
Value
| 0-10 Not	Used  |     | 1-1024     | (Always	returns	0)      |
| -------------- | --- | ---------- | ----------------------- |
| 11 Totalizer   |     | 2048       | A	totalizer	has	counted |
| Overflow       |     |            | past	its	limit.         |
| 12 Memory      |     | 4096       | The	reading	memory	has  |
| Overflow       |     |            | overflowed.             |
| 13-15 Not	Used |     | 8192-32768 | (Always	returns	0)      |

A	Factory	Reset	(*RST	command)	clears	all	bits	in	the	condition
register.

Return Format
The query reads the questionable condition register and returns a
decimal value which corresponds to the binary-weighted sum of all bits
set in the register (see table above). For example, if bit 11 (decimal value
= 2048) and bit 12 (decimal value = 4096) are set, this command will
return "6144".

Examples
The following command reads the condition register (bit 11 is set).
STAT:QUES:COND?
Typical Response: +2048

See Also
STATus Subsystem Introduction
STATus:QUEStionable:ENABle
STATus:QUEStionable[:EVENt]?

STATus:QUEStionable:ENABle
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
STATus:QUEStionable:ENABle <enable_val>
STATus:QUEStionable:ENABle?

Description
This command enables bits in the enable register for the Questionable
Data Register group. The selected bits are then reported to the Status
Byte.
For more information on the
Status System for the
instrument, see Status System
Introduction.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name         | Type    | Range	of   | Default    |
| ------------ | ------- | ---------- | ---------- |
|              |         | Values     | Value      |
| <enable_val> | Numeric | An	integer | This	is	a  |
|              |         | from	0	to  | required   |
|              |         | 65535,     | parameter. |
specifying
the	bits	to
enable	as	a
bit	sum.

Remarks
The	following	table	lists	the	bit	definitions	for	the	Questionable
Data	Register.
| Bit       | Bit	Name | Decimal | Definition            |
| --------- | -------- | ------- | --------------------- |
| #         |          | Value   |                       |
| 0 Voltage |          | 1       | The	instrument	has    |
| Overload  |          |         | experienced	a	voltage |
overload.
| 1 Current |     | 2   | The	instrument	has    |
| --------- | --- | --- | --------------------- |
| Overload  |     |     | experienced	a	current |
overload.
| 2 Not	Used     |     | 4   | (Always	returns	0) |
| -------------- | --- | --- | ------------------ |
| 3 Not	Used     |     | 8   | (Always	returns	0) |
| 4 Not	Used     |     | 16  | (Always	returns	0) |
| 5 Not	Used     |     | 32  | (Always	returns	0) |
| 6 Not	Used     |     | 64  | (Always	returns	0) |
| 7 Not	Used     |     | 128 | (Always	returns	0) |
| 8 Not	Used     |     | 256 | (Always	returns	0) |
| 9 Res	Overload |     | 512 | The	instrument	has |
experienced	a	resistance
overload.
| 10 Temperature |     | 1024 | The	instrument	has        |
| -------------- | --- | ---- | ------------------------- |
| Overload       |     |      | experienced	a	temperature |
overload.
| 11 Totalizer |     | 2048 | A	totalizer	has	counted |
| ------------ | --- | ---- | ----------------------- |
| Overflow     |     |      | past	its	limit.         |
| 12 Memory    |     | 4096 | The	reading	memory	has  |
| Overflow     |     |      | overflowed.             |

| 13 Not	Used | 8192  | (Always	returns	0) |
| ----------- | ----- | ------------------ |
| 14 Not	Used | 16384 | (Always	returns	0) |
| 15 Not	Used | 32768 | (Always	returns	0) |

Use	the	<enable_value>	parameter	to	specify	which	bits	will	be
reported	to	the	Status	Byte.	The	decimal	value	specified
corresponds	to	the	binary-weighted	sum	of	the	bits	you	wish	to
enable	in	the	register.	For	example,	to	enable	bit	0	(decimal	value
=	1)	and	bit	10	(decimal	value	=	1024),	the	corresponding	decimal
value	would	be	1025	(1	+	1024).
The	*CLS	(clear	status)	command	will	not	clear	the	enable	register
but	it	does	clear	all	bits	in	the	event	register.
The	*RST	command	has	no	effect	on	this	register.

Return Format
The query command reads the enable register and returns a decimal
value corresponding to the binary-weighted sum of all bits set in the
register. For example, if bit 0 (decimal value = 1) and bit 10 (decimal
value = 1024) are enabled, the query command will return +1025.

Examples
The following command enables bit 9 (decimal value = 512) in the
enable register.
STAT:QUES:ENAB 512
The following query returns which bits are enabled in the register.
STAT:QUES:ENAB?
Typical Response: +512

See Also
STATus Subsystem Introduction
STATus:QUEStionable:CONDition?
STATus:QUEStionable[:EVENt]?

STATus:QUEStionable[:EVENt]?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
STATus:QUEStionable[:EVENt]?

Description
This command queries the condition register for the Questionable Data
Register group. This is a read-destructive register and the bits are
cleared when you read the register.
For more information on the Status System for the
instrument, see Status System Introduction.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
The	following	table	lists	the	bit	definitions	for	the	Questionable
Data	Register.
| Bit       | Bit	Name | Decimal | Definition            |
| --------- | -------- | ------- | --------------------- |
| #         |          | Value   |                       |
| 0 Voltage |          | 1       | The	instrument	has    |
| Overload  |          |         | experienced	a	voltage |
overload.
| 1 Current |     | 2   | The	instrument	has    |
| --------- | --- | --- | --------------------- |
| Overload  |     |     | experienced	a	current |
overload.
| 2 Not	Used     |     | 4   | (Always	returns	0) |
| -------------- | --- | --- | ------------------ |
| 3 Not	Used     |     | 8   | (Always	returns	0) |
| 4 Not	Used     |     | 16  | (Always	returns	0) |
| 5 Not	Used     |     | 32  | (Always	returns	0) |
| 6 Not	Used     |     | 64  | (Always	returns	0) |
| 7 Not	Used     |     | 128 | (Always	returns	0) |
| 8 Not	Used     |     | 256 | (Always	returns	0) |
| 9 Res	Overload |     | 512 | The	instrument	has |
experienced	a	resistance
overload.
| 10 Temperature |     | 1024 | The	instrument	has        |
| -------------- | --- | ---- | ------------------------- |
| Overload       |     |      | experienced	a	temperature |
overload.
| 11 Totalizer |     | 2048 | A	totalizer	has	counted |
| ------------ | --- | ---- | ----------------------- |
| Overflow     |     |      | past	its	limit.         |
| 12 Memory    |     | 4096 | The	reading	memory	has  |
| Overflow     |     |      | overflowed.             |

| 13 Not	Used | 8192  | (Always	returns	0) |
| ----------- | ----- | ------------------ |
| 14 Not	Used | 16384 | (Always	returns	0) |
| 15 Not	Used | 32768 | (Always	returns	0) |

Once	a	bit	is	set,	it	remains	set	until	cleared	by	reading	the	event
register	or	the	*CLS	(clear	status)	command.
The	*RST	command	has	no	effect	on	this	register.

Return Format
The query reads the questionable event register and returns a decimal
value which corresponds to the binary-weighted sum of all bits set in the
register (see table above). For example, if bit 1 (decimal value = 2) and
bit 9 (decimal value = 512) are set, this command will return "+514".

Example
The following command reads the questionable event register (bits 1 and
9 are set).
STAT:QUES?
Typical Response: +514

See Also
STATus Subsystem Introduction
STATus:QUEStionable:ENABle
STATus:QUEStionable:CONDition?

SYSTem Subsystem Introduction
Command Summary
SYSTem:ALARm?
SYSTem:CPON
SYSTem:CTYPe?
SYSTem:DATE
SYSTem:DATE?
SYSTem:ERRor?
SYSTem:INTerface
SYSTem:INTerface?
SYSTem:LANGuage
SYSTem:LANGuage?
SYSTem:LFRequency?
SYSTem:LOCal
SYSTem:LOCK:NAME?
SYSTem:LOCK:OWNer?
SYSTem:LOCK:RELease
SYSTem:LOCK:REQuest?
SYSTem:PRESet
SYSTem:REMote
SYSTem:RWLock
SYSTem:SECurity[:IMMediate]
SYSTem:TIME
SYSTem:TIME?

SYSTem:TIME:SCAN?
SYSTem:VERSion?
LAN Configuration Commands
The instrument uses the
following LAN ports (34972A
only):
Port 5024 is used for
SCPI Telnet sessions.
Port 5025 is used for
Socket sessions.

LAN Configuration Introduction
Remote Interface Configuration Commands
SYSTem:COMMunicate:LAN:CONTrol?
SYSTem:COMMunicate:LAN:DHCP
SYSTem:COMMunicate:LAN:DHCP?
SYSTem:COMMunicate:LAN:DNS
SYSTem:COMMunicate:LAN:DNS?
SYSTem:COMMunicate:LAN:DOMain?
SYSTem:COMMunicate:LAN:GATEway
SYSTem:COMMunicate:LAN:GATEway?
SYSTem:COMMunicate:LAN:HOSTname
SYSTem:COMMunicate:LAN:HOSTname?
SYSTem:COMMunicate:LAN:IPADdress
SYSTem:COMMunicate:LAN:IPADdress?
SYSTem:COMMunicate:LAN:MAC?
SYSTem:COMMunicate:LAN:SMASk
SYSTem:COMMunicate:LAN:SMASk?
SYSTem:COMMunicate:LAN:TELNet:PROMpt
SYSTem:COMMunicate:LAN:TELNet:PROMpt?
SYSTem:COMMunicate:LAN:TELNet:WMESsage
SYSTem:COMMunicate:LAN:TELNet:WMESsage?
SYSTem:COMMunicate:LAN:UPDate
The instrument uses the following LAN ports (34972A only):

Port 5024 is used for SCPI Telnet sessions.
Port 5025 is used for Socket sessions.

SYSTem:COMMunicate:LAN:CONTrol?
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:CONTrol?

Description
This query returns the control connection port number for socket
communications.

Remarks
This query is only used when programming over sockets.
You can use the control socket connection to send a Device Clear
to the instrument or to detect pending Service Request (SRQ)
events.
This query always returns 0 if not sent from a socket connection.

Return Format
The query returns the control connection port number. If 0 is returned,
the interface does not support a Socket Control connection.

Examples
The following query returns the control connection port number.
SYST:COMM:LAN:CONT?
Typical Response: +5005

See Also
LAN Configuration Introduction

SYSTem:COMMunicate:LAN:DHCP
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:DHCP <mode>
SYSTem:COMMunicate:LAN:DHCP?

Description
This command disables or enables use of the Dynamic Host
Configuration Protocol (DHCP) for the instrument.
When DHCP is enabled (factory setting), the instrument will try to obtain
an IP address from a DHCP server. If a DHCP server is found, it will
assign a dynamic IP address, Subnet Mask, and Default Gateway to the
instrument. If a DHCP server is not found, the instrument uses AutoIP to
automatically configure its IP setting in the Automatic Private IP
Addressing range (169.254.xxx.xxx).
When DHCP is disabled, the instrument will use the static IP address,
Subnet Mask, and Default Gateway during power-on.
If you change the DHCP mode, you
must execute a
SYSTem:COMMunicate:LAN:UPDate
command to activate the setting.

Parameters
| Name   | Type    | Range	of     | Default   |
| ------ | ------- | ------------ | --------- |
|        |         | Values       | Value     |
| <mode> | Boolean | {OFF|0|ON|1} | This	is	a |
required
parameter.

Remarks
Most site LANs have a DHCP server.
If a DHCP LAN address is not assigned by a DHCP server, then
an AutoIP address static IP will be assumed after approximately
two minutes.
The DHCP setting is stored in non-volatile memory, and does not
change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).
The query returns the current setting only. This may differ from
what was just set if you have not yet executed a
SYSTem:COMMunicate:LAN:UPDate command.

Return Format
The query returns 0 (OFF) or 1 (ON).

Examples
The following command disables DHCP.
SYST:COMM:LAN:DHCP OFF SYST:COMM:LAN:UPDate
The following query returns the current DHCP setting.
SYST:COMM:LAN:DHCP?
Typical Response: 0

See Also
LAN Configuration Introduction
SYSTem:COMMunicate:LAN:GATEway
SYSTem:COMMunicate:LAN:IPADdress
SYSTem:COMMunicate:LAN:SMASk
SYSTem:COMMunicate:LAN:UPDate

SYSTem:COMMunicate:LAN:DNS
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:DNS "<address>"
SYSTem:COMMunicate:LAN:DNS? [{CURRent|STATic}]

Description
This command assign the IP address of the Domain Name System
server (DNS).
Contact your network administrator to determine whether DNS is being
used and for the correct address. If DHCP is available and enabled,
DHCP will auto-assign the DNS address. This auto-assigned DNS
address takes precedence over the static DNS address assigned with
this command.
If you change the DNS address, you
must execute a
SYSTem:COMMunicate:LAN:UPDate
command to activate the setting.

Parameters
| Name | Type | Range	of	Values | Default	Value |
| ---- | ---- | --------------- | ------------- |
<address> Quoted Specified	in	four-byte	dot This	is	a	required
|     | String | notation | parameter. |
| --- | ------ | -------- | ---------- |
("nnn.nnn.nnn.nnn"),	where
"nnn"	in	each	case	is	a	byte
value	in	the	range	0	through
255.

Remarks
The assigned DNS address is used for the DNS server if DHCP is
disabled. Otherwise, the DNS server address is auto-assigned by
DHCP.
The DNS address is stored in non-volatile memory, and does not
change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).

Return Format
The query form returns the address of the DNS server in the form
"nnn.nnn.nnn.nnn".
Note that the query version of the command has two optional
parameters. Specify "CURRent" (default) to read the DNS address
currently in use. Specify "STATic" to read the DNS address, static
gateway, or IP address currently stored in non-volatile memory within the
instrument. The DNS address stored in memory is used if DHCP is
disabled. If DHCP is enabled, it will auto-assign the DNS address, and
that DHCP assigned address can be read by specifying "CURRent".

Examples
The following command sets the static DNS address.
SYST:COMM:LAN:DNS "198.105.232.4"
SYST:COMM:LAN:UPDate
The following query returns the DNS address currently being used by the
instrument (the quotes are also returned).
SYST:COMM:LAN:DNS? CURR
Typical Response: "198.105.232.4"

See Also
LAN Configuration Introduction
SYSTem:COMMunicate:LAN:HOSTname
SYSTem:COMMunicate:LAN:UPDate

SYSTem:COMMunicate:LAN:DOMain?
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:DOMain?

Description
This query returns the current network domain.

Remarks
If the instrument has a DNS server, it looks up its domain name.

Return Format
The query reads the domain name and returns an ASCII string enclosed
in double quotes. If a domain name has not been assigned, a null string
( " " ) is returned.

Examples
The following query returns the domain name currently being used by
the instrument (the quotes are also returned).
SYST:COMM:LAN:DOM?
Typical Response: "example.com"

See Also
LAN Configuration Introduction
SYSTem:COMMunicate:LAN:DNS
SYSTem:COMMunicate:LAN:HOSTname

SYSTem:COMMunicate:LAN:GATEway
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:GATEway "<address>"
SYSTem:COMMunicate:LAN:GATEway? [{CURRent|STATic}]

Description
This command assigns the static gateway for the instrument.
Contact your network administrator to determine whether subnetting is
being used and for the correct address. If DHCP is enabled, DHCP will
auto-assign the gateway. This auto-assigned gateway takes precedence
over the static gateway assigned with this command.
If you change the gateway, you must
execute a
SYSTem:COMMunicate:LAN:UPDate
command to activate the setting.

Parameters
| Name | Type | Range	of	Values | Default	Value |
| ---- | ---- | --------------- | ------------- |
<address> Quoted Specified	in	four-byte	dot This	is	a	required
|     | String | notation | parameter. |
| --- | ------ | -------- | ---------- |
("nnn.nnn.nnn.nnn"),	where
"nnn"	in	each	case	is	a	byte
value	in	the	range	0	through
255.

Remarks
The assigned gateway is used if DHCP is disabled. Otherwise, the
gateway is auto-assigned by DHCP.
The static gateway is stored in non-volatile memory, and does not
change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).
If DHCP is enabled (see SYSTem:COMMunicate:LAN:DHCP
command), the static gateway is assigned by the DHCP server, so
the specified static gateway is not used. However, if DHCP is
turned off, the currently configured static gateway will be used.
A gateway value of "0.0.0.0" indicates that subnetting is not being
used.

Return Format
The query form returns the address of the gateway in the form
"nnn.nnn.nnn.nnn".
Note that the query version of the command has two optional
parameters. Specify "CURRent" (default) to read the static gateway
currently in use. Specify "STATic" to read the static gateway currently
stored in non-volatile memory within the instrument. The gateway stored
in memory is used if DHCP is disabled. If DHCP is enabled, it will auto-
assign the gateway can be read by specifying "CURRent".

Examples
The following command sets the static gateway.
SYST:COMM:LAN:GATEway "192.168.1.1"
SYST:COMM:LAN:UPDate
The following query returns the gateway currently being used by the
instrument (the quotes are also returned).
SYST:COMM:LAN:GATEway? CURR
Typical Response: "192.168.1.1"

See Also
LAN Configuration Introduction
SYSTem:COMMunicate:LAN:IPADdress
SYSTem:COMMunicate:LAN:SMASk
SYSTem:COMMunicate:LAN:DHCP
SYSTem:COMMunicate:LAN:UPDate

SYSTem:COMMunicate:LAN:HOSTname
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:HOSTname "<name>"
SYSTem:COMMunicate:LAN:HOSTname? [{CURRent|STATic}]

Description
This command assigns a host name to the instrument. The host name is
the host portion of the domain name, which is translated into an IP
address.
If you change the host name, you
must execute a
SYSTem:COMMunicate:LAN:UPDate
command to activate the setting.

Parameters
| Name   | Type   | Range	of	Values       | Default	Value |
| ------ | ------ | --------------------- | ------------- |
| <name> | Quoted | A	string	of	up	to	45  |               |
|        | ASCII  | characters.	The	first | This	is	a     |
required
|     | String | character	must	be	a	letter  |            |
| --- | ------ | --------------------------- | ---------- |
|     |        | (A-Z),	but	the	remaining	44 | parameter. |
characters	can	be	letters,
The	LXI	reset
numbers	(0-9),	or	dashes
value	is	A-
("-").	Blank	spaces	are	not
34970A-nnnnn
allowed.
or	A-34972A-
nnnnn,	where
nnnnn	is	the
last	5	digits	in
the	instrument's
serial	number.

Remarks
If Dynamic Domain Name System (DDNS) is available on your
network and your instrument uses DHCP, the host name is
registered with the Dynamic DNS service at power-on.
If DHCP is enabled (see SYSTem:COMMunicate:LAN:DHCP
command), the DHCP server can assign a different name if the
requested name is already in use on the network.
The host name is stored in non-volatile memory, and does not
change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).

Return Format
The query reads the host name and returns an ASCII string enclosed in
double quotes. If a host name has not been assigned, the query returns
a null string ("").
Note that the query version of the command has two optional
parameters. Specify "CURRent" (default) to read the host name that the
instrument is currently using. Specify "STATic" to read the desired host
name currently stored in non-volatile memory within the instrument
(which may not be the actual name currently in use on the network).

Examples
The following command defines a host name.
SYST:COMM:LAN:HOST "LAB1-34970A"
SYST:COMM:LAN:UPDate
The following query returns the host name currently being used by the
instrument (the quotes are also returned).
SYST:COMM:LAN:HOST? CURR or SYST:COMM:LAN:HOST?
Typical Response: "LAB1-34970A"

See Also
LAN Configuration Introduction
SYSTem:COMMunicate:LAN:DHCP
SYSTem:COMMunicate:LAN:DOMain?
SYSTem:COMMunicate:LAN:UPDate

SYSTem:COMMunicate:LAN:IPADdress
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:IPADdress "<address>"
SYSTem:COMMunicate:LAN:IPADdress? [{CURRent|STATic}]

Description
This command assigns the static IP address for the instrument.
If DHCP is enabled, DHCP will auto-assign the IP address. This auto-
assigned IP address takes precedence over the static IP address
assigned with this command.
If you change the IP address, you
must execute a
SYSTem:COMMunicate:LAN:UPDate
command to activate the setting.

Parameters
| Name | Type | Range	of	Values | Default	Value |
| ---- | ---- | --------------- | ------------- |
<address> Quoted Specified	in	four-byte	dot This	is	a	required
|     | String | notation | parameter. |
| --- | ------ | -------- | ---------- |
("nnn.nnn.nnn.nnn"),	where
"nnn"	in	each	case	is	a	byte
value	in	the	range	0	through
255.

Remarks
The assigned IP address is used if DHCP is disabled. Otherwise,
the IP address is auto-assigned by DHCP.
The IP address is stored in non-volatile memory, and does not
change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).
If DHCP is enabled (see SYSTem:COMMunicate:LAN:DHCP
command), the IP address is assigned by the DHCP server, so the
specified IP address is not used. However, if DHCP is turned off,
the currently configured IP address will be used.
IF DHCP is enabled, but a DHCP server is not available, the IP
address is determined by AutoIP.
If you are planning to use a static IP address on a site LAN,
contact your network administrator to obtain a fixed IP address to
be used exclusively for your instrument, along with the
corresponding subnet mask and gateway.

Return Format
The query form returns the address of the IP address of the instrument in
the form "nnn.nnn.nnn.nnn".
Note that the query version of the command has two optional
parameters. Specify "CURRent" (default) to read the IP address currently
in use. Specify "STATic" to read the IP address currently stored in non-
volatile memory within the instrument. The IP address stored in memory
is used if DHCP is disabled. If DHCP is enabled, it will auto-assign the IP
address, and that DHCP assigned address can be read by specifying
"CURRent".

Examples
The following command sets the static IP address.
SYST:COMM:LAN:IPAD "198.168.1.2"
SYST:COMM:LAN:UPDate
The following query returns the IP address currently being used by the
instrument (the quotes are also returned).
SYST:COMM:LAN:IPAD? CURR
Typical Response: "198.168.1.2"

See Also
LAN Configuration Introduction
SYSTem:COMMunicate:LAN:DHCP
SYSTem:COMMunicate:LAN:SMASk
SYSTem:COMMunicate:LAN:GATEway
SYSTem:COMMunicate:LAN:UPDate

SYSTem:COMMunicate:LAN:MAC?
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:MAC?

Description
This query reads the instrument's Media Access Control (MAC) address,
also known as the link-layer address, the Ethernet (station) address,
LANIC ID, or Hardware Address. This is an unchangeable 48-bit address
assigned by the manufacturer to each unique Internet device.
Your network administrator may need the instrument's
MAC address in order to assign a static IP address for
this device.

Remarks
The instrument's MAC address is unique to the instrument. It is set
at the factory and cannot be changed.
The MAC address is stored in non-volatile memory, and does not
change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).

Return Format
The query reads the MAC address and returns an ASCII string enclosed
in double quotes. The MAC address is represented as 12 hexadecimal
characters.

Examples
The following query returns the MAC address (the quotes are also
returned).
SYST:COMM:LAN:MAC?
Typical Response: "0030D3001041"

See Also
LAN Configuration Introduction
SYSTem:COMMunicate:LAN:IPADdress

SYSTem:COMMunicate:LAN:SMASk
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:SMASk "<mask>"
SYSTem:COMMunicate:LAN:SMASk? [{CURRent|STATic}]

Description
This command assigns a Subnet Mask for the instrument. The
instrument uses the Subnet Mask to determine whether a client IP
address is on the same local subnet. When a client IP address is on a
different subnet, all packets must be sent to the Default Gateway.
Contact your network administrator to determine whether subnetting is
being used and for the correct Subnet Mask.
If you change the subnet mask, you
must execute a
SYSTem:COMMunicate:LAN:UPDate
command to activate the setting.

Parameters
| Name   | Type   | Range	of	Values            | Default	Value      |
| ------ | ------ | -------------------------- | ------------------ |
| <mask> | Quoted | Specified	in	four-byte	dot |                    |
|        | String | notation                   | This	is	a	required |
parameter.
("nnn.nnn.nnn.nnn"),
	where	"nnn"	in	each	case
The	factory	default
is	a	byte	value	in	the	range
value	is
0	through	255.
"255.255.0.0".

Remarks
The assigned subnet mask is used if DHCP is disabled.
Otherwise, the subnet mask is auto-assigned by DHCP.
If DHCP is enabled (factory default), the subnet mask does not
need to be set.
If DHCP is enabled (see SYSTem:COMMunicate:LAN:DHCP
command), the subnet mask is assigned by the DHCP server, so
the specified subnet mask is not used. However, if DHCP is turned
off, the currently configured Subnet Mask will be used.
A value of "0.0.0.0" or "255.255.255.255" indicates that subnetting
is not being used.
The Subnet Mask is stored in non-volatile memory, and does not
change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).

Return Format
The query returns the Subnet Mask in the form "nnn.nnn.nnn.nnn".
Note that the query version of the command has two optional
parameters. Specify "CURRent" (default) to read the dynamic Subnet
Mask currently being used by the instrument. Specify "STATic" to read
the Subnet Mask currently stored in non-volatile memory within the
instrument (may not be the actual mask used by the instrument if DHCP
is enabled).

Examples
The following command sets the Subnet Mask.
SYST:COMM:LAN:SMAS "255.255.254.0"
SYST:COMM:LAN:UPDate
The following query returns the subnet mask currently being used by the
instrument (the quotes are also returned).
SYST:COMM:LAN:SMAS? CURR or SYST:COMM:LAN:SMAS?
Typical Response: "255.255.254.0"

See Also
LAN Configuration Introduction
SYSTem:COMMunicate:LAN:DHCP
SYSTem:COMMunicate:LAN:GATEway
SYSTem:COMMunicate:LAN:IPADdress
SYSTem:COMMunicate:LAN:UPDate

SYSTem:COMMunicate:LAN:TELNet:PROMpt
SYSTem:COMMunicate:LAN:TELNet:WMESsage
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:TELNet:PROMpt "<string>"
SYSTem:COMMunicate:LAN:TELNet:PROMpt?
SYSTem:COMMunicate:LAN:TELNet:WMESsage "<string>"
SYSTem:COMMunicate:LAN:TELNet:WMESsage?

Description
These commands set the command prompt and welcome message that
are displayed when you use a Telnet session to communicate with the
instrument.

Parameters
| Name     | Type   | Range	of	Values        | Default	Value |
| -------- | ------ | ---------------------- | ------------- |
| <string> | Quoted | A	string	of	up	to	15   |               |
|          | ASCII  | characters	(prompt)	or | "34972A>	"    |
(prompt)
|     | String | 63	characters	(welcome |     |
| --- | ------ | ---------------------- | --- |
message).
"Welcome	to
Keysight's	34972A
Switch/Measure
Unit"	(welcome
message)

Remarks
The Telnet port is an alternate way to send SCPI commands to the
instrument.
Port 5024 is used for SCPI Telnet sessions.
Telnet session can typically be started as follows from a host
computer shell:
telnet <IP_address> <port>
For example:
telnet 169.254.4.10 5024
To exit a Telnet session, press <Ctrl-D>.
The command prompt and welcome message are stored in non-
volatile memory, and they do not change when power has been off
or after a Factory Reset (*RST command).
The following image shows both the prompt and the welcome
message.

Return Format
The queries return the command prompt or welcome message as ASCII
strings enclosed in double quotes.

Examples
The following command defines the command prompt.
SYST:COMM:LAN:TELN:PROM "Command>"
The following query returns the command prompt currently being used
(the quotes are also returned).
SYST:COMM:LAN:TELN:PROM?
Typical Response: "Command>"

See Also
LAN Configuration Introduction

SYSTem:COMMunicate:LAN:UPDate
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:COMMunicate:LAN:UPDate

Description
This command updates all of the LAN changes. It disconnects all active
LAN and Web connections and restarts the LAN interface, possibly with
a new IP address, depending on how your instrument's IP address is
assigned.

Remarks
Executing this command is necessary to make the following
commands take effect:
SYSTem:COMMunicate:LAN:DHCP
SYSTem:COMMunicate:LAN:DNS
SYSTem:COMMunicate:LAN:GATEway
SYSTem:COMMunicate:LAN:HOSTname
SYSTem:COMMunicate:LAN:IPADdress
SYSTem:COMMunicate:LAN:SMASk
Be very careful when you execute this command, because your
instrument may not work on the LAN if you update the instrument
with invalid LAN settings.
If your instrument does not work after you execute this command,
push the LAN Reset front panel softkey to restore the settings to
reset values and reset the LAN, or use another I/O interface, such as
USB, to correct the settings.

Example
The commands below demonstrate a typical use model for setting and
applying LAN parameters.
SYST:COMM:LAN:DHCP OFF
SYST:COMM:LAN:IPADdress "192.168.1.2"
SYST:COMM:LAN:SMASk "255.255.0.0"
SYST:COMM:LAN:GATEway "192.168.1.1"
SYST:COMM:LAN:UPDate

See Also
LAN Configuration Introduction
SYSTem:COMMunicate:LAN:DHCP
SYSTem:COMMunicate:LAN:DNS
SYSTem:COMMunicate:LAN:GATEway
SYSTem:COMMunicate:LAN:HOSTname
SYSTem:COMMunicate:LAN:IPADdress
SYSTem:COMMunicate:LAN:SMASk

SYSTem:ALARm?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
SYSTem:ALARm?

Description
This query reads the alarm data from the alarm queue (one alarm event
is read and deleted from the queue each time this command is
executed). A record of up to 20 alarms can be stored in the instrument's
alarm queue.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
Each time you start a new scan, the instrument clears all readings
(including alarm data) stored in reading memory from the previous
measurement. Therefore, the contents of memory are always from
the most recent measurement.
Alarm data is retrieved in first-in-first-out (FIFO) order. The first
alarm returned is the first alarm that was stored.
Up to 20 alarms can be logged in the alarm queue. If more than 20
alarms are generated, they will be lost (only the first 20 alarms are
saved).
To retrieve scanned readings and alarm data from reading
memory without clearing the information, use the FETCh?
command.
The alarm queue is cleared by the *CLS (clear status) command,
when power is cycled, and by reading all of the entries. A Factory
Reset (*RST command) or Instrument Preset (SYSTem:PRESet
command) does not clear the alarm queue.

Return	Format
The	query	returns	one	string	each	time	it	is	executed.	It	also	reads	the
alarm	data	and	clears	one	alarm	event	from	the	alarm	queue.
The	query	returns	a	string	in	the	form	shown	below	(independent	of
FORMat:READing	commands):
| 	   | 1	Reading	with	Units	(26.195 | 4	Channel |
| --- | ---------------------------- | --------- |
|     | °C)                          | Number    |
| 	   | 2	Date	(November	21,	2004)   | 5	Alarm   |
Limit
Threshold
Crossed				(0
=	No	Alarm,
1	=	LO,	2	=
HI)
| 	   | 3	Time	of	Day	(3:30:23.000 | 6	Alarm |
| --- | -------------------------- | ------- |
|     | PM)                        | Number  |
(1-4)

Example
The following query reads one message from the alarm queue and
removes that message from the queue.
SYST:ALAR?
Typical Response: -1.17616000E-04
VDC,2004,11,21,15,54,50.184,103,1,3

See Also
SYSTem Subsystem Introduction

SYSTem:CPON
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
SYSTem:CPON <slot>

Description
This command resets the module in the specified slot to its power-on
state (CPON means "card power on"). See Factory Reset State for a
complete listing of the instrument's Factory configuration.

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <slot> | Discrete | {100|200|300|ALL} | This	is	a |
| ------ | -------- | ----------------- | --------- |
required
parameter.

Remarks
The various module cards are affected as follows:
Module Effect
34901A If any channel is
configured for a
measurement, this
command has no effect. If
no channel is configured,
this command opens all
channels.
34902A If any channel is
configured for a
measurement, this
command has no effect. If
no channel is configured,
this command opens all
channels.
34903A This command opens all
channels.
34904A This command opens all
channels.
34905A This command closes
channels 11 and 21.
34906A This command closes
channels 11 and 21.
34907A This command resets all
channels not involved in
scan to the power-on
state.

34908A If any channel is
configured for a
measurement, this
command has no effect. If
no channel is configured,
this command opens all
channels.
This command does not reset the internal DMM.
The instrument will produce an error if you are actively scanning
and try to execute a SYSTem:CPON for a card that is involved in
the scan.
To reset the modules in all three slots in the instrument, use the
ALL keyword shown above.

Example
The following command resets the module in slot 200.
SYST:CPON 200

See Also
SYSTem Subsystem Introduction
SYSTem:PRESet
*RST

SYSTem:CTYPe?
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
SYSTem:CTYPe? <slot>

Description
This query returns the identity of the plug-in module in the specified slot.
The table below shows the plug-in modules available for the Keysight
34970A/34972A.
Model Module
Number Description
34901A 20 Channel
Multiplexer
(2/4-wire)
Module
34902A 16 Channel
Multiplexer
(2/4-wire)
Module
34903A 20 Channel
Actuator/GP
Switch Module
34904A 4 x 8 Two-Wire
Matrix Module
34905A 2 GHz Dual 1:4
RF Mux, 50
Ohm Module
34906A 2 GHz Dual 1:4
RF Mux, 75
Ohm Module
34907A Multifunction
Module
34908A 40 Channel
Single-Ended
Multiplexer

Module

Parameters
| Name   | Type Range	of	Values  | Default	Value |
| ------ | --------------------- | ------------- |
| <slot> | Numeric {100|200|300} | This	is	a     |
required
parameter.

Return Format
The query returns comma-delimited fields of ASCII characters, as
shown below. To read the string into your computer, be sure to
dimension a string variable with at least 43 characters.
<Company Name>,<Card Model Number>,<Serial Number>,
<Firmware Rev>
For the 34970A, the <Company Name> is HEWLETT-PACKARD.
For the 34972A, the <Company Name> is Keysight Technologies.
If you have used the SYSTem:LANGuage command to set the
language to "34970A", the query will also return the company
name as HEWLETT-PACKARD.
The <Card Model Number> is either a number from 34901A
through 34908A. The number 0 is returned for the <Serial
Number> field. The Firmware Revision has the form R.R and
indicates the revision of firmware currently in use on the specified
module.
If the specified slot is empty, the command responds with either
Keysight Technologies,0,0,0 (34972A) or HEWLETT-
PACKARD,0,0,0 (34970A).

Example
The following command returns the identity of the module in slot 300 of a
34972A.
SYST:CTYP? 300
Typical Response: Keysight Technologies,34907A,0,1.0

See Also
SYSTem Subsystem Introduction
SYSTem:CTYPe?
*IDN?

SYSTem:DATE
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
SYSTem:DATE <yyyy>,<mm>,<dd>
SYSTem:DATE?

Description
During a scan, the instrument stores all readings and alarms with the
current time and date. This command sets the instrument calendar.

Parameters
| Name | Type | Range	of | Default	Value |
| ---- | ---- | -------- | ------------- |
Values
| <yyyy> | Numeric | The	current | This	is	a |
| ------ | ------- | ----------- | --------- |
|        |         | year        | required  |
parameter.
| <mm> | Numeric | The	current | This	is	a |
| ---- | ------- | ----------- | --------- |
|      |         | month       | required  |
parameter.
| <dd> | Numeric | The	current | This	is	a  |
| ---- | ------- | ----------- | ---------- |
|      |         | day	of	the  | required   |
|      |         | current     | parameter. |
month

Remarks
When shipped from the factory, the instrument is set to the current
time and date for Greenwich Mean Time (GMT).
The calendar setting is stored in non-volatile memory, and does
not change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).

Return Format
The query returns three comma-separated values in the form
"yyyy,mm,dd".

Examples
The following command sets the instrument date to September 12, 2009.
SYST:DATE 2009,09,12
The following query returns the date.
SYST:DATE?
Typical Response: 2009,09,12

See Also
SYSTem Subsystem Introduction
SYSTem:TIME

SYSTem:ERRor?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
SYSTem:ERRor?

Description
This query reads and clears one error from the instrument's error queue.
A record of up to 10 errors (34970A) or 20 errors (34972A) is stored in
the instrument’s error queue. Errors are retrieved in first-in-first-out
(FIFO) order. The error queue is cleared by the *CLS (clear status)
command or when power is cycled. The errors are also cleared when
you read the queue.
For a complete listing of the error messages for the Keysight
34970A/34972A, see SCPI Error Messages.

Remarks
The instrument beeps once each time a command syntax or
hardware error is generated. The front-panel ERROR annunciator
turns on when one or more errors are currently stored in the error
queue.
Errors are retrieved in first-in-first-out (FIFO) order. The first error
returned is the first error that was stored. Once you have read all
of the interface-specific errors, the errors in the global error queue
are retrieved.
Errors are cleared as you read them. When you have read all
errors from the interface-specific error queue (errors from the
current I/O session) and global error queue (errors from any I/O
session), the ERROR annunciator turns off and the errors are
cleared.
If more than the maximum number of errors have occurred (10
errors on the 34970A or 20 errors on the 34972A), the last error
stored in the queue (the most recent error) is replaced with
-350,"Error queue overflow". No additional errors are stored until
you remove errors from the queue. If no errors have occurred
when you read the error queue, the instrument responds with
+0,"No error".
The front panel reports errors from all I/O sessions as well as the
global error queue. To read the error queue from the front panel,
use the View key.
Error conditions are also summarized in the Status Byte Register.
For more information on the Status System for the instrument, see
Status System Introduction.
The interface-specific and global error queues are cleared by the
*CLS (Clear Status) command and when power is cycled. The
errors are also cleared when you read the error queue. The error

queue is not cleared by a Factory Reset (*RST command) or an
Instrument Preset (SYSTem:PRESet command).

Return Format
The query reads and clears one error string from the error queue. The
error string may contain up to 160 characters and consists of an error
number and an error string enclosed in double quotes. For example:
-113,"Undefined header"

Example
The following query reads and clears one error.
SYST:ERR?
Typical Response: -101,"Invalid character"

See Also
SYSTem Subsystem Introduction
*SRE

SYSTem:INTerface
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34970A
only.

Syntax
SYSTem:INTerface {GPIB|RS232}
SYSTem:INTerface?

Description
This command/query selects the remote interface for the instrument.
Only one interface can be enabled at a time. The GPIB interface is
selected when the instrument is shipped from the factory.

Remarks
This command only has effect on the 34970A. The 34972A will
accept the command, but the command will have no effect. Both
the parameters and the response to the query are meaningless.
The non-selected interface is disabled immediately.

Return Format
The query returns GPIB or RS232. On the 34972A, the (meaningless)
response is GPIB.

Examples
The following command sets the remote interface to RS-232 on a
34970A.
SYST:INT RS232
The following query returns the remote interface for a 34970A.
SYST:INT?
Typical Response: RS232

See Also
SYSTem Subsystem Introduction
SYSTem:LOCal
SYSTem:REMote

SYSTem:LANGuage
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:LANGuage <language>
SYSTem:LANGuage?

Description
This command allows you to specify whether the instrument should
behave as a 34970A or a 34972A.

Parameters
| Name | Type | Range	of	Values | Default |
| ---- | ---- | --------------- | ------- |
Value
| <language> | Discrete | {"34970A"|"34972A"} | This	is	a |
| ---------- | -------- | ------------------- | --------- |
required
parameter.

Remarks
This command only affects the output of the *IDN? and
SYSTem:CTYPe? queries.
If you do not specify 34970A or 34972A, the instrument will
dispatch an error message.

Return Format
The query returns "34970A" or "34972A".

Examples
The following command sets the language to 34970A.
SYST:LANG "34970A"
The following query returns the current <language> setting for the
instrument.
SYST:LANG?
Typical Response: "34970A"

See Also
SYSTem Subsystem Introduction
*IDN?
SYSTem:CTYPe?

SYSTem:LFRequency?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
SYSTem:LFRequency?

Description
This command returns the current power-line reference frequency used
by the instrument. When you apply power to the instrument, the
instrument automatically detects the power-line frequency (50 Hz, 60 Hz,
or 400 Hz) and uses this value to determine the integration time used.

Remarks
If the detected power line frequency is 400 Hz, the 50 Hz
reference value is actually used (a subharmonic of 400 Hz).
The instrument uses this information in determining integration
time in NPLC commands.
The reference frequency setting is stored in volatile memory and
will be lost when power is turned off. The instrument automatically
measures the power-line frequency (50 Hz, 60 Hz, or 400 Hz) at
power-on.

Return Format
The command returns "50" (for 50 Hz or 400 Hz) or "60" indicating the
present reference frequency setting.

Example
The following query returns the power line frequency.
SYST:LFR?
Typical Response: +60

See Also
SYSTem Subsystem Introduction

SYSTem:LOCal
SYSTem:REMote
SYSTEM:RWLock
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
SYSTem:LOCal
SYSTem:REMote
SYSTem:RWLock

Description
These commands place the instrument in either the local, remote or local
lockout (LLO) mode.

Remarks
In the LOCal mode, all keys on the front panel are fully functional.
In the REMote mode, most keys on the front panel are disabled.
The exceptions are the Local, Mon and View keys. Also, the knob
and the arrows above it are enabled.
In the local lockout mode (RWLock), all keys on the front panel are
disabled, including the Local key.
These commands are not allowed over GPIB on the 34970A.

Examples
The following command puts the instrument in local mode.
SYST:LOC
The following command puts the instrument in remote mode.
SYST:REMote

See Also
SYSTem Subsystem Introduction
SYSTem:INTerface

SYSTem:LOCK:NAME?
Syntax | Description | Parameters | Remarks | Return Format | Example
This functionality is available on the 34972A
only.

Syntax
SYSTem:LOCK:NAME?

Description
This query returns the I/O interface name of the I/O session sending the
query. You can use the returned name to determine whether the I/O
session owns the interface lock by comparing it to the value returned by
SYSTem:LOCK:OWNer?.

Remarks
Use this command to determine the lock name for the interface
that you are using. Then use the SYSTem:LOCK:OWNer?
command to determine which interface, if any, has the lock. Once
you have executed both of these commands, you can compare the
results to determine whether you have the lock.
This query is sometimes confused with the
SYSTem:LOCK:OWNer? query. The difference is that
SYSTem:LOCK:OWNer? returns the name of the interface that
has the lock, and SYSTem:LOCK:NAME? returns the name of the
current interface, regardless of whether it has the lock.

Return Format
The query returns USB or LAN<IP Address> indicating the I/O interface
being used by the querying computer. The IP address is four integers
separated by periods, such as 156.140.79.29, and there is no space
between the word LAN and the <IP Address>. Therefore, a typical LAN
with an IP address would be returned as LAN156.140.79.29.

Example
The following query returns the name of the I/O interface in use by the
querying computers.
SYST:LOCK:NAME?
Typical Response: "LAN169.254.149.35"

See Also
SYSTem:LOCK:OWNer?
SYSTem:LOCK:RELease
SYSTem:LOCK:REQuest?

SYSTem:LOCK:OWNer?
Syntax | Description | Parameters | Remarks | Return Format | Example
This functionality is available on the 34972A
only.

Syntax
SYSTem:LOCK:OWNer?

Description
This query returns the name of the I/O interface that currently has a lock.

Remarks
If the value returned by this query matches the value returned by
SYSTem:LOCK:NAME?, then the I/O session sending this query
owns the lock.
When a lock is active, Bit 10 in the Standard Operation Register
will be set (see STATus:OPERation:CONDition? command). When
there is no active lock on any I/O interface, this bit will be cleared.
This query is sometimes confused with the
SYSTem:LOCK:NAME? query. The difference is that
SYSTem:LOCK:OWNer? returns the name of the interface that
has the lock, and SYSTem:LOCK:NAME? returns the name of the
current interface, regardless of whether it has the lock.

Return Format
The query returns USB or LAN<IP Address> indicating the I/O interface
that currently has a lock. If no interface has a lock, the query returns
NONE. The IP address is four integers separated by periods, such as
156.140.79.29, and there is no space between the word LAN and the <IP
Address>. Therefore, a typical LAN with an IP address would be
returned as LAN156.140.79.29.

Example
The following query returns the name of the I/O interface that currently
has a lock.
SYST:LOCK:OWN?
Typical Response: "USB"

See Also
SYSTem:LOCK:NAME?
SYSTem:LOCK:RELease
SYSTem:LOCK:REQuest?

SYSTem:LOCK:RELease
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:LOCK:RELease

Description
This command decrements the lock count by one and releases the
instrument lock.

Remarks
When a lock is active, Bit 10 in the Standard Operation Register
will be set (see STATus:OPERation:CONDition? command). When
the lock is released, this bit is cleared.

Examples
The following command decreases the lock count by one.
SYST:LOCK:REL
The following series of commands illustrates usage.
Initial State = unlocked, Count = 0
<FROM USB> SYST:LOCK:REQ? returns +1
(request successful)
State = locked, Count = 1
<FROM LAN> SYST:LOCK:REQ? returns +0
because USB has lock
State = locked, Count = 1
<FROM USB> SYST:LOCK:REQ? returns +1
(request successful)
State = locked, Count = 2
<FROM USB> SYST:LOCK:REL
State = locked, Count = 1
<FROM USB> SYST:LOCK:REL
State = unlocked, Count = 0
Note that for each successful lock request, a lock release is required.
Two requests require two releases.

See Also
SYSTem:LOCK:NAME?
SYSTem:LOCK:OWNer?
SYSTem:LOCK:REQuest?

SYSTem:LOCK:REQuest?
Syntax | Description | Parameters | Remarks | Return Format | Examples
This functionality is available on the 34972A
only.

Syntax
SYSTem:LOCK:REQuest?

Description
This command issues a request to lock the instrument's configuration to
a single I/O interface. This allows you to lock the instrument or share the
instrument with other computers.

Remarks
When a request is granted, only I/O sessions from the interface
which was granted the lock will be allowed to change the state of
the instrument. From the other I/O interfaces, you can query the
state of the instrument but no instrument configuration changes or
measurements are allowed.
Lock requests can be nested and each request will increase the
lock count by 1. For every request, you will need a release from
the same I/O interface (see SYSTem:LOCK:RELease command).
Instrument locks are handled at the I/O interface level (USB or
sockets) and you are responsible for all coordination between
threads and/or programs on that interface.
Locks from socket sessions will be automatically released when a
socket disconnect is detected.
When a lock is granted, Bit 10 in the Standard Operation Register
will be set (see STATus:OPERation:CONDition? command).

Return Format
The command immediately returns +1 if the lock request is granted or +0
if denied.

Examples
The following command requests a lock of the current I/O interface.
SYST:LOCK:REQ?
Typical Response: +1
The following series of commands illustrates usage.
Initial State = unlocked, Count = 0
<FROM USB> SYST:LOCK:REQ? returns +1
(request successful)
State = locked, Count = 1
<FROM LAN> SYST:LOCK:REQ? returns +0
because USB has lock
State = locked, Count = 1
<FROM USB> SYST:LOCK:REQ? returns +1
(request successful)
State = locked, Count = 2
<FROM USB> SYST:LOCK:REL
State = locked, Count = 1
<FROM USB> SYST:LOCK:REL
State = unlocked, Count = 0

Note that for each successful lock request, a lock release is required.
Two requests require two releases.

See Also
SYSTem:LOCK:NAME?
SYSTem:LOCK:OWNer?
SYSTem:LOCK:RELease

SYSTem:PRESet
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
SYSTem:PRESet

Description
This command presets the instrument to a known configuration.

Remarks
See Instrument Preset State for a complete listing of the
instrument’s preset state.
This command is equivalent to selecting PRESET from the front-
panel Sto/Rcl Menu.

Example
The following command returns the instrument to its preset state.
SYST:PRES

See Also
SYSTem Subsystem Introduction
*RST
SYSTem:CPON

SYSTem:SECurity:IMMediate
Syntax | Description | Parameters | Remarks | >Return Format| Example
This functionality is available on the 34972A
only.

Syntax
SYSTem:SECurity:IMMediate

Description
This command clears and sanitizes all instrument memory except for the
instrument's firmware, MAC address, calibration parameters, and serial
number. It then reboots the instrument to the new memory state. This
command is typically used to clear all memory before removing the
instrument from a secure area.
This command is not recommended for use in
routine applications because of the possibility of
unintended loss of data.

Remarks
This command initializes all instrument settings to their Factory
Reset (*RST command) values.
All I/O settings, such as the IP address, are returned to their
factory settings.
This command will not clear an attached USB storage device.
The command clears and sanitizes all user files on the internal file
system.

Example
The following command clears all instrument memory other than the
instrument's firmware, MAC address, calibration parameters, and serial
number.
SYST:SEC:IMM

See Also
SYSTem Subsystem Introduction
*RST

SYSTem:TIME
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
SYSTem:TIME <hh>,<mm>,<ss.sss>
SYSTem:TIME?

Description
During a scan, the instrument stores all readings and alarms with the
current time and date. This command sets the instrument clock (based
on a 24-hour clock).

Parameters
| Name | Type    | Range	of        | Default    |
| ---- | ------- | --------------- | ---------- |
|      |         | Values          | Value      |
| <hh> | Numeric | The	hour	in	24- | This	is	a  |
|      |         | hour	clock      | required   |
|      |         | format,	from	0  | parameter. |
to	23
| <mm> | Numeric | The	minutes, | This	is	a |
| ---- | ------- | ------------ | --------- |
|      |         | from	0	to	59 | required  |
parameter.
| <ss.sss> | Numeric | The	seconds, | This	is	a  |
| -------- | ------- | ------------ | ---------- |
|          |         | with	1	ms    | required   |
|          |         | resolution,  | parameter. |
from	00.000	to
59.999

Remarks
When shipped from the factory, the instrument is set to the current
time and date for Greenwich Mean Time (GMT).
The clock setting is stored in non-volatile memory, and does not
change when power has been off, after a Factory Reset (*RST
command), or after an Instrument Preset (SYSTem:PRESet
command).

Return Format
The query returns three comma-separated values in the form
"hh,mm,sss.ss".

Examples
The following command sets the clock to 3:30:23.000 PM.
SYST:TIME 15,30,23.000
The following query returns the current time.
SYST:TIME?
Typical Response: 15,30,23.000

See Also
SYSTem Subsystem Introduction
SYSTem:DATE
SYSTem:TIME

SYSTem:TIME:SCAN?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
SYSTem:TIME:SCAN?

Description
This query returns the time at the start of the scan.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Remarks
You can read the time at any time, even during a scan.
This command is not affected by the
FORMat:READing:TIME:TYPE command, which selects the time
format for storing scanned data in memory (absolute time versus
relative time).
This command is not affected by the CALCulate:AVERage:CLEar
command, which clears all values from the statistics registers.
The instrument clears all stored data on all channels when a new
scan is started, after a Factory Reset (*RST command), or after an
Instrument Preset (SYSTem:PRESet command).

Return Format
The query returns a string indicating the time and date at the start of the
most recent scan.
The string returned has the form yyyy,mm,dd,hh,mm,ss.sss:
yyyy is the year
mm is the month
dd is the day of the month
hh is the hour in 24-hour format
mm is the minutes
ss.sss is the seconds (with 1 ms resolution)
For example:

Example
The following query returns the time and date at the start of the most
recent scan.
SYST:TIME:SCAN?
Typical Response: 2009,07,26,22,03,10.314

See Also
SYSTem Subsystem Introduction
SYSTem:DATE
SYSTem:TIME

SYSTem:VERSion?
Syntax | Description | Parameters | Remarks | Return Format | Example

Syntax
SYSTem:VERSion?

Description
This query returns the version of the SCPI (Standard Commands for
Programmable Instruments) standard with which the instrument is in
compliance. The instrument complies with the rules and conventions of
the indicated version of the SCPI standard.
You cannot query the
SCPI version from the
front panel.

Return Format
The instrument returns the version in the form YYYY.V, where YYYY is
the year and V is the version number.

Example
The following query returns the version number of the software.
SYST:VERS?
Typical Response: 1994.0

See Also
SYSTem Subsystem Introduction

TRIGger Subsystem Introduction
Command Summary
TRIGger:COUNt
TRIGger:COUNt?
TRIGger:SOURce
TRIGger:SOURce?
TRIGger:TIMer
TRIGger:TIMer?

TRIGger:COUNt
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
TRIGger:COUNt {<count>|MIN|MAX|INFinity}
TRIGger:COUNt?

Description
This command specifies the number of times to sweep through the scan
list. A sweep is one pass through the scan list. The scan stops when the
number of specified sweeps has occurred.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name    | Type    | Range	of | Default   |
| ------- | ------- | -------- | --------- |
|         |         | Values   | Value     |
| <count> | Numeric |          | This	is	a |
An	integer
required
|     |     | from	1	to | parameter. |
| --- | --- | --------- | ---------- |
50,000
triggers,	or
continuous
(INFinity).
MIN	=	1
MAX	=	50,000

Remarks
After setting the trigger count, you must place the internal DMM in
the "wait-for-trigger" state using the INITiate or READ? command.
A trigger will not be accepted from the selected trigger source (see
TRIGger:SOURce command) until the internal DMM is in the
"wait-for-trigger" state.
a. For the BUS source, the trigger count sets the number of *TRG
commands that will be accepted before returning to the "idle"
trigger state.
b. For the EXTernal source, the trigger count sets the number of
external pulses that will be accepted before returning to the "idle"
trigger state.
c. For the ALARmx source, the trigger count sets the number of
alarms that will be accepted before returning to the "idle" trigger
state.
d. For the TIMer source, the trigger count sets the number of times
the instrument will sweep through the scan list and therefore
determines the overall duration of the scan.
You can store at least 50,000 readings in memory and all readings
are automatically time stamped. If memory overflows, the new
readings will overwrite the first (oldest) readings stored; the most
recent readings are always preserved.
To set the trigger-to-trigger interval (in seconds) for measurements
on the channels in the present scan list, use the TRIGger:TIMer
command.
The CONFigure and MEASure? commands automatically set the
trigger count to 1.
The instrument sets the trigger count to 1 after a Factory Reset

(*RST command). An Instrument Preset (SYSTem:PRESet
command) or Card Reset (SYSTem:CPON command) does not
change the setting.

Return Format
The query returns the scan count in the form "+1.00000000E+01". For a
continuous trigger (INFinity), the count is returned as "9.90000200E+37".

Examples
The following program segment configures two channels for DC voltage
measurements, puts the channels in the scan list (the scan list is
redefined), and sets the trigger count to 10. For each trigger received,
one reading is returned for each channel (20 readings total).
CONF:VOLT:DC 10,0.003,(@103,108)
ROUT:SCAN (@103,108)
TRIG:COUN 10
INIT
The following program segment configures the current scan list for an
AC voltage measurement and sets the trigger count to 5. For each
trigger received, one reading is returned (5 readings total).
CONF:VOLT:AC 10,0.001,(@205,206,208)
TRIG:COUN 5
INIT
The following query returns the current trigger count.
TRIG:COUN?
Typical Response: +5.00000000E+00

See Also
TRIGger Subsystem Introduction
ROUTe:CHANnel:ADVance:SOURce
ROUTe:SCAN
TRIGger:SOURce
TRIGger:TIMer

TRIGger:SOURce
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
TRIGger:SOURce <source>
TRIGger:SOURce?

Description
Select the trigger source to control the onset of each sweep through the
scan list (a sweep is one pass through the scan list). The instrument will
accept a software (bus) command, an immediate (continuous) scan
trigger, an external TTL trigger pulse, an alarm-initiated action, or an
internally paced timer.
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
| Name     | Type     | Range	of | Default   |
| -------- | -------- | -------- | --------- |
|          |          | Values   | Value     |
| <source> | Discrete |          | This	is	a |
{BUS|
required
|     |     | IMMediate | parameter. |
| --- | --- | --------- | ---------- |
|	EXTernal	|
|     |     | ALARm1|  | The	factory |
| --- | --- | -------- | ----------- |
|     |     | ALARm2	| | default	is  |
|     |     | ALARm3	| | IMMediate.  |
ALARm4	|
TIMer}
IMMediate
=
Continuous
scan
trigger
BUS	=
Software
trigger
EXTernal	=
An	external
TTL	pulse
trigger
ALARm	=
Trigger	on
an	alarm
TIMer	=
Internally
paced
timer
trigger

Remarks
For the IMMediate (continuous) source, the trigger signal is always
present. When you place the instrument in the "wait-for-trigger"
state, the trigger is issued immediately.
The READ? and MEASure commands and queries cannot be
used to take readings when the trigger source is BUS. This is
called a trigger deadlock condition.
For the BUS (software) source, the instrument is triggered by the
*TRG command received over the remote interface. The *TRG
command will not be accepted unless the instrument is in the
"wait-for-trigger" state (see INITiate command). If the instrument
receives an external trigger before the next "waiting for trigger"
state, it will buffer one *TRG command and then ignore any
additional triggers received (no error is generated).
For the EXTernal source, the instrument will accept a hardware
trigger applied to the rear-panel Ext Trig Input line (Pin 6). The
instrument takes one sweep through the scan list each time a low-
true TTL pulse is received. If the instrument receives an external
trigger but is not in the "wait-for-trigger" state, it will buffer one
trigger and then ignore any additional triggers received (no error is
generated). Also, if the trigger source is BUS, you can use the
scan button as a trigger.
For the ALARmx source, the instrument is triggered each time a
reading crosses an alarm limit on a channel. See the
OUTPut:ALARm<n>:SOURce command for more information.
With this source, you can use the Monitor mode (see
ROUTe:MONitor:STATe command) to continuously take readings
on a selected channel and wait for an alarm on that channel.
Digital input and totalizer channels do not have to be part of the
active scan list to be monitored.

For the TIMer source, you control the trigger-to-trigger interval (in
seconds) for measurements on the channels in the present scan
list. Use the TRIGger:TIMer command to set the wait period.
After selecting the trigger source, you must place the instrument in
the "wait-for-trigger" state using the INITiate or READ? command.
A trigger will not be accepted from the selected trigger source until
the instrument is in the "wait-for-trigger" state.
Although the TRIGger:SOURce command shares some of the
same signals as the ROUTe:CHANnel:ADVance:SOURce
command (used for external scanning), they cannot be set to the
same source (except IMMediate). If you attempt to select the
same source, an error is generated and the TRIGger:SOURce is
reset to IMMediate.
The CONFigure and MEASure? commands automatically set the
trigger source to IMMediate.
The instrument selects the immediate trigger source after a
Factory Reset (*RST command). An Instrument Preset
(SYSTem:PRESet command) or Card Reset (SYSTem:CPON
command) does not change the setting.

Return Format
The query returns the trigger source as "BUS", "IMM", "EXT", "ALAR1",
"ALAR2", "ALAR3", "ALAR4", or "TIM".

Examples
The following program segment selects the external trigger source. In
this configuration, the instrument sweeps through the scan list once each
time a low-true TTL pulse is received on the rear-panel Ext Trig Input line
(Pin 6).
TRIG:SOUR EXT
INIT
The following program segment selects the bus (software) trigger
source. Note that the *TRG command will not be accepted unless the
internal DMM is in the "wait-for-trigger" state.
TRIG:SOUR BUS
INIT
*TRG
The following program segment selects the alarm source and configures
the instrument to scan when an alarm is reported on Alarm 1. The
Monitor mode is used to evaluate alarm conditions on the selected
channel.
ROUT:SCAN (@103) !Set the scan list to a single channel
TRIG:SOUR ALARM1 !Select trigger source
OUTP:ALAR:SOUR (@103)
CALC:LIM:UPP 10.25,(@103) !Set upper alarm limit
CALC:LIM:UPP:STAT ON,(@103) !Enable alarms
ROUT:MON (@103) !Select monitor channel
ROUT:MON:STAT ON !Enable monitor mode
INIT

The following program segment selects the timer source and sets the
scan interval to 30 milliseconds.
TRIG:SOUR TIMER !Select trigger
source
TRIG:TIM 30E-03 !Scan interval is 30
ms
INIT
The following query returns the trigger source currently selected.
TRIG:SOUR?
Typical Response: EXT

See Also
TRIGger Subsystem Introduction
*TRG
OUTPut:ALARm{1|2|3|4}:SOURce
ROUTe:CHANnel:ADVance:SOURce
ROUTe:MONitor:STATe
TRIGger:TIMer

TRIGger:TIMer
Syntax | Description | Parameters | Remarks | Return Format | Examples

Syntax
TRIGger:TIMer {<seconds>|MIN|MAX}
TRIGger:TIMer? [{MIN|MAX}]

Description
This command sets the trigger-to-trigger interval (in seconds) for
measurements on the channels in the present scan list. This command
defines the time from the start of one trigger to the start of the next
trigger, up to the specified trigger count (see TRIGger:COUNt
command).
Used With:
34901A 20 Channel Multiplexer (2/4-wire) Module
34902A 16 Channel Multiplexer (2/4-wire) Module
34907A Multifunction Module (digital input and totalizer channels
only)
34908A 40 Channel Single-Ended Multiplexer Module

Parameters
Name Type Range of Values Default
Value
<seconds> Numeric This is a
A number from required
0 seconds to parameter.
359,999 with
1 ms
resolution.
MIN = 0
seconds,
MAX = 359,999
seconds
Note that
359,999 is one
second less
than 100 hours.

Remarks
The scan interval applies to the TIMer trigger source as set by the
TRIGger:SOURce command.
If you are using the multiplexer modules, an error is generated if
the internal DMM is disabled (see INSTrument:DMM command) or
not installed in the mainframe. The internal DMM is not required
for operations on the digital modules.
If the scan interval is less than the time required to measure all
channels in the scan list, the instrument will scan continuously, as
fast as possible (no error is generated).
The CONFigure and MEASure? commands automatically set the
trigger interval to 1 second and the trigger count to 1 sweep.
The instrument sets the scan interval to immediate (0 seconds)
after a Factory Reset (*RST command). An Instrument Preset
(SYSTem:PRESet command) or Card Reset (SYSTem:CPON
command) does not change the setting.

Return Format
The query returns the scan-to-scan interval in seconds in the form
"+1.00000000E+01".

Examples
The following program segment sets the trigger interval to 30
milliseconds.
TRIG:SOUR TIMER
TRIG:TIM 30E-03
The following query returns the trigger interval in seconds.
TRIG:TIM?
Typical Response: +3.00000000E-02

See Also
TRIGger Subsystem Introduction
TRIGger:COUNt
TRIGger:SOURce

Commands A-Z
A – C | D - L | M - R | S | T - W

A
ABORt

C
CALCulate:AVERage:AVERage?
CALCulate:AVERage:CLEar
CALCulate:AVERage:COUNt?
CALCulate:AVERage:MAXimum?
CALCulate:AVERage:MAXimum:TIME?
CALCulate:AVERage:MINimum?
CALCulate:AVERage:MINimum:TIME?
CALCulate:AVERage:PTPeak?
CALCulate:COMPare:DATA
CALCulate:COMPare:DATA?
CALCulate:COMPare:MASK
CALCulate:COMPare:MASK?
CALCulate:COMPare:STATe
CALCulate:COMPare:STATe?
CALCulate:COMPare:TYPE
CALCulate:COMPare:TYPE?
CALCulate:LIMit:LOWer
CALCulate:LIMit:LOWer?
CALCulate:LIMit:LOWer:STATe
CALCulate:LIMit:LOWer:STATe?
CALCulate:LIMit:UPPer
CALCulate:LIMit:UPPer?

CALCulate:LIMit:UPPer:STATe
CALCulate:LIMit:UPPer:STATe?
CALCulate:SCALe:GAIN
CALCulate:SCALe:GAIN?
CALCulate:SCALe:OFFSet
CALCulate:SCALe:OFFSet?
CALCulate:SCALe:OFFSet:NULL
CALCulate:SCALe:STATe
CALCulate:SCALe:STATe?
CALCulate:SCALe:UNIT
CALCulate:SCALe:UNIT?
CALibration?
CALibration:COUNt?
CALibration:SECure:CODE
CALibration:SECure:STATe
CALibration:SECure:STATe?
CALibration:STRing
CALibration:STRing?
CALibration:VALue
CALibration:VALue?
*CLS

CONFigure?
CONFigure:CURRent:AC
CONFigure:CURRent:DC
CONFigure:DIGital:BYTE
CONFigure:FREQuency
CONFigure:FRESistance
CONFigure:PERiod
CONFigure:RESistance
CONFigure:TEMPerature
CONFigure:TOTalize
CONFigure:VOLTage:AC
CONFigure:VOLTage:DC

D
DATA:LAST?
DATA:POINts?
DATA:POINts:EVENt:THReshold
DATA:POINts:EVENt:THReshold?
DATA:REMove?
DIAGnostic:DMM:CYCLes?
DIAGnostic:DMM:CYCLes:CLEar
DIAGnostic:PEEK:SLOT:DATA?
DIAGnostic:POKE:SLOT:DATA
DIAGnostic:RELay:CYCLes?
DIAGnostic:RELay:CYCLes:CLEar
DISPlay
DISPlay?
DISPlay:TEXT
DISPlay:TEXT?
DISPlay:TEXT:CLEar

E
*ESE
*ESE?
*ESR?

F
FETCh?
FORMat:READing:ALARm
FORMat:READing:ALARm?
FORMat:READing:CHANnel
FORMat:READing:CHANnel?
FORMat:READing:TIME
FORMat:READing:TIME?
FORMat:READing:TIME:TYPE
FORMat:READing:TIME:TYPE?
FORMat:READing:UNIT
FORMat:READing:UNIT?

I
*IDN?
INITiate
INPut:IMPedance:AUTO
INPut:IMPedance:AUTO?
INSTrument:DMM
INSTrument:DMM?
INSTrument:DMM:INSTalled?

L
LXI:IDENtify[:STATe]
LXI:IDENtify[:STATe]?
LXI:RESet
LXI:RESTart

M
MEASure:CURRent:AC?
MEASure:CURRent:DC?
MEASure:DIGital:BYTE?
MEASure:FREQuency?
MEASure:FRESistance?
MEASure:PERiod?
MEASure:RESistance?
MEASure:TEMPerature?
MEASure:TOTalize?
MEASure:VOLTage:AC?
MEASure:VOLTage:DC?
MEMory:NSTates?
MEMory:STATe:DELete
MEMory:STATe:NAME
MEMory:STATe:NAME?
MEMory:STATe:RECall:AUTO
MEMory:STATe:RECall:AUTO?
MEMory:STATe:VALid?
MMEMory:EXPort?
MMEMory:FORMat:READing:CSEParator
MMEMory:FORMat:READing:CSEParator?
MMEMory:FORMat:READing:RLIMit

MMEMory:FORMat:READing:RLIMit?
MMEMory:IMPort:CATalog?
MMEMory:IMPort:CONFig?
MMEMory:LOG[:ENABle]
MMEMory:LOG[:ENABle]?

O
*OPC
*OPC?
OUTPut:ALARm:CLEar:ALL
OUTPut:ALARm:MODE
OUTPut:ALARm:MODE?
OUTPut:ALARm:SLOPe
OUTPut:ALARm:SLOPe?
OUTPut:ALARm{1|2|3|4}:CLEar
OUTPut:ALARm{1|2|3|4}:SOURce
OUTPut:ALARm{1|2|3|4}:SOURce?

P
*PSC
*PSC?

R
R?
*RCL
READ?
ROUTe:CHANnel:ADVance:SOURce
ROUTe:CHANnel:ADVance:SOURce?
ROUTe:CHANnel:DELay
ROUTe:CHANnel:DELay?
ROUTe:CHANnel:DELay:AUTO
ROUTe:CHANnel:DELay:AUTO?
ROUTe:CHANnel:FWIRe
ROUTe:CHANnel:FWIRe?
ROUTe:CLOSe
ROUTe:CLOSe?
ROUTe:CLOSe:EXCLusive
ROUTe:DONE?
ROUTe:MONitor
ROUTe:MONitor?
ROUTe:MONitor:DATA?
ROUTe:MONitor:STATe
ROUTe:MONitor:STATe?
ROUTe:OPEN

ROUTe:OPEN?
ROUTe:SCAN
ROUTe:SCAN?
ROUTe:SCAN:SIZE?
*RST

S
*SAV
[SENSe:]CURRent:AC:BANDwidth
[SENSe:]CURRent:AC:BANDwidth?
[SENSe:]CURRent:AC:RANGe
[SENSe:]CURRent:AC:RANGe?
[SENSe:]CURRent:AC:RANGe:AUTO
[SENSe:]CURRent:AC:RANGe:AUTO?
[SENSe:]CURRent:AC:RESolution
[SENSe:]CURRent:AC:RESolution
[SENSe:]CURRent:DC:APERture
[SENSe:]CURRent:DC:APERture?
[SENSe:]CURRent:DC:NPLC
[SENSe:]CURRent:DC:NPLC?
[SENSe:]CURRent:DC:RANGe
[SENSe:]CURRent:DC:RANGe?
[SENSe:]CURRent:DC:RANGe:AUTO
[SENSe:]CURRent:DC:RANGe:AUTO?
[SENSe:]CURRent:DC:RESolution
[SENSe:]CURRent:DC:RESolution?
[SENSe:]DIGital:DATA:{BYTE|WORD}?
[SENSe:]FREQuency:APERture

[SENSe:]FREQuency:APERture?
[SENSe:]FREQuency:RANGe:LOWer
[SENSe:]FREQuency:RANGe:LOWer?
[SENSe:]FREQuency:VOLTage:RANGe
[SENSe:]FREQuency:VOLTage:RANGe?
[SENSe:]FREQuency:VOLTage:RANGe:AUTO
[SENSe:]FREQuency:VOLTage:RANGe:AUTO?
[SENSe:]FRESistance:APERture
[SENSe:]FRESistance:APERture?
[SENSe:]FRESistance:NPLC
[SENSe:]FRESistance:NPLC?
[SENSe:]FRESistance:OCOMpensated
[SENSe:]FRESistance:OCOMpensated?
[SENSe:]FRESistance:RANGe
[SENSe:]FRESistance:RANGe?
[SENSe:]FRESistance:RANGe:AUTO
[SENSe:]FRESistance:RANGe:AUTO?
[SENSe:]FRESistance:RESolution
[SENSe:]FRESistance:RESolution?
[SENSe:]FUNCtion
[SENSe:]FUNCtion?

[SENSe:]PERiod:APERture
[SENSe:]PERiod:APERture?
[SENSe:]PERiod:VOLTage:RANGe
[SENSe:]PERiod:VOLTage:RANGe?
[SENSe:]PERiod:VOLTage:RANGe:AUTO
[SENSe:]PERiod:VOLTage:RANGe:AUTO?
[SENSe:]RESistance:APERture
[SENSe:]RESistance:APERture?
[SENSe:]RESistance:NPLC
[SENSe:]RESistance:NPLC?
[SENSe:]RESistance:OCOMpensated
[SENSe:]RESistance:OCOMpensated?
[SENSe:]RESistance:RANGe
[SENSe:]RESistance:RANGe?
[SENSe:]RESistance:RANGe:AUTO
[SENSe:]RESistance:RANGe:AUTO?
[SENSe:]RESistance:RESolution
[SENSe:]RESistance:RESolution?
[SENSe:]TEMPerature:APERture
[SENSe:]TEMPerature:APERture?
[SENSe:]TEMPerature:NPLC
[SENSe:]TEMPerature:NPLC?
[SENSe:]TEMPerature:RJUNction?

[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated
[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated?
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]?
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE?
[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated
[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated?
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]?
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE?
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk?
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction?
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE?
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE?
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE?
[SENSe:]TEMPerature:TRANsducer:TYPE
[SENSe:]TEMPerature:TRANsducer:TYPE?

[SENSe:]TOTalize:CLEar:IMMediate
[SENSe:]TOTalize:DATA?
[SENSe:]TOTalize:SLOPe
[SENSe:]TOTalize:SLOPe?
[SENSe:]TOTalize:STARt[:IMMediate]
[SENSe:]TOTalize:STOP[:IMMediate]
[SENSe:]TOTalize:TYPE
[SENSe:]TOTalize:TYPE?
[SENSe:]VOLTage:AC:RANGe
[SENSe:]VOLTage:AC:RANGe?
[SENSe:]VOLTage:AC:RANGe:AUTO
[SENSe:]VOLTage:AC:RANGe:AUTO?
[SENSe:]VOLTage:AC:BANDwidth
[SENSe:]VOLTage:AC:BANDwidth?
[SENSe:]VOLTage:DC:APERture
[SENSe:]VOLTage:DC:APERture?
[SENSe:]VOLTage:DC:NPLC
[SENSe:]VOLTage:DC:NPLC?
[SENSe:]VOLTage:DC:RANGe
[SENSe:]VOLTage:DC:RANGe?
[SENSe:]VOLTage:DC:RANGe:AUTO
[SENSe:]VOLTage:DC:RANGe:AUTO?
[SENSe:]VOLTage:DC:RESolution
[SENSe:]VOLTage:DC:RESolution?

[SENSe:]ZERO:AUTO
[SENSe:]ZERO:AUTO?
SOURce:DIGital:DATA[:{BYTE|WORD}]
SOURce:DIGital:DATA[:{BYTE|WORD}]?
SOURce:DIGital:STATe?
SOURce:VOLTage
SOURce:VOLTage?
*SRE
*SRE?
STATus:ALARm:CONDition?
STATus:ALARm:ENABle
STATus:ALARm:ENABle?
STATus:ALARm[:EVENt]?
STATus:OPERation:CONDition?
STATus:OPERation:ENABle
STATus:OPERation:ENABle?
STATus:OPERation[:EVENt]?
STATus:PRESet
STATus:QUEStionable:CONDition?

STATus:QUEStionable:ENABle
STATus:QUEStionable:ENABle?
STATus:QUEStionable[:EVENt]?
*STB?
SYSTem:ALARm?
SYSTem:COMMunicate:LAN:CONTrol?
SYSTem:COMMunicate:LAN:DHCP
SYSTem:COMMunicate:LAN:DHCP?
SYSTem:COMMunicate:LAN:DNS
SYSTem:COMMunicate:LAN:DNS?
SYSTem:COMMunicate:LAN:DOMain?
SYSTem:COMMunicate:LAN:GATEway
SYSTem:COMMunicate:LAN:GATEway?
SYSTem:COMMunicate:LAN:HOSTname
SYSTem:COMMunicate:LAN:HOSTname?
SYSTem:COMMunicate:LAN:IPADdress
SYSTem:COMMunicate:LAN:IPADdress?
SYSTem:COMMunicate:LAN:MAC?
SYSTem:COMMunicate:LAN:SMASk
SYSTem:COMMunicate:LAN:SMASk?
SYSTem:COMMunicate:LAN:TELNet:PROMpt
SYSTem:COMMunicate:LAN:TELNet:PROMpt?
SYSTem:COMMunicate:LAN:TELNet:WMESsage

SYSTem:COMMunicate:LAN:TELNet:WMESsage?
SYSTem:COMMunicate:LAN:UPDate
SYSTem:CPON
SYSTem:CTYPe?
SYSTem:DATE
SYSTem:DATE?
SYSTem:ERRor?
SYSTem:INTerface
SYSTem:INTerface?
SYSTem:LANGuage
SYSTem:LANGuage?
SYSTem:LFRequency?
SYSTem:LOCal
SYSTem:LOCK:NAME?
SYSTem:LOCK:OWNer?
SYSTem:LOCK:RELease
SYSTem:LOCK:REQuest?
SYSTem:PRESet
SYSTem:REMote
SYSTem:RWLock
SYSTem:SECurity[:IMMediate]
SYSTem:TIME

SYSTem:TIME?
SYSTem:TIME:SCAN?
SYSTem:VERSion?

T
*TRG
TRIGger:COUNt
TRIGger:COUNt?
TRIGger:SOURce
TRIGger:SOURce?
TRIGger:TIMer
TRIGger:TIMer?
*TST?

U
UNIT:TEMPerature
UNIT:TEMPerature?

W
*WAI

Keysight 34970A/34972A Command Quick
Reference
Printable PDF Version
Syntax Conventions
Braces ( { } ) enclose the parameter choices for a given command
string. The braces are not sent with the command string.
A vertical bar ( | ) separates multiple parameter choices for a given
command string. The bar is not sent with the command string.
Angle brackets ( < > ) indicate that you must specify a value for
the enclosed parameter. For example, the above syntax statement
shows the <range> parameter enclosed in triangle brackets. The
brackets are not sent with the command string. You must specify a
value for the parameter (e.g., "VOLT:DC:RANG 10").
Some parameters are enclosed in square brackets ( [ ] ).
The square brackets indicate that the parameter is optional and
can be omitted. The brackets are not sent with the command
string. If you do not specify a value for an optional parameter, the
instrument chooses a default value.
CALCulate Subsystem
CALCulate:AVERage:AVERage? [(@<ch_list>)]
CALCulate:AVERage:CLEar [(@<ch_list>)]
CALCulate:AVERage:COUNt? [(@<ch_list>)]
CALCulate:AVERage:MAXimum? [(@<ch_list>)]
CALCulate:AVERage:MAXimum:TIME? [(@<ch_list>)]

CALCulate:AVERage:MINimum? [(@<ch_list>)]
CALCulate:AVERage:MINimum:TIME? [(@<ch_list>)]
CALCulate:AVERage:PTPeak? [(@<ch_list>)]
CALCulate:COMPare:DATA <data>[,(@<ch_list>)]
CALCulate:COMPare:DATA? [(@<ch_list>)]
CALCulate:COMPare:MASK <mask>[,(@<ch_list>)]
CALCulate:COMPare:MASK? [(@<ch_list>)]
CALCulate:COMPare:STATe <state>[,(@<ch_list>)]
CALCulate:COMPare:STATe? [(@<ch_list>)]
CALCulate:COMPare:TYPE <mode>[,(@<ch_list>)]
CALCulate:COMPare:TYPE? [(@<ch_list>)]

CALCulate:LIMit:LOWer <lo_limit>[,(@<ch_ list>)]
CALCulate:LIMit:LOWer? [(@<ch_list>)]
CALCulate:LIMit:LOWer:STATe <mode>,(@<ch_list>)
CALCulate:LIMit:LOWer:STATe? (@<ch_list>)
CALCulate:LIMit:UPPer <hi_limit>[,(@<ch_ list>)]
CALCulate:LIMit:UPPer? [(@<ch_list>)]
CALCulate:LIMit:UPPer:STATe <mode>,(@<ch_list>)
CALCulate:LIMit:UPPer:STATe? (@<ch_list>)
CALCulate:SCALe:GAIN <gain>[,(@<ch_list>)]
CALCulate:SCALe:GAIN? [(@<ch_list>)]
CALCulate:SCALe:OFFSet <offset>[,(@<ch_list>)]
CALCulate:SCALe:OFFSet? [(@<ch_list>)]
CALCulate:SCALe:OFFSet:NULL [(@<ch_list>)]
CALCulate:SCALe:STATe <state>[,(@<ch_list>)]
CALCulate:SCALe:STATe? [(@<ch_list>)]
CALCulate:SCALe:UNIT <quoted_string>[,(@<ch_list>)]
CALCulate:SCALe:UNIT? [(@<ch_list>)]
CALibration Subsystem
CALibration?
CALibration:COUNt?
CALibration:SECure:CODE <new_code>
CALibration:SECure:STATe <state>,<code>
CALibration:SECure:STATe?
CALibration:STRing <quoted_string>

CALibration:STRing?
CALibration:VALue <value>
CALibration:VALue?

CONFigure Subsystem
CONFigure? [(@<ch_list>)]
CONFigure:CURRent:AC [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:CURRent:DC [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:DIGital:BYTE (@<scan_list>)
CONFigure:FREQuency [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:FRESistance [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:PERiod [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:RESistance [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:TEMPerature {<probe_type>|DEF},{<type>|DEF}[,1[,
{<resolution>|MIN|MAX|DEF}]] ,(@<scan_list>)
CONFigure:TOTalize <mode>,(@<scan_list>)
CONFigure:VOLTage:AC [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
CONFigure:VOLTage:DC [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
DATA Subsystem
DATA:LAST? [<num_rdgs>,](@<channel>)
DATA:POINts?
DATA:POINts:EVENt:THReshold <num_rdgs>
DATA:POINts:EVENt:THReshold?

DATA:REMove? <num_rdgs>

DIAGnostic Subsystem
DIAGnostic:DMM:CYCLes?
DIAGnostic:DMM:CYCLes:CLEar {1|2|3}
DIAGnostic:PEEK:SLOT:DATA? {100|200|300}
DIAGnostic:POKE:SLOT:DATA? {100|200|300}, <quoted_string>
DIAGnostic:RELay:CYCLes? (@<ch_list>)
DIAGnostic:RELay:CYCLes:CLEar (@<ch_list>)
DISPlay Subsystem
DISPlay <state>
DISPlay?
DISPlay:TEXT <quoted_string>
DISPlay:TEXT?
DISPlay:TEXT:CLEar
FORMat Subsystem
FORMat:READing:ALARm <state>
FORMat:READing:ALARm?
FORMat:READing:CHANnel <mode>
FORMat:READing:CHANnel?
FORMat:READing:TIME <mode>
FORMat:READing:TIME?
FORMat:READing:TIME:TYPE <format>
FORMat:READing:TIME:TYPE?
FORMat:READing:UNIT <format>

FORMat:READing:UNIT?

IEEE-488 Subsystem
*CLS
*ESE <enable_val>
*ESE?
*ESR?
*IDN?
*OPC
*OPC?
*PSC <state>
*PSC?
*RCL {0|1|2|3|4|5}
*RST
*SAV {0|1|2|3|4|5}
*SRE <enable_val>
*SRE?
*STB?
*TRG
*TST?
*WAI
INSTrument Subsystem
INSTrument:DMM <state>
INSTrument:DMM?
INSTrument:DMM:INSTalled?

LXI Subsystem
LXI:IDENtify[:STATe] <state>
LXI:IDENtify[:STATe]?
LXI:RESet
LXI:RESTart

MEASure Subsystem
MEASure:CURRent:AC? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:CURRent:DC? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:DIGital:BYTE? (@<scan_list>)
MEASure:FREQuency? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:FRESistance? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:PERiod? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:RESistance? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:TEMPerature? {<probe_type>|DEF},{<type>|DEF}[,1[,
{<resolution>|MIN|MAX|DEF}]] ,(@<scan_list>)
MEASure:TOTalize? <mode>,(@<scan_list>)
MEASure:VOLTage:AC? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEASure:VOLTage:DC? [{<range>|AUTO|MIN|MAX|DEF}[,
{<resolution>|MIN|MAX|DEF}],] (@<scan_list>)
MEMory Subsystem
MEMory:NSTates?
MEMory:STATe:DELete <location>
MEMory:STATe:NAME <location>[,<name>]
MEMory:STATe:NAME? <location>
MEMory:STATe:RECall:AUTO <mode>

MEMory:STATe:RECall:AUTO?
MEMory:STATe:VALid? <location>

MMEMory Subsystem
MMEMory:EXPort?
MMEMory:FORMat:READing:CSEParator <column_separator>
MMEMory:FORMat:READing:CSEParator?
MMEMory:FORMat:READing:RLIMit <row_limit>
MMEMory:FORMat:READing:RLIMit?
MMEMory:IMPort:CATalog?
MMEMory:IMPort:CONFig? "<configuration_file>"
MMEMory:LOG[:ENABle] <state>
MMEMory:LOG[:ENABle]?
Other Commands
ABORt
FETCh?
INITiate
INPut:IMPedance:AUTO <state>[,(@<ch_list>)]
INPut:IMPedance:AUTO? [(@<ch_list>)]
R? [<max_count>
READ? [(@<scan_list>]
UNIT:TEMPerature <units>[,(@<ch_list>) ]
UNIT:TEMPerature? [(@<ch_list>)]
OUTPut Subsystem
OUTPut:ALARm:CLEar:ALL
OUTPut:ALARm:MODE <mode>

OUTPut:ALARm:MODE?
OUTPut:ALARm:SLOPe <edge>
OUTPut:ALARm:SLOPe?
OUTPut:ALARm{1|2|3|4}:CLEar
OUTPut:ALARm{1|2|3|4}:SOURce (@<ch_list>)
OUTPut:ALARm{1|2|3|4}:SOURce?
ROUTe Subsystem
ROUTe:CHANnel:ADVance:SOURce <source>
ROUTe:CHANnel:ADVance:SOURce?
ROUTe:CHANnel:DELay <seconds>,(@<ch_list>)
ROUTe:CHANnel:DELay? (@<ch_list>)
ROUTe:CHANnel:DELay:AUTO <state>[,(@<ch_list>)]
ROUTe:CHANnel:DELay:AUTO? [(@<ch_list>)]
ROUTe:CHANnel:FWIRe <state>[,(@<ch_list>)]
ROUTe:CHANnel:FWIRe? [(@<ch_list>)]
ROUTe:CLOSe (@<ch_list>)
ROUTe:CLOSe? (@<ch_list>)
ROUTe:CLOSe:EXCLusive (@<ch_list>)
ROUTe:DONE?
ROUTe:MONitor (@<channel>)
ROUTe:MONitor?
ROUTe:MONitor:DATA?
ROUTe:MONitor:STATe <mode>
ROUTe:MONitor:STATe?
ROUTe:OPEN (@<ch_list>)

ROUTe:OPEN? (@<ch_list>)
ROUTe:SCAN (@<scan_list>)
ROUTe:SCAN?
ROUTe:SCAN:SIZE?

SENSe Subsystem
[SENSe:]CURRent:AC:BANDwidth {<filter>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:AC:BANDwidth? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]CURRent:AC:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:AC:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]CURRent:AC:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]CURRent:AC:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]CURRent:AC:RESolution {<resolution>|MIN|MAX|DEF}[,
(@<ch_list>)]
[SENSe:]CURRent:AC:RESolution? {<ch_list>|MIN|MAX}
[SENSe:]CURRent:DC:APERture {<time>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:DC:APERture? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]CURRent:DC:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:DC:NPLC? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]CURRent:DC:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]CURRent:DC:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]CURRent:DC:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]CURRent:DC:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]CURRent:DC:RESolution{<resolution>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]CURRent:DC:RESolution? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]DIGital:DATA:{BYTE|WORD}? [(@<ch_list>)]
[SENSe:]FREQuency:APERture {<seconds>|MIN|MAX}[,(@<ch_list>)]

[SENSe:]FREQuency:APERture? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FREQuency:RANGe:LOWer {<filter>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]FREQuency:RANGe:LOWer? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FREQuency:VOLTage:RANGe {<range>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]FREQuency:VOLTage:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FREQuency:VOLTage:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]FREQuency:VOLTage:RANGe:AUTO? [(@<ch_list>)]

[SENSe:]FRESistance:APERture {<time>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]FRESistance:APERture? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FRESistance:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]FRESistance:NPLC? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FRESistance:OCOMpensated <state>[,(@<ch_list>)]
[SENSe:]FRESistance:OCOMpensated? [(@<ch_list>)]
[SENSe:]FRESistance:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]FRESistance:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FRESistance:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]FRESistance:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]FRESistance:RESolution {<resolution>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]FRESistance:RESolution? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]FUNCtion "<function>"[,(@<ch_list>)]
[SENSe:]FUNCtion? [(@<ch_list>)]
[SENSe:]PERiod:APERture {<seconds>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]PERiod:APERture? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]PERiod:VOLTage:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]PERiod:VOLTage:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]PERiod:VOLTage:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]PERiod:VOLTage:RANGe:AUTO? [(@<ch_list>)]

[SENSe:]RESistance:APERture {<time>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]RESistance:APERture? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]RESistance:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]RESistance:NPLC? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]RESistance:OCOMpensated <state>[,(@<ch_list>)]
[SENSe:]RESistance:OCOMpensated? [(@<ch_list>)]
[SENSe:]RESistance:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]RESistance:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]RESistance:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]RESistance:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]RESistance:RESolution {<resolution>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]RESistance:RESolution? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]TEMPerature:APERture {<time>|MIN|MAX|DEF}[,
(@<ch_list>)]
[SENSe:]TEMPerature:APERture? {(@<ch_list>)|MIN|MAX}
[SENSe:]TEMPerature:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]TEMPerature:NPLC? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]TEMPerature:RJUNction? [(@<ch_list>)]

[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated <state>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:OCOMpensated?
[(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]?
[(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE <type>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE? [(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated <state>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:RTD:OCOMpensated?
[(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]?
[(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE <type>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE? [(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk <state>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk? [(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction
{<temperature>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction?
[(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE
<type>[,(@<ch_list>)]

[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE?
[(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE <type>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE? [(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE <type>[,
(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE?
[(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TYPE
{TCouple|RTD|FRTD|THERmistor|DEF}[,(@<ch_list>)]
[SENSe:]TEMPerature:TRANsducer:TYPE? [(@<ch_list>)]
[SENSe:]TOTalize:CLEar:IMMediate [(@<ch_list>)]
[SENSe:]TOTalize:DATA? [(@<ch_list>)]
[SENSe:]TOTalize:SLOPe <edge>[,(@<ch_list>)]
[SENSe:]TOTalize:SLOPe? [(@<ch_list>)]
[SENSe:]TOTalize:STARt[:IMMediate] [(@<ch_list>)]
[SENSe:]TOTalize:STOP[:IMMediate] [(@<ch_list>)]
[SENSe:]TOTalize:TYPE <mode>[,(@<ch_list>)]
[SENSe:]TOTalize:TYPE? [(@<ch_list>)]
[SENSe:]VOLTage:AC:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]VOLTage:AC:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]VOLTage:AC:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]VOLTage:AC:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]VOLTage:AC:BANDwidth {<filter>|MIN|MAX}[,(@<ch_list>)]

[SENSe:]VOLTage:AC:BANDwidth? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]VOLTage:DC:APERture {<time>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]VOLTage:DC:APERture? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]VOLTage:DC:NPLC {<PLCs>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]VOLTage:DC:NPLC? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]VOLTage:DC:RANGe {<range>|MIN|MAX}[,(@<ch_list>)]
[SENSe:]VOLTage:DC:RANGe? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]VOLTage:DC:RANGe:AUTO <state>[,(@<ch_list>)]
[SENSe:]VOLTage:DC:RANGe:AUTO? [(@<ch_list>)]
[SENSe:]VOLTage:DC:RESolution {<resolution>|MIN|MAX}[,
(@<ch_list>)]
[SENSe:]VOLTage:DC:RESolution? [{(@<ch_list>)|MIN|MAX}]
[SENSe:]ZERO:AUTO {OFF|ONCE|ON}[,(@<ch_list>)]
[SENSe:]ZERO:AUTO? [(@<ch_list>)]
SOURce Subsystem
SOURce:DIGital:DATA[:{BYTE|WORD}] <data>,(@<ch_list>)
SOURce:DIGital:DATA[:{BYTE|WORD}]? (@<ch_list>)
SOURce:DIGital:STATe? (@<ch_list>)
SOURce:VOLTage <voltage>,(@<ch_list>)
SOURce:VOLTage? (@<ch_list>)

STATus Subsystem
STATus:ALARm:CONDition?
STATus:ALARm:ENABle <enable_val>
STATus:ALARm:ENABle?
STATus:ALARm[:EVENt]?
STATus:OPERation:CONDition?
STATus:OPERation:ENABle <enable_val>
STATus:OPERation:ENABle?
STATus:OPERation[:EVENt]?
STATus:PRESet
STATus:QUEStionable:CONDition?
STATus:QUEStionable:ENABle <enable_val>
STATus:QUEStionable:ENABle?
STATus:QUEStionable[:EVENt]?

SYSTEM Subsystem - LAN Configuration
SYSTem:COMMunicate:LAN:CONTrol?
SYSTem:COMMunicate:LAN:DHCP <mode>
SYSTem:COMMunicate:LAN:DHCP?
SYSTem:COMMunicate:LAN:DNS "<address>"
SYSTem:COMMunicate:LAN:DNS? [{CURRent|STATic}]
SYSTem:COMMunicate:LAN:DOMain? [{CURRent|STATic}]
SYSTem:COMMunicate:LAN:GATEway "<address>"
SYSTem:COMMunicate:LAN:GATEway? [{CURRent|STATic}]
SYSTem:COMMunicate:LAN:HOSTname "<name>"
SYSTem:COMMunicate:LAN:HOSTname? [{CURRent|STATic}]
SYSTem:COMMunicate:LAN:IPADdress "<address>"
SYSTem:COMMunicate:LAN:IPADdress? [{CURRent|STATic}]
SYSTem:COMMunicate:LAN:MAC?
SYSTem:COMMunicate:LAN:SMASk "<mask>"
SYSTem:COMMunicate:LAN:SMASk? [{CURRent|STATic}]
SYSTem:COMMunicate:LAN:TELNet:PROMpt "<string>"
SYSTem:COMMunicate:LAN:TELNet:PROMpt?
SYSTem:COMMunicate:LAN:TELNet:WMESsage "<string>"
SYSTem:COMMunicate:LAN:TELNet:WMESsage?
SYSTem:COMMunicate:LAN:UPDate

SYSTem Subsystem - Other Commands
SYSTem:ALARm?
SYSTem:CPON <slot>
SYSTem:CTYPe? <slot>
SYSTem:DATE <yyyy>,<mm>,<dd>
SYSTem:DATE?
SYSTem:ERRor?
SYSTem:INTerface {GPIB|RS232}
SYSTem:INTerface?
SYSTem:LANGuage <language>
SYSTem:LANGuage?
SYST:LFRequency?
SYSTem:LOCal
SYSTem:LOCK:NAME?
SYSTem:LOCK:OWNer?
SYSTem:LOCK:RELease
SYSTem:LOCK:REQuest?
SYSTem:PRESet
SYSTem:REMote
SYSTem:RWLock
SYSTem:SECurity[:IMMediate]
SYSTem:TIME <hh>,<mm>,<ss.sss>
SYSTem:TIME?
SYSTem:TIME:SCAN?
SYSTem:VERSion?

TRIGger Subsystem
TRIGger:COUNt {<count>|MIN|MAX|INFinity}
TRIGger:COUNt?
TRIGger:SOURce <source>
TRIGger:SOURce?
TRIGger:TIMer {<seconds>|MIN|MAX}
TRIGger:TIMer? [{MIN|MAX}]
© Keysight Technologies, Inc. 2009-2013

Error Messages
-350-99 IEEE and Parser Errors | 100-299 General Errors | 300-399
Module and Channel Errors | 400-449 Mass Storage Errors | 450-499
USB Logging Errors | 500-599 Serious Instrument Errors | 600-649 Self-
test Errors | 700-799 Calibration Errors | 811 Operation Not Implemented
| 900-999 Module Errors
The instrument beeps once each time a command syntax or
hardware error is generated. The front-panel ERROR annunciator
turns on when one or more errors are currently stored in the error
queue.
Errors are retrieved in first-in-first-out (FIFO) order. The first error
returned is the first error that was stored. Once you have read all
of the interface-specific errors, the errors in the global error queue
are retrieved.
Errors are cleared as you read them. When you have read all
errors from the interface-specific and global error queues, the
ERROR annunciator turns off and the errors are cleared.
If more than 20 errors have occurred, the last error stored in the
queue (the most recent error) is replaced with -350,"Error queue
overflow". No additional errors are stored until you remove errors
from the queue. If no errors have occurred when you read the
error queue, the instrument responds with +0,"No error".
The front panel reports errors from all I/O sessions as well as the
global error queue. To read the error queue from the front panel,
use the View key.
Error conditions are also summarized in the Status Byte Register.
For more information on the Status System for the instrument, see
Status System Introduction.
The interface-specific and global error queues are cleared by the

*CLS (Clear Status) command and when power is cycled. The
errors are also cleared when you read the error queue. The error
queue is not cleared by a Factory Reset (*RST command) or an
Instrument Preset (SYSTem:PRESet command).
The query reads and clears one error string from the error queue.
The error string may contain up to 160 characters and consists of
an error number and an error string enclosed in double quotes.
For example:
-113,"Undefined header"

-350-99 IEEE and Parser Errors
-350 "Error queue overflow"
-330 "Self test failed"
-256 "File or folder name not found"
-231 "Internal software error"
-230 "Data stale"
-224 "Data questionable"
-224 "Illegal parameter value ranges must be positive"
-222 "Data out of range"
-221 "Settings conflict"
-214 "Trigger deadlock"
-213 "INIT ignored"
-211 "Trigger ignored"
-123 "Numeric overflow"
-114 "Subopcode out of range"
-110 "Internal communications timeout"
-56 "System error"

100-299 General Errors
100 "Network Error"
111 "Channel list: slot number out of range"
112 "Channel list: channel number out of range"
113 "Channel list: empty scan list"
201 "Memory lost: stored state"
202 "Memory lost: power-on state"
203 "Memory lost: stored readings"
204 "Memory lost: time and date"
221 "Settings conflict: calculate limit state forced off"
222 "Settings conflict: module type does not match state"
223 "Settings conflict: trig source changed to IMM"
224 "Settings conflict: chan adv source changed to IMM"
225 "Settings conflict: DMM disabled or missing"
226 "Settings conflict: DMM enabled"
251 "Unsupported temperature transducer type"
261 "Not able to execute while scan initiated"
262 "Not able to abort scan"
271 "Not able to accept unit names longer than 3 characters"
272 "Not able to accept character in unit name"
281 "Not able to perform on more than one channel"
291 "Not able to recall state: it is empty"
292 "Not able to recall state: DMM enable changed"

300-399 Module and Channel Errors
301 "Module currently committed to scan"
302 "No module was detected in this slot"
303 "Module is not able to perform requested operation"
304 "Does not exist"
305 "Not able to perform requested operation"
306 "Part of a 4-wire pair"
307 "Incorrectly configured ref channel"
308 "Channel not able to perform requested operation"
309 "Incorrectly formatted channel list"

400-449 Mass Storage Errors
401 "Mass storage error: failed to create file"
402 "Mass storage error: failed to open file"
403 "Mass storage error: failed to close file"
404 "Mass storage error: file write error"
405 "Mass storage error: file read error"
406 "Mass storage error: file write error"
407 "Mass storage error: failed to remove file"
408 "Mass storage error: failed to create directory"
409 "Mass storage error: failed to remove directory"
410 "Not enough disk space"
411 "No external disk detected"
412 "External disk has been detached"
413 "File already exists"
414 "Directory already exists"
415 "File not found"
416 "Path not found"
417 "File not opened for writing"
418 "File not opened for reading"

450-499 USB Logging Errors
450 "Overrun during data collection: readings lost in USB transfer"
451 "Overrun during USB output: readings lost in USB transfer"
452 "Reading memory export aborted due to measurement reconfig"
453 "Not able to execute while logging data to USB"
454 "Not able to execute while copying data to USB"
455 "Not able to execute while importing a configuration from USB"
456 (none)
457 "Logging request ignored: USB device is busy"
458 "External USB drive is inaccessible"
459 "Logging to USB was stopped"
460 "Logging to USB was stopped after 2^32 sweeps of data"
461 "Memory lost: non-volatile settings; USB drive"
462 "Configuration import aborted"
463 "Configuration import failed"
464 "Invalid import file"
465 "Import file cardset does not match instrument"
466 "Operation not allowed in a configuration import file"
467 "No readings to export"
468 "Unable to fetch measurement config from internal processor"
469 "Internal processor returned an invalid measurement config"
470 "Measurement was reconfigured; Cannot save configuration data"
471 "USB operation aborted; Cannot save configuration data"
472 "One or more blcfg file names invalid; files inaccessible"
473 "Disk contains too many blcfg files; oldest files inaccessible"

500-599 Serious Instrument Errors
514 "RS-232 only: unable to execute using HP-IB" (34970A
only)
514 "Not allowed; Instrument locked by another I/O
session" (34972A only)
521 "Communications: input buffer overflow"
522 "Communications: output buffer overflow"
532 "Not able to achieve requested resolution"
540 "Not able to null channel in overload"
550 "Not able to execute command in local mode"

600-649 Self-test Errors
601 "Self-test: front panel not responding"
602 "Self-test: RAM read/write"
603 "Self-test: A/D sync stuck"
604 "Self-test: A/D slope convergence"
605 "Self-test/Cal: not able to calibrate rundown gain"
606 "Self-test/Cal: rundown gain out of range"
607 "Self-test: rundown too noisy"
608 "Self-test: serial configuration readback failed"
609 "Self-test: DC gain x1 failed"
610 "Self-test: DC gain x10 failed"
611 "Self-test: DC gain x100 failed"
612 "Self-test: Ohms 500 nA source failed"
613 "Self-test: Ohms 5 uA source failed"
614 "Self-test: DC 300V zero failed"
615 "Self-test: Ohms 10 uA source failed"
616 "Self-test: DC current sense failed"
617 "Self-test: Ohms 100 uA source failed"
618 "Self-test: DC high voltage attenuator failed"
619 "Self-test: Ohms 1 mA source failed"
620 "Self-test: AC rms zero failed"
621 "Self-test: AC rms full scale failed"
622 "Self-test: frequency counter failed"
623 "Self-test: cannot calibrate precharge"
624 "Self-test: unable to sense line frequency"
625 "Self-test: I/O processor does not respond"
626 "Self-test: I/O processor failed self-test"

700-799 Calibration Errors
701 "Cal security disabled by jumper"
702 "Cal: secured"
703 "Cal: invalid secure code"
704 "Cal: secure code too long"
705 "Cal: aborted"
706 "Cal: value out of range"
707 "Cal: signal measurement out of range"
708 "Cal: signal frequency out of range"
709 "Cal: no cal for this function or range"
710 "Cal: full scale correction out of range"
720 "Cal: DCV offset out of range"
721 "Cal: DCI offset out of range"
722 "Cal: RES offset out of range"
723 "Cal: FRES offset out of range"
724 "Cal: extended resistance self cal failed"
725 "Cal: 300V DC correction out of range"
730 "Cal: precharge DAC convergence failed"
731 "Cal: A/D turnover correction out of range"
732 "Cal: AC flatness DAC convergence failed"
733 "Cal: AC low frequency convergence failed"
734 "Cal: AC low frequency correction out of range"
735 "Cal: AC rms converter noise correction out of range"
736 "Cal: AC rms 100th scale correction out of range"
740 "Cal data lost: secure state"
741 "Cal data lost: string data"
742 "Cal data lost: DCV corrections"
743 "Cal data lost: DCI corrections"
744 "Cal data lost: RES corrections"
745 "Cal data lost: FRES corrections"
746 "Cal data lost: AC corrections"
747 "Config data lost: HP-IB address" (34970A only)
747 "Calibration failed" (34972A only)
748 "Config data lost: RS-232" (34970A only)
748 "Cal checksum failed internal data" (34972A only)
749 "DMM relay count data lost"

811 Operation Not Implemented
811 "Operation not implemented"

900-999 Module Errors
901 "Module hardware: unexpected data received"
902 "Module hardware: missing stop bit"
903 "Module hardware: data overrun"
904 "Module hardware: protocol violation"
905 "Module hardware: early end of data"
906 "Module hardware: missing end of data"
907 "Module hardware: module SRQ signal stuck low"
908 "Module hardware: not responding"
910 "Module reported an unknown module type"
911 "Module reported command buffer overflow"
912 "Module reported command syntax error"
913 "Module reported nonvolatile memory fault"
914 "Module reported temperature sensor fault"
915 "Module reported firmware defect"
916 "Module reported incorrect firmware installed"

Factory Reset State
The following tables show the state of the instrument after a
FACTORY RESET from the Sto/Rcl menu, or *RST from the remote
interface.
Measurement Factory Reset State
Configuration
Function DC Volts
Range Autorange
Resolution 5½ Digits
Integration Time 1 PLC
Input Resistance 10 MΩ (fixed for all
DCV ranges)
Channel Delay Automatic Delay
Totalizer Reset Count Not Reset
Mode When Read

Totalizer Edge Rising Edge
Detect
Scanning Factory Reset
Operations State
Scan List Empty
Reading Memory All Readings are
Cleared
Min, Max, and Not Changed
Average
Scan Trigger Source Immediate
Scan Interval (used 10 Seconds
with
TRIGger:SOURce
TIMer)
Scan Count 1
Scan Reading Reading Only (No
Format Units, Channel,
Time)

Monitor in Progress Stopped
Mx+B Scaling Factory Reset State
Gain Factor 1
("M")
Offset Factor 0
("B")
Scale Label VDC
Alarm Limits Factory Reset State
Alarm Queue Not Cleared
Alarm State Off
HI and LO Alarm 0
Limits

Alarm Output Alarm 1
Alarm Output Latched Mode
Configuration
Alarm Output State Output Lines are
Cleared
Alarm Output Slope Fail = Low
Module Factory Reset State
Hardware
34901A, 34902A, All Channels Open
34908A
34903A, 34904A All Channels Open
34905A, 34906A Channels s11 and s21
Selected
34907A Both DIO Ports = Input,
Totalizer Count =
0, Both DACs = 0 VDC

System-Related Factory Reset State
Operations
Display State On
Error Queue Errors Not Cleared
Stored States No Change

Instrument Preset State
The following tables show the state of the instrument after a PRESET
from the Sto/Rcl menu or a SYSTem:PRESet command from the remote
interface.
Measurement Instrument Preset State
Configuration
Function No Change
Range No Change
Resolution No Change
Advanced Settings No Change
Totalizer Reset Count Not Reset When
Mode Read
Totalizer Edge Rising Edge
Detect
Scanning Instrument Preset State
Operations

Scan List No Change
Reading Memory All Readings are Cleared
Min, Max, and No Change
Average
Scan Interval No Change
Source
Scan Interval No Change
Scan Count No Change
Scan Reading No Change
Format
Monitor in Stopped
Progress
Mx+B Scaling Instrument Preset State
Gain Factor No Change

("M")
Offset Factor No Change
("B")
Scale Label No Change
Alarm Limits Instrument Preset State
Alarm Queue No Change
Alarm State No Change
HI and LO Alarm No Change
Limits
Alarm Output No Change
Configuration
Alarm Output State Output Lines are Cleared
Alarm Output No Change
Slope

Module Instrument Preset State
Hardware
34901A, 34902A, All Channels Open
34908A
34903A, 34904A All Channels Open
34905A, 34906A Channels s11 and s21
Selected
34907A Both DIO Ports = Input,
Totalizer Count = 0, Both
DACs = 0 VDC
System-Related Instrument Preset State
Operations
Display State No Change
Error Queue Errors Not Cleared
Stored States No Change

34970A/34972A Module Details
The links below take you to summary information for the
Keysight 34970A/34972A plug-in modules.
34901A 20-Channel Armature Multiplexer
34902A 16-Channel Reed Multiplexer
34903A 20-Channel Actuator/General-Purpose Switch
34904A 4x8 Two-Wire Matrix Switch
34905A/34906A Dual 4-Channel RF Multiplexers
34907A Multifunction Module
34908A 40-Channel Single-Ended Multiplexer

Keysight 34901A Module Summary
20-Channel Armature Multiplexer (2/4-wire)
Module
Simplified Schematic
SCPI Commands Used

CALCulate:AVERage:AVERage?
CALCulate:AVERage:CLEar
CALCulate:AVERage:COUNt?
CALCulate:AVERage:MAXimum?
CALCulate:AVERage:MAXimum:TIME?
CALCulate:AVERage:MINimum?
CALCulate:AVERage:MINimum:TIME?
CALCulate:AVERage:PTPeak?
CALCulate:LIMit:LOWer
CALCulate:LIMit:LOWer:STATe
CALCulate:LIMit:UPPer
CALCulate:LIMit:UPPer:STATe
CALCulate:SCALe:GAIN
CALCulate:SCALe:OFFSet
CALCulate:SCALe:OFFSet:NULL
CALCulate:SCALe:STATe
CALCulate:SCALe:UNIT
CONFigure?
CONFigure:CURRent:AC
CONFigure:CURRent:DC
CONFigure:FREQuency
CONFigure:FRESistance
CONFigure:PERiod
CONFigure:RESistance
CONFigure:TEMPerature
CONFigure:VOLTage:AC

CONFigure:VOLTage:DC
DIAGnostic:RELay:CYCLes?
DIAGnostic:RELay:CYCLes:CLEar
MEASure:CURRent:AC?
MEASure:CURRent:DC?
MEASure:FREQuency?
MEASure:FRESistance?
MEASure:PERiod?
MEASure:RESistance?
MEASure:TEMPerature?
MEASure:VOLTage:AC?
MEASure:VOLTage:DC?
ROUTe:CHANnel:DELay
ROUTe:CHANnel:DELay:AUTO
ROUTe:CHANnel:FWIRe
ROUTe:CLOSe
ROUTe:CLOSe:EXCLusive
ROUTe:MONitor
ROUTe:MONitor:DATA?
ROUTe:OPEN
ROUTe:SCAN
[SENSe:]CURRent:AC:BANDwidth
[SENSe:]CURRent:AC:RANGe
[SENSe:]CURRent:AC:RANGe:AUTO
[SENSe:]CURRent:DC:APERture
[SENSe:]CURRent:DC:NPLC

[SENSe:]CURRent:DC:RANGe
[SENSe:]CURRent:DC:RANGe:AUTO
[SENSe:]CURRent:DC:RESolution
[SENSe:]FREQuency:APERture
[SENSe:]FREQuency:RANGe:LOWer
[SENSe:]FREQuency:VOLTage:RANGe
[SENSe:]FREQuency:VOLTage:RANGe:AUTO
[SENSe:]FRESistance:APERture
[SENSe:]FRESistance:NPLC
[SENSe:]FRESistance:OCOMpensated
[SENSe:]FRESistance:RANGe
[SENSe:]FRESistance:RANGe:AUTO
[SENSe:]FRESistance:RESolution
[SENSe:]PERiod:APERture
[SENSe:]PERiod:VOLTage:RANGe
[SENSe:]PERiod:VOLTage:RANGe:AUTO
[SENSe:]RESistance:APERture
[SENSe:]RESistance:NPLC
[SENSe:]RESistance:OCOMpensated
[SENSe:]RESistance:RANGe
[SENSe:]RESistance:RANGe:AUTO
[SENSe:]RESistance:RESolution
[SENSe:]TEMPerature:NPLC
[SENSe:]TEMPerature:RJUNction?
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE

[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE
[SENSe:]TEMPerature:TRANsducer:TYPE
[SENSe:]VOLTage:AC:BANDwidth
[SENSe:]VOLTage:AC:RANGe
[SENSe:]VOLTage:AC:RANGe:AUTO
[SENSe:]VOLTage:DC:APERture
[SENSe:]VOLTage:DC:NPLC
[SENSe:]VOLTage:DC:RANGe
[SENSe:]VOLTage:DC:RANGe:AUTO
[SENSe:]VOLTage:DC:RESolution
[SENSe:]ZERO:AUTO
SYSTem:CPON
SYSTem:CTYPe?
UNIT:TEMPerature

Keysight 34902A Module Summary
16-Channel Reed Multiplexer (2/4-wire) Module
Simplified Schematic
SCPI Commands Used
CALCulate:AVERage:AVERage?
CALCulate:AVERage:CLEar
CALCulate:AVERage:COUNt?
CALCulate:AVERage:MAXimum?
CALCulate:AVERage:MAXimum:TIME?
CALCulate:AVERage:MINimum?

CALCulate:AVERage:MINimum:TIME?
CALCulate:AVERage:PTPeak?
CALCulate:LIMit:LOWer
CALCulate:LIMit:LOWer:STATe
CALCulate:LIMit:UPPer
CALCulate:LIMit:UPPer:STATe
CALCulate:SCALe:GAIN
CALCulate:SCALe:OFFSet
CALCulate:SCALe:OFFSet:NULL
CALCulate:SCALe:STATe
CALCulate:SCALe:UNIT
CONFigure?
CONFigure:FREQuency
CONFigure:FRESistance
CONFigure:PERiod
CONFigure:RESistance
CONFigure:TEMPerature
CONFigure:VOLTage:AC
CONFigure:VOLTage:DC
DIAGnostic:RELay:CYCLes?
DIAGnostic:RELay:CYCLes:CLEar
MEASure:FREQuency?
MEASure:FRESistance?
MEASure:PERiod?
MEASure:RESistance?
MEASure:TEMPerature?

MEASure:VOLTage:AC?
MEASure:VOLTage:DC?
ROUTe:CHANnel:DELay
ROUTe:CHANnel:DELay:AUTO
ROUTe:CHANnel:FWIRe
ROUTe:CLOSe
ROUTe:CLOSe:EXCLusive
ROUTe:MONitor
ROUTe:MONitor:DATA?
ROUTe:OPEN
ROUTe:SCAN
[SENSe:]FREQuency:APERture
[SENSe:]FREQuency:RANGe:LOWer
[SENSe:]FREQuency:VOLTage:RANGe
[SENSe:]FREQuency:VOLTage:RANGe:AUTO
[SENSe:]FRESistance:APERture
[SENSe:]FRESistance:NPLC
[SENSe:]FRESistance:OCOMpensated
[SENSe:]FRESistance:RANGe
[SENSe:]FRESistance:RANGe:AUTO
[SENSe:]FRESistance:RESolution
[SENSe:]PERiod:APERture
[SENSe:]PERiod:VOLTage:RANGe
[SENSe:]PERiod:VOLTage:RANGe:AUTO
[SENSe:]RESistance:APERture
[SENSe:]RESistance:NPLC

[SENSe:]RESistance:OCOMpensated
[SENSe:]RESistance:RANGe
[SENSe:]RESistance:RANGe:AUTO
[SENSe:]RESistance:RESolution
[SENSe:]TEMPerature:NPLC
[SENSe:]TEMPerature:RJUNction?
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE
[SENSe:]TEMPerature:TRANsducer:TYPE
[SENSe:]VOLTage:AC:BANDwidth
[SENSe:]VOLTage:AC:RANGe
[SENSe:]VOLTage:AC:RANGe:AUTO
[SENSe:]VOLTage:DC:APERture
[SENSe:]VOLTage:DC:NPLC
[SENSe:]VOLTage:DC:RANGe
[SENSe:]VOLTage:DC:RANGe:AUTO
[SENSe:]VOLTage:DC:RESolution
[SENSe:]ZERO:AUTO
SYSTem:CPON

SYSTem:CTYPe?
UNIT:TEMPerature

Keysight 34903A Module Summary
20-Channel Actuator/GP Switch Module
Simplified Schematic
SCPI Commands Used
DIAGnostic:RELay:CYCLes?
DIAGnostic:RELay:CYCLes:CLEar
ROUTe:CLOSe
ROUTe:CLOSe:EXCLusive
ROUTe:OPEN
SYSTem:CPON
SYSTem:CTYPe?

Keysight 34904A Module Summary
4x8 Two-Wire Matrix Module
Simplified Schematic

SCPI Commands Used
DIAGnostic:RELay:CYCLes?
DIAGnostic:RELay:CYCLes:CLEar
ROUTe:CLOSe

ROUTe:CLOSe:EXCLusive
ROUTe:OPEN
SYSTem:CPON
SYSTem:CTYPe?

Keysight 34905A/34906A Module Summary
2 GHz Dual 1:4 RF Mux, 50 Ohm Module
(34905A)
2 GHz Dual 1:4 RF Mux, 75 Ohm Module
(34906A)
Simplified Schematic

SCPI Commands Used
DIAGnostic:RELay:CYCLes?
DIAGnostic:RELay:CYCLes:CLEar
ROUTe:CLOSe
ROUTe:CLOSe:EXCLusive
SYSTem:CPON

SYSTem:CTYPe?

Keysight 34907A Module Summary
Multifunction Module
Simplified Schematic - Digital Input/Output
Simplified Schematic - Totalize Input
Simplified Schematic - Analog Output (DAC)

SCPI Commands Used
CALCulate:AVERage:AVERage?
CALCulate:AVERage:CLEar
CALCulate:AVERage:COUNt?
CALCulate:AVERage:MAXimum?
CALCulate:AVERage:MAXimum:TIME?
CALCulate:AVERage:MINimum?
CALCulate:AVERage:MINimum:TIME?
CALCulate:AVERage:PTPeak?
CALCulate:COMPare:DATA
CALCulate:COMPare:MASK
CALCulate:COMPare:STATe
CALCulate:COMPare:TYPE
CALCulate:LIMit:LOWer
CALCulate:LIMit:UPPer
CALibration?
CALibration:VALue

CONFigure?
CONFigure:DIGital:BYTE
CONFigure:TOTalize
MEASure:DIGital:BYTE?
MEASure:TOTalize?
ROUTe:CHANnel:DELay
ROUTe:CHANnel:DELay:AUTO
ROUTe:MONitor
ROUTe:MONitor:DATA?
ROUTe:SCAN
[SENSe:]DIGital:DATA:{BYTE|WORD}?
[SENSe:]TOTalize:CLEar:IMMediate
[SENSe:]TOTalize:DATA?
[SENSe:]TOTalize:SLOPe
[SENSe:]TOTalize:TYPE
SOURce:DIGital:DATA[:{BYTE|WORD}]
SOURce:DIGital:STATe?
SOURce:VOLTage
SYSTem:CPON
SYSTem:CTYPe?

Keysight 34908A Module Summary
40 Channel Single-Ended Multiplexer Module
Simplified Schematic
SCPI Commands Used

CALCulate:AVERage:AVERage?
CALCulate:AVERage:CLEar
CALCulate:AVERage:COUNt?
CALCulate:AVERage:MAXimum?
CALCulate:AVERage:MAXimum:TIME?
CALCulate:AVERage:MINimum?
CALCulate:AVERage:MINimum:TIME?
CALCulate:AVERage:PTPeak?
CALCulate:LIMit:LOWer
CALCulate:LIMit:LOWer:STATe
CALCulate:LIMit:UPPer
CALCulate:LIMit:UPPer:STATe
CALCulate:SCALe:GAIN
CALCulate:SCALe:OFFSet
CALCulate:SCALe:OFFSet:NULL
CALCulate:SCALe:STATe
CALCulate:SCALe:UNIT
CALibration?
CONFigure?
CONFigure:FREQuency
CONFigure:PERiod
CONFigure:RESistance
CONFigure:TEMPerature
CONFigure:VOLTage:AC
CONFigure:VOLTage:DC
DIAGnostic:RELay:CYCLes?

DIAGnostic:RELay:CYCLes:CLEar
MEASure:FREQuency?
MEASure:PERiod?
MEASure:RESistance?
MEASure:TEMPerature?
MEASure:VOLTage:AC?
MEASure:VOLTage:DC?
ROUTe:CHANnel:DELay
ROUTe:CHANnel:DELay:AUTO
ROUTe:CHANnel:FWIRe
ROUTe:CLOSe
ROUTe:CLOSe:EXCLusive
ROUTe:MONitor
ROUTe:MONitor:DATA?
ROUTe:OPEN
ROUTe:SCAN
[SENSe:]FREQuency:APERture
[SENSe:]FREQuency:RANGe:LOWer
[SENSe:]FREQuency:VOLTage:RANGe
[SENSe:]FREQuency:VOLTage:RANGe:AUTO
[SENSe:]FRESistance:APERture
[SENSe:]PERiod:APERture
[SENSe:]PERiod:VOLTage:RANGe
[SENSe:]PERiod:VOLTage:RANGe:AUTO
[SENSe:]RESistance:APERture
[SENSe:]RESistance:NPLC

[SENSe:]RESistance:OCOMpensated
[SENSe:]RESistance:RANGe
[SENSe:]RESistance:RANGe:AUTO
[SENSe:]RESistance:RESolution
[SENSe:]TEMPerature:NPLC
[SENSe:]TEMPerature:RJUNction?
[SENSe:]TEMPerature:TRANsducer:FRTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:FRTD:TYPE
[SENSe:]TEMPerature:TRANsducer:RTD:RESistance[:REFerence]
[SENSe:]TEMPerature:TRANsducer:RTD:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE
[SENSe:]TEMPerature:TRANsducer:THERmistor:TYPE
[SENSe:]TEMPerature:TRANsducer:TYPE
[SENSe:]VOLTage:AC:BANDwidth
[SENSe:]VOLTage:AC:RANGe
[SENSe:]VOLTage:AC:RANGe:AUTO
[SENSe:]VOLTage:DC:APERture
[SENSe:]VOLTage:DC:NPLC
[SENSe:]VOLTage:DC:RANGe
[SENSe:]VOLTage:DC:RANGe:AUTO
[SENSe:]VOLTage:DC:RESolution
[SENSe:]ZERO:AUTO
SYSTem:CPON

SYSTem:CTYPe?
UNIT:TEMPerature

Introduction to the Command Language
This document describes the SCPI command language for the Keysight
34970A/34972A multifunction switch/measure unit. These commands
are based on a hierarchical tree system in which associated commands
are grouped together under a common node or root to form subsystems.
A portion of the INPut subsystem is shown below to illustrate the tree
system.
INPut:
COUPling:
IMPedance:
INPut is the root keyword of the command, and COUPling and
IMPedance are second-level keywords. A colon ( : ) separates a
command keyword from a lower-level keyword.

Syntax Conventions
The format used to show commands is illustrated below:
MEASure:INSTall:DELete {<label>|ALL}
The command syntax shows most commands (and some parameters) as
a mixture of upper- and lower-case letters. The upper-case letters
indicate the abbreviated spelling for the command. For shorter program
lines, you can send the abbreviated form. For better program readability,
you can send the long form.
For example, in the above syntax statement, MEAS and MEASure are
both acceptable forms. You can use upper- or lower-case letters.
Therefore, MEASure, meas, and Meas are all acceptable. Other forms,
such as MEA and MEASUR, are not valid and will generate an error.
Braces ( { } ) enclose the parameter choices for a given command
string. The braces are not sent with the command string.
A vertical bar ( | ) separates multiple parameter choices for a given
command string. For example, {<label>|ALL} in the above
command indicates that you can specify a <label>, or "ALL". The
bar is not sent with the command string.
Angle brackets ( < > ) indicate that you must specify a value for
the enclosed parameter. For example, the above syntax statement
shows the <label> parameter enclosed in angle brackets. The
brackets are not sent with the command string. You must specify a
value for the parameter (for example, MEASure:INSTall:DELete
"MEZ_25") unless you select one of the other options shown in the
syntax (for example, MEASure:INSTall:DELete ALL).
Some parameters are enclosed in square brackets ( [ ] ). This
indicates that the parameter is optional. The brackets are not sent
with the command string. If you do not specify a value for an
optional parameter, the instrument chooses a default value.

Command Separators
A colon ( : ) separates a command keyword from a lower-level keyword.
You must insert a blank space to separate a parameter from a command
keyword. If a command requires more than one parameter, you must
separate adjacent parameters using a comma as shown below:
MEASure:THResholds:ABSolute (@1:4),90,50,10
A semicolon ( ; ) is used to separate commands within the same
subsystem, and can also minimize typing. For example, sending the
following command string:
TRIG:SOUR EXT; COUNT 10
... is the same as sending the following two commands:
TRIG:SOUR EXT
TRIG:COUNT 10
Use a colon and a semicolon to link commands from different
subsystems. For example, in the following command string, an error is
generated if you do not use both the colon and semicolon:
TRIG:COUN MIN;:SAMP:COUN MIN

Querying Parameter Settings
You can query the current value of most parameters by adding a
question mark ( ? ) to the command. For example, the following
command turns protection on for channels 1 through 4.
CONFigure:CHANnel:PROTection (@1:4),1
You can then query the protection by sending:
CONFigure:CHANnel:PROTection? (@1:4)
This would return +1,+1,+1,+1.

Command Terminators
A command string sent to the instrument must terminate with a <new
line> (<NL>) character. The IEEE-488 EOI (End-Or-Identify) message is
interpreted as a <NL> character and can be used to terminate a
command string in place of a <NL> character. A <carriage return>
followed by a <NL> is also accepted. Command string termination will
always reset the current command path to the root level.
For every message that includes a query and is sent
to the instrument , the instrument terminates the
returned response with a <NL> or line-feed character
(EOI). For example, if *IDN? is sent, the response is
terminated with a <NL> after the block of data that is
returned. If a message includes multiple queries
separated by semicolons (for example
"*ESR?;*IDN?"), the returned response is again
terminated by a <NL> after the response to the last
query. In either case, the program must read this
<NL> in the response before another command is
sent to the instrument, or an error will occur.

IEEE-488.2 Common Commands
The IEEE-488.2 standard defines a set of common commands that
perform functions such as reset, self-test, and status operations.
Common commands always begin with an asterisk ( * ), are three
characters in length, and may include one or more parameters.
The command keyword is separated from the first parameter by a
blank space. Use a semicolon ( ; ) to separate multiple commands as
shown below:
*RST; *CLS; *ESE 32; *OPC?

Parameter Types
The language defines several data formats to be used in program
messages and response messages.
Numeric Parameters
Commands that require numeric parameters will accept all commonly
used decimal representations of numbers including optional signs,
decimal points, and scientific notation. You can also send engineering
unit suffixes with numeric parameters (e.g., M, k, m, or u). If a command
accepts only certain specific values, the instrument will automatically
round the input numeric parameters to the accepted values. The
following command requires numeric parameters for the <vHigh>,
<vMid> and <vLow> parameters.
MEASure:THResholds:ABSolute (@<ch_list>)[,<vHigh>,<vMid>,
<vLow>]
Because the parser is case-insensitive, there is some
confusion over the letter "M" (or "m"). For your
convenience, the instrument interprets "mV" (or "MV")
as millivolts, and "MHZ" (or "mhz") as megahertz.
Likewise "MΩ" (or "mΩ") is interpreted as megohms.
You can use the prefix "MA" for mega. For example,
"MAV" is interpreted as megavolts.
Discrete Parameters
Discrete parameters are used to program settings that have a limited
number of values (like IMMediate, EXTernal, or BUS). They have a short
form and a long form just like command keywords. You can mix upper-
and lower-case letters. Query responses will always return the short form
in all upper-case letters. The following command requires a discrete

parameter for the trigger source:
CONFigure:TRIGger:SOURce
{IMMediate|SOFTware|EXTernal|CHANnel|OR}
Boolean Parameters
Boolean parameters represent a single binary condition that is either true
or false. For a false condition, the instrument will accept "OFF" or 0. For
a true condition, the instrument will accept "ON" or "1". When you query
a Boolean setting, the instrument will always return 0 or 1. The following
command requires a Boolean parameter:
CALibration:SECure:STATe {OFF|0|ON|1}
ASCII String Parameters
String parameters can contain virtually any set of ASCII characters. A
string must begin and end with matching quotes; either with a single
quote or a double quote. You can include the quote delimiter as part of
the string by typing it twice without any characters in between. The
following command uses a string parameter:
DISPlay:TEXT <quoted string>
For example, the following command displays the message "WAITING..."
on the instrument's front panel (the quotes are not displayed).
DISP:TEXT "WAITING..."
You can also display the same message using the following command
with single quotes.
DISP:TEXT 'WAITING...'

Using Device Clear
Device Clear is an IEEE-488 low-level bus message that you can use to
return the instrument to a responsive state. Different programming
languages and IEEE-488 interface cards provide access to this capability
through their own unique commands. The status registers, the error
queue, and all configuration states are left unchanged when a Device
Clear message is received.
Device Clear performs the following actions:
If a measurement is in progress, it is aborted.
The instrument returns to the trigger "idle" state.
The instrument's input and output buffers are cleared.
The instrument is prepared to accept a new command string.
An overlapped command, if any, will be terminated with no
"Operation Complete" indication.
The ABORt command is the recommended method to
terminate a measurement.

LAN Port Usage
The Keysight 34972A uses the following LAN ports:
Port 5024 is used for SCPI Telnet sessions.
Port 5025 is used for Socket sessions.

DHCP
Short for Dynamic Host Configuration Protocol, a protocol for assigning
dynamic IP addresses to devices on a network. With dynamic
addressing, a device can have a different IP address every time it
connects to the network.