"""Windows Service support for the mDNS scanner."""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

try:
    import win32event
    import win32service
    import win32serviceutil
except ImportError as exc:  # pragma: no cover - Windows only
    raise RuntimeError("pywin32 is required to run the Windows service") from exc

from .service import ScannerService, _configure_logging, _prepare_service_state, _service_root, run_service_debug


class MdnsScannerWindowsService(win32serviceutil.ServiceFramework):  # pragma: no cover - Windows only
    _svc_name_ = "sq-discovery"
    _svc_display_name_ = "sq-discovery"
    _svc_description_ = "Continuously discovers mDNS/Bonjour devices on the local network."
    _svc_start_type_ = win32service.SERVICE_AUTO_START

    def __init__(self, args):
        super().__init__(args)
        self._stop_event = win32event.CreateEvent(None, 0, 0, None)
        self._scanner = ScannerService()
        self._bootstrap_thread = None
        self._scanner_thread = None
        self._service_dir = _service_root()
        self._log_path = self._service_dir / "logs" / "sq-discovery-service.log"

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self._scanner.stop()
        win32event.SetEvent(self._stop_event)

    def _scanner_loop(self) -> None:
        try:
            self._scanner.run()
        except Exception as exc:
            logging.exception("Scanner loop failed")
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)
            win32event.SetEvent(self._stop_event)

    def _bootstrap(self) -> None:
        try:
            self._service_dir.mkdir(parents=True, exist_ok=True)
            _prepare_service_state()
            _configure_logging(str(self._log_path))
            logging.info("Starting sq-discovery service")
            self._scanner_thread = threading.Thread(target=self._scanner_loop, daemon=True)
            self._scanner_thread.start()
        except Exception as exc:  # pragma: no cover - Windows only
            logging.exception("Service bootstrap failed")
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)
            win32event.SetEvent(self._stop_event)

    def SvcDoRun(self):
        try:
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self._bootstrap_thread = threading.Thread(target=self._bootstrap, daemon=True)
            self._bootstrap_thread.start()
            win32event.WaitForSingleObject(self._stop_event, win32event.INFINITE)
            logging.info("Stopping sq-discovery service")
        except Exception as exc:  # pragma: no cover - Windows only
            raise
        finally:
            self._scanner.stop()
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - Windows only
    original_argv = sys.argv[:]
    try:
        if argv is not None:
            sys.argv = [sys.argv[0], *argv]
        if len(sys.argv) > 1 and sys.argv[1].lower() == "debug":
            raise SystemExit(run_service_debug())
        win32serviceutil.HandleCommandLine(MdnsScannerWindowsService)
    finally:
        sys.argv = original_argv
