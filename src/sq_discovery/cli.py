"""Command line entry point for scanning local mDNS devices."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Sequence
from dataclasses import asdict
from threading import Event

from zeroconf import IPVersion

from .scanner import discover_services


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan the local network for mDNS/Bonjour devices.")
    parser.add_argument("--find", action="store_true", help="Browse all service types discovered on the network")
    parser.add_argument("--service-type", action="append", dest="service_types", help="Service type to browse, can be repeated")
    parser.add_argument("--v6-only", action="store_true")
    parser.add_argument("--v4-only", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--duration", type=float, default=15.0, help="Seconds to scan before exiting")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object per discovered service")
    args = parser.parse_args(argv)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.v6_only:
        ip_version = IPVersion.V6Only
    elif args.v4_only:
        ip_version = IPVersion.V4Only
    else:
        ip_version = IPVersion.All

    def on_event(message: str) -> None:
        if not args.json:
            print(message)

    def on_service(service) -> None:
        payload = asdict(service)
        payload["kind"] = "service"
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(json.dumps(payload, indent=2, sort_keys=True))

    discover_services(
        service_types=args.service_types,
        find_all=args.find,
        ip_version=ip_version,
        stop_event=Event(),
        duration=args.duration,
        on_event=on_event,
        on_service=on_service,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
