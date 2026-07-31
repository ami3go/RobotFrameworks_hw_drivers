#!/usr/bin/env python3
"""Diagnose BK8500 serial echo versus real instrument responses.

This utility follows the proven bench opening sequence:
1. create the pyserial object closed;
2. request DTR and RTS high;
3. open the selected COM port;
4. reassert DTR and RTS;
5. wait one second;
6. transmit a 26-byte packet.

Unlike a simple loopback check, it does not count an exact copy of a write
request as instrument success.  The BK8500 protocol requires write commands to
return command 0x12 with a status byte, normally 0x80.
"""

from __future__ import annotations

import argparse
import time

import serial

from bk8500_load import protocol as p


def read_exactly(ser: serial.Serial, count: int, deadline: float) -> bytes:
    received = bytearray()
    while len(received) < count and time.monotonic() < deadline:
        chunk = ser.read(count - len(received))
        if chunk:
            received.extend(chunk)
    return bytes(received)


def exchange(ser: serial.Serial, frame: bytes, timeout_s: float) -> tuple[bytes | None, bool]:
    ser.reset_input_buffer()
    ser.write(frame)
    ser.flush()
    print("TX:", p.format_frame(frame))

    deadline = time.monotonic() + timeout_s
    first = read_exactly(ser, p.PACKET_LENGTH, deadline)
    if len(first) != p.PACKET_LENGTH:
        print(f"RX: timeout/short frame ({len(first)} bytes)")
        return None, False
    print("RX1:", p.format_frame(first))

    echo_seen = first == frame
    if echo_seen:
        expected = "device status" if p.command_expects_status(frame[2]) else "device data"
        print(f"RX1 classification: exact local echo candidate; waiting for {expected}")
        second = read_exactly(ser, p.PACKET_LENGTH, deadline)
        if len(second) != p.PACKET_LENGTH:
            print("RX2: no device response followed the echo")
            return None, True
        print("RX2:", p.format_frame(second))
        return second, True

    return first, echo_seen


def require_status(command: int, response: bytes | None) -> bool:
    if response is None:
        return False
    ok, reason = p.frame_is_well_formed(response)
    if not ok:
        print("Response validation failed:", reason)
        return False
    if response[2] != int(p.Command.STATUS):
        print(
            f"Expected status command 0x12 for write 0x{command:02X}, "
            f"received 0x{response[2]:02X}"
        )
        return False
    print(f"Device status: 0x{response[3]:02X} ({p.STATUS_TEXT.get(response[3], 'unknown')})")
    return response[3] == int(p.StatusCode.SUCCESS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM12")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--address", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()

    ser = serial.Serial(
        port=None,
        baudrate=args.baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=args.timeout,
        write_timeout=args.timeout,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
    )
    ser.dtr = True
    ser.rts = True
    ser.port = args.port

    try:
        ser.open()
        ser.dtr = True
        ser.rts = True
        time.sleep(1.0)
        print(f"Port={ser.port} baud={ser.baudrate} DTR={ser.dtr} RTS={ser.rts}")

        remote = p.build_frame(args.address, p.Command.SET_REMOTE, bytes([1]))
        response, _ = exchange(ser, remote, args.timeout)
        if not require_status(int(p.Command.SET_REMOTE), response):
            print("FAIL: remote command was not acknowledged by the instrument")
            return 2

        fixed = p.build_frame(args.address, p.Command.SET_FUNCTION, bytes([0]))
        response, _ = exchange(ser, fixed, args.timeout)
        if not require_status(int(p.Command.SET_FUNCTION), response):
            print("FAIL: fixed-function command was not acknowledged by the instrument")
            return 3

        identity = p.build_frame(args.address, p.Command.GET_PRODUCT_INFO)
        response, echo_seen = exchange(ser, identity, args.timeout)
        if response is None:
            print("FAIL: no product-information response")
            return 4
        ok, reason = p.frame_is_well_formed(response)
        if not ok:
            print("FAIL:", reason)
            return 5
        payload = response[3:25]
        model = payload[0:5].split(b"\x00")[0].decode("ascii", "replace").strip()
        serial_number = payload[7:17].split(b"\x00")[0].decode("ascii", "replace").strip()
        firmware = f"{payload[6]:X}.{payload[5]:02X}"
        if not any(payload):
            print("FAIL: identity frame is empty and matches an echoed request signature")
            return 6
        print(
            f"PASS: model={model!r} serial={serial_number!r} firmware={firmware} "
            f"echo_seen={echo_seen}"
        )
        return 0
    finally:
        if ser.is_open:
            ser.close()


if __name__ == "__main__":
    raise SystemExit(main())
