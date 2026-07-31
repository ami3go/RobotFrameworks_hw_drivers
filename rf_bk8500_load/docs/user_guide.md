# User guide


> **Verified baseline:** all 55 public keywords and the list persistence
> workflow passed on physical model 8500, serial `1687710135`, firmware
> `1.84`, using COM12 at 9600 baud. Release 26.16 keeps the verified
> v26.14 protocol path and adds optional read-only baud detection.

## Install

```bash
pip install -e .          # from the package root
# or, from the built wheel
pip install dist/bk8500_load-26.16.0-py3-none-any.whl
```

Requirements: Python 3.9+, `pyserial` for hardware, `robotframework` for the
keyword layer. On Linux add your user to the `dialout` group, or you will get
`BK8500ConnectionError: Cannot open /dev/ttyUSB0: Permission denied`.

## Wire it up

1. Connect the DC load to the PC with the vendor's **IT-E132B USB-to-TTL**
   adapter.

   > **The rear panel DB9 carries TTL levels, not RS-232.** Connecting it
   > directly to a standard RS-232 port can damage the instrument. Use the
   > IT-E132B or an equivalent level shifter.

   The manual also requires that **DTR and RTS be asserted**; the adapter takes
   part of its interface enable from those lines. The driver raises both
   explicitly on open and verifies the result, so a stubborn adapter fails with
   a message naming the line instead of a bare timeout. `assert_dtr` and
   `assert_rts` exist as escape hatches and should be left alone.
2. On the front panel, set the communication baud rate (`Shift` + `Menu` →
   `Connect`) and note it. The instrument supports **4800, 9600, 19200 and
   38400** only; the driver rejects anything else. The default here is 9600.
3. Set the instrument address to 0 unless your bench uses multi-drop.
4. Connect the DUT to the input terminals **with the correct polarity**. If the
   test needs accurate voltage at the DUT rather than at the load, wire the
   sense terminals too and enable remote sensing.

## Smallest working suite

```robotframework
*** Settings ***
Library           BK8500Library    port=/dev/ttyUSB0    baudrate=9600    model=8500
Suite Teardown    Close All Load Connections
Test Teardown     Load Input Off

*** Test Cases ***
Supply Holds Voltage Under Two Amps
    Claim Remote Control
    Configure Load Protection    max_voltage=${20}    max_current=${5}    max_power=${100}
    Apply Constant Current    ${2.0}    enable_input=${TRUE}
    Wait Until Load Reading Is Stable    quantity=current    tolerance=${0.02}
    Load Current Should Be Within    ${2.0}    ${0.05}
    Load Voltage Should Be Within    ${12.0}    ${0.2}
    Load Should Report No Protection Faults
```

## Developing without hardware

Every keyword works against the built-in instrument model:

```robotframework
Library    BK8500Library    simulated=${TRUE}    model=8500
...        source_voltage=${12.0}    source_resistance=${0.05}
```

The simulator gives physically consistent readings for all four modes, so
sequencing, teardown and oracle logic can all be developed and run in CI. It
does not model instrument accuracy, slew rate or thermal behaviour, so a
simulated pass is never evidence for a measurement objective.

Run the bundled suite either way:

```bash
robot --outputdir results atest                                   # simulated
robot --outputdir results --variable SIMULATED:False \
      --variable PORT:/dev/ttyUSB0 --exclude deliberate_fault atest   # hardware
```

## Choosing a mode

| Mode | The load holds constant | Typical use |
|------|------------------------|-------------|
| `CC` | current | Supply regulation, efficiency, thermal soak |
| `CV` | terminal voltage | Testing a source's current limit, charger characterisation |
| `CW` | power | Battery run-time, constant-power discharge |
| `CR` | resistance | Emulating a resistive load, gentle start-up |

Each mode keeps its own setpoint register. Switching mode applies whatever that
mode's register already contains, which is why `Apply Constant Current` and its
siblings always write the setpoint before closing the input.

## Multiple loads in one suite

```robotframework
Open Load Connection    port=/dev/ttyUSB0    model=8500    alias=main_rail
Open Load Connection    port=/dev/ttyUSB1    model=8502    alias=aux_rail
Switch Load Connection  main_rail
Apply Constant Current  ${2.0}    enable_input=${TRUE}
Switch Load Connection  aux_rail
Apply Constant Current  ${0.5}    enable_input=${TRUE}
```

Each alias is an independent instrument on its own port. Do not point two
aliases at the same port.

## Transients and lists

```robotframework
# Toggle between 1 A and 2 A, 10 ms each, triggered from the bus
Configure Load Transient    CC    ${1.0}    ${0.010}    ${2.0}    ${0.020}    operation=CONTINUOUS
Set Load Function           TRANSIENT
Set Load Trigger Source     BUS
Load Input On
Trigger Load

# A three step profile
${steps}=    Evaluate    [(0.5, 0.05), (1.5, 0.10), (2.5, 0.15)]
Configure Load List    CC    ${steps}    repeat=ONCE    name=PROFILE1
```

The driver forces the input OFF before list editing, requires at least two steps,
and validates the list length against the active memory partition
(1000/500/250/120 steps). Persistent save
and recall keywords include an EEPROM settle barrier before returning.

```robotframework
Set Load Function      LIST
```

Dwell times are seconds on the keyword interface, quantised to 0.1 ms on the
wire. The field is two bytes, so **6.5535 s is the hard maximum per step**;
longer profiles are built from several steps or driven from the test itself.

Bus trigger latency over the serial link is tens of milliseconds and jitters
with baud rate. If a measurement needs tighter alignment than about 50 ms, use
the rear panel external trigger input instead.

## Reading the instrument

`Measure Load Input` is one transaction and returns everything at once:

```robotframework
${reading}=    Measure Load Input
Log    ${reading}[voltage_v] V, ${reading}[current_a] A, ${reading}[power_w] W
Should Be Empty    ${reading}[active_protections]
```

Prefer it over three separate `Get Load Voltage` / `Current` / `Power` calls:
one round trip instead of three, and the three values are consistent with each
other.

`operation_state` and `demand_state` expose the raw status registers as named
booleans — `input_on`, `waiting_for_trigger`, `remote_sense_enabled`,
`constant_current`, `over_temperature` and so on.

## Choosing tolerances

Start from the instrument's accuracy, then add the DUT's own specification:

* current: ±(0.2 % of reading + 0.15 % of full scale)
* voltage: ±(0.02 % of reading + 0.025 % of full scale)
* power: ±(1 % of reading + 0.1 % of full scale)

A tolerance tighter than the instrument's accuracy produces intermittent
failures that tell you nothing about the DUT.

## When something goes wrong

| Symptom | Likely cause | What to do |
|---------|--------------|------------|
| `BK8500TimeoutError` on the first keyword | Baud rate mismatch, instrument off, wrong port, wrong address, or DTR/RTS not asserted | Check the front panel `Connect` menu against the suite variables. The adapter LEDs blink only when frames actually move; if they are dark, suspect the signal lines. `Get Load Connection Info` reports the measured DTR and RTS state |
| `BK8500ConnectionError: DTR did not assert` | The USB-serial driver will not raise the line — common with third-party PL-2303 clones | Install the vendor's Prolific driver, or try another adapter. Do not work around it with `assert_dtr=${FALSE}`: the instrument needs the line |
| `BK8500ConfigurationError: Baud rate ... not supported` | A rate above 38400 | The firmware supports 4800, 9600, 19200 and 38400 only |
| `BK8500CommandError ... status 0xB0` | Remote control not claimed, or a bus trigger with the wrong trigger source | Add `Claim Remote Control`, or set the trigger source to `BUS` |
| `BK8500CommandError ... status 0xA0` | The value exceeded the instrument's own limit | Check the setpoint against the protection limits currently programmed |
| `BK8500ValidationError` | The driver refused before transmitting | Read the message: it names the permitted range and the model it used |
| `BK8500ProtectionError` | The instrument tripped | Open the input, find the cause. Do not clear and retry automatically |
| `BK8500ProtocolError` after retries | Line noise, another process on the same port, or a reply from a different instrument address | Check the cable and that nothing else has the port open |
| `BK8500ProtocolError: Ambiguous reply` | The instrument answered a read with a bare success status and no data — that read is probably unsupported by this firmware | Route the objective to another instrument; report the firmware version |
| Front panel unresponsive after a crashed run | Remote control left claimed | Press `Shift` + `Local`, or run `Reset Load To Safe State` |

## First contact with a new instrument

Two things are worth logging on the first hardware run, because the manual does
not pin them down:

```robotframework
${info}=    Get Load Connection Info
Log    Reply framing: ${info}[response_style]     # echo or status_tagged
Log    Signal lines: ${info}[signal_lines]        # both should be true
${product}=    Get Load Product Information
Log    Firmware ${product}[firmware_version] raw ${product}[firmware_raw]
```

Compare the firmware string against the front panel. The driver decodes it as
hexadecimal; if the panel disagrees, the encoding is BCD and the raw bytes are
the value to trust.

## Safety checklist before an unattended run

- Protection limits set from the **DUT's** rating, not the instrument's.
- Test teardown calls `Load Input Off` and runs on failure.
- Suite teardown calls `Reset Load To Safe State` and `Close All Load Connections`.
- The front panel LOCAL key is left enabled.
- No use of `Set Load Function Unchecked` without written authorisation.
- Wiring and fixture rated above the highest current the suite programs.
- Airflow around the instrument adequate for sustained high-power tests.

## Automatic baud-rate detection

Use automatic detection when the instrument front-panel baud may differ from
the bench configuration:

```robotframework
Open Load Connection    port=COM12    baudrate=AUTO
```

To retain a preferred rate and fall back only when it fails:

```robotframework
Open Load Connection    port=COM12    baudrate=9600
...    auto_detect_baudrate=${TRUE}
...    baudrate_candidates=4800,9600,19200,38400
...    probe_timeout=0.75
```

The probe is read-only and uses product-information query `0x6A`. By default,
two consecutive identities must match. Read the selected value and evidence
through `Get Load Connection Info`.
