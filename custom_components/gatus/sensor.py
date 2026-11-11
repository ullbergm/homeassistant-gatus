"""Sensor platform for gatus_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime

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
    """Set up the sensor platform."""
    async_track_endpoints(
        entry,
        async_add_entities,
        lambda coordinator, endpoint: GatusEndpointResponseTimeSensor(
            coordinator=coordinator,
            endpoint_key=endpoint.key,
            endpoint_name=endpoint.name,
            endpoint_group=endpoint.group,
        ),
    )


class GatusEndpointResponseTimeSensor(GatusEndpointEntity, SensorEntity):
    """Response time of the latest health check for a Gatus endpoint."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    # Opt-in: one extra entity (and one recorder row per poll) per endpoint.
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: GatusDataUpdateCoordinator,
        endpoint_key: str,
        endpoint_name: str,
        endpoint_group: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, endpoint_key, endpoint_name, endpoint_group)
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{endpoint_key}_response_time"
        )
        self._attr_name = f"{self._endpoint_label} response time"

    @property
    def native_value(self) -> float | None:
        """Return the latest response time in milliseconds."""
        endpoint = self._get_endpoint()
        if endpoint is None or endpoint.latest_result is None:
            return None
        return round(endpoint.latest_result.duration_ms, 3)
