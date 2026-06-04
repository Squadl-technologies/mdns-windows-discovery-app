"""Shared discovery logic for the Windows CLI and service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Event
from time import monotonic, sleep
from typing import cast

from zeroconf import IPVersion, ServiceBrowser, ServiceStateChange, Zeroconf, ZeroconfServiceTypes


@dataclass(slots=True)
class DiscoveredService:
    service_type: str
    name: str
    addresses: list[str] = field(default_factory=list)
    port: int | None = None
    server: str | None = None
    properties: dict[str, str] = field(default_factory=dict)


def discover_services(
    *,
    service_types: list[str] | None = None,
    find_all: bool = False,
    ip_version: IPVersion = IPVersion.All,
    stop_event: Event | None = None,
    duration: float | None = None,
    on_event: Callable[[str], None] | None = None,
    on_service: Callable[[DiscoveredService], None] | None = None,
    on_service_removed: Callable[[str, str], None] | None = None,
) -> None:
    """Browse for mDNS services and emit results through callbacks."""

    def emit(message: str) -> None:
        if on_event is not None:
            on_event(message)

    zeroconf = Zeroconf(ip_version=ip_version)
    services = service_types or ["_http._tcp.local.", "_hap._tcp.local.", "_airplay._tcp.local."]
    if find_all and service_types is None:
        services = list(ZeroconfServiceTypes.find(zc=zeroconf))
        if not services:
            services = ["_http._tcp.local.", "_hap._tcp.local.", "_airplay._tcp.local."]
            emit("find_all returned no service types; falling back to default service list")

    def on_service_state_change(
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        emit(f"{state_change.name}: {name} ({service_type})")
        if state_change is ServiceStateChange.Removed:
            if on_service_removed is not None:
                on_service_removed(service_type, name)
            return
        if state_change is not ServiceStateChange.Added:
            return
        info = zeroconf.get_service_info(service_type, name)
        if info is None:
            emit("  no service info")
            return
        discovered = DiscoveredService(
            service_type=service_type,
            name=name,
            addresses=[f"{addr}:{cast(int, info.port)}" for addr in info.parsed_scoped_addresses()],
            port=info.port,
            server=info.server,
            properties={str(key): value.decode(errors="replace") if isinstance(value, bytes) else str(value) for key, value in info.properties.items()},
        )
        if on_service is not None:
            on_service(discovered)

    emit(f"browsing {len(services)} service type(s)")
    deadline = None if duration is None else monotonic() + duration
    try:
        with ServiceBrowser(zeroconf, services, handlers=[on_service_state_change]):
            while True:
                if stop_event is not None and stop_event.is_set():
                    break
                if deadline is not None and monotonic() >= deadline:
                    break
                sleep(1)
    finally:
        zeroconf.close()
