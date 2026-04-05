"""Diagnostics support for Gatus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_URL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import GatusConfigEntry

_REDACT = {CONF_URL}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: GatusConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator

    endpoint_summary: list[dict[str, Any]] = []
    if coordinator.data and isinstance(coordinator.data, list):
        for endpoint in coordinator.data:
            latest = endpoint.latest_result
            endpoint_summary.append(
                {
                    "key": endpoint.key,
                    "name": endpoint.name,
                    "group": endpoint.group,
                    "success": latest.success if latest else None,
                    "status_code": latest.status_code if latest else None,
                    "duration_ms": latest.duration_ms if latest else None,
                    "timestamp": latest.timestamp if latest else None,
                    "result_count": len(endpoint.results),
                }
            )

    return {
        "config_entry": async_redact_data(entry.as_dict(), _REDACT),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": str(coordinator.last_exception)
            if coordinator.last_exception
            else None,
            "endpoint_count": len(endpoint_summary),
        },
        "endpoints": endpoint_summary,
    }
