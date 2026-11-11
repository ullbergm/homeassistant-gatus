"""Binary sensor platform for gatus_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .entity import GatusEndpointEntity, async_track_endpoints

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import GatusDataUpdateCoordinator
    from .data import GatusConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: GatusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_track_endpoints(
        entry,
        async_add_entities,
        lambda coordinator, endpoint: GatusEndpointBinarySensor(
            coordinator=coordinator,
            endpoint_key=endpoint.key,
            endpoint_name=endpoint.name,
            endpoint_group=endpoint.group,
        ),
    )


class GatusEndpointBinarySensor(GatusEndpointEntity, BinarySensorEntity):
    """Gatus endpoint binary sensor class."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    # These change on every health check; keep them out of the recorder so the
    # attributes table does not grow with every poll.
    _unrecorded_attributes = frozenset({"duration_ms", "timestamp"})

    def __init__(
        self,
        coordinator: GatusDataUpdateCoordinator,
        endpoint_key: str,
        endpoint_name: str,
        endpoint_group: str,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator, endpoint_key, endpoint_name, endpoint_group)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{endpoint_key}"
        # Using has_entity_name=True, so just the endpoint identification
        self._attr_name = self._endpoint_label

    @property
    def is_on(self) -> bool:
        """Return true if there is a problem (failure detected)."""
        endpoint = self._get_endpoint()
        if endpoint is None:
            return True  # No data = problem

        latest = endpoint.latest_result
        if latest is None:
            return True  # No results = problem

        return not latest.success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        endpoint = self._get_endpoint()
        if endpoint is None:
            return {}

        latest = endpoint.latest_result
        if latest is None:
            return {}

        return {
            "endpoint_group": self._endpoint_group,
            "endpoint_name": self._endpoint_name,
            "hostname": latest.hostname,
            "status_code": latest.status_code,
            "duration_ms": latest.duration_ms,
            "timestamp": latest.timestamp,
        }
