# Release v26.14 serial-echo handling review

## Finding

The uploaded bench log labels exact copies of write requests as responses.
Those copies have command bytes `0x20` and `0x5D`. The BK8500 write protocol
requires command `0x12` in the response and status `0x80` for success.

## Root cause

The driver previously read exactly one 26-byte frame. On a serial path with
local echo, that first frame is the transmitted request, so the driver rejected
it before a later device response could be read.

## Correction

1. Reproduce the verified closed-port DTR/RTS setup.
2. Reassert both lines after open.
3. Wait one second before traffic.
4. For write commands only, identify an exact request copy as local echo.
5. Continue reading within the original transaction deadline.
6. Accept only the actual status frame.
7. Treat echo without a device response as timeout.
8. Reject an all-zero product identity as an echoed query signature.

## Safety decision

The library does not accept echo alone as success. Doing so would allow a
disconnected or incorrectly wired adapter to make hazardous load commands look
successful.

## API impact

No public keyword names or signatures changed.
