# Hardware setup and checkout

- Board A outputs 0–3 are logical CH1–CH4.
- Board B outputs 0–3 are logical CH5–CH8.
- Label both USB devices and relay wiring with their Phidget serial numbers.
- Confirm whether energized means contact closed before using the library.
- Begin with an unpowered load and run example 07 while checking every channel.
- Verify contact continuity with a DMM; software state is only commanded state.
- Confirm the load voltage/current and isolation stay within the exact hardware
  variant's ratings. Add fusing and emergency isolation where appropriate.

If two devices appear reversed, correct the serial arguments; do not swap
logical mappings in code. If attachment times out, verify the OS driver,
Control Panel access, USB power, serial value, and that no other process holds
the channel.

