"""Small diagnostic CLI. It never probes devices in the list-ports command."""
from __future__ import annotations

import argparse
import json
import sys

from . import BK8500B, DriverConfig, Protocol
from .transport import list_serial_ports


def _protocol(value: str) -> Protocol:
    try:
        return Protocol(value.lower())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bk8500b", description="B&K 8500B diagnostic utility")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-ports", help="List serial ports without probing")
    for name in ("identify", "measure", "diagnostic"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--port", required=True)
        cmd.add_argument("--protocol", type=_protocol, default=Protocol.SCPI)
        cmd.add_argument("--address", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "list-ports":
        print(json.dumps([p.__dict__ if hasattr(p, "__dict__") else {
            "device": p.device,
            "description": p.description,
            "hardware_id": p.hardware_id,
            "manufacturer": p.manufacturer,
            "serial_number": p.serial_number,
        } for p in list_serial_ports()], indent=2))
        return 0
    config = DriverConfig(port=args.port, protocol=args.protocol, address=args.address)
    try:
        with BK8500B(config) as device:
            if args.command == "identify":
                identity = device.identify()
                print(json.dumps({
                    "manufacturer": identity.manufacturer,
                    "model": identity.model,
                    "serial_number": identity.serial_number,
                    "firmware_revision": identity.firmware_revision,
                }, indent=2))
            elif args.command == "measure":
                snapshot = device.measure_all()
                print(json.dumps({
                    "voltage_v": snapshot.voltage.value,
                    "current_a": snapshot.current.value,
                    "power_w": snapshot.power.value,
                    "resistance_ohm": None if snapshot.resistance is None else snapshot.resistance.value,
                }, indent=2))
            else:
                print(json.dumps(device.diagnostic_snapshot().to_dict(), indent=2))
        return 0
    except Exception as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
