"""Unified entry point for the SQ-Discovery executable."""

from __future__ import annotations

import argparse
import sys

import ifaddr  # noqa: F401

from sq_discovery.cli import main as scan_main
from sq_discovery.win_service import MdnsScannerWindowsService, main as service_admin_main


def main() -> int:
    if sys.platform == "win32" and len(sys.argv) == 1:
        import servicemanager

        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MdnsScannerWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
        return 0

    if sys.platform == "win32" and len(sys.argv) > 1 and sys.argv[1].lower() in {
        "install",
        "remove",
        "start",
        "stop",
        "restart",
        "debug",
    }:
        return service_admin_main(sys.argv[1:])

    parser = argparse.ArgumentParser(description="SQ-Discovery mDNS discovery tool")
    parser.add_argument(
        "--service",
        nargs="*",
        help="Windows service command, for example install/start/stop/remove",
    )
    args, remaining = parser.parse_known_args()

    if args.service:
        return service_admin_main(args.service)
    return scan_main(remaining)


if __name__ == "__main__":
    raise SystemExit(main())
