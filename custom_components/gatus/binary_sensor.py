"""Binary sensor platform for gatus_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .const import LOGGER
from .entity import GatusEntity

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
    coordinator = entry.runtime_data.coordinator

    # Create a binary sensor for each endpoint from Gatus
    sensors = []
    if coordinator.data and isinstance(coordinator.data, list):
        sensors.extend(
            GatusEndpointBinarySensor(
                coordinator=coordinator,
                endpoint_key=endpoint.get("key"),
                endpoint_name=endpoint.get("name"),
                endpoint_group=endpoint.get("group"),
            )
            for endpoint in coordinator.data
        )

    async_add_entities(sensors)


class GatusEndpointBinarySensor(GatusEntity, BinarySensorEntity):
    """Gatus endpoint binary sensor class."""

    def __init__(
        self,
        coordinator: GatusDataUpdateCoordinator,
        endpoint_key: str,
        endpoint_name: str,
        endpoint_group: str,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self._endpoint_key = endpoint_key
        self._endpoint_name = endpoint_name
        self._endpoint_group = endpoint_group
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{endpoint_key}"
        # Using has_entity_name=True, so just the endpoint identification
        self._attr_name = f"{endpoint_group} {endpoint_name}"
        self._attr_translation_key = "endpoint_status"

    def _find_endpoint_data(self) -> dict[str, Any] | None:
        """Find this endpoint's data in the coordinator data."""
        if not self.coordinator.data or not isinstance(self.coordinator.data, list):
            return None

        for endpoint in self.coordinator.data:
            if endpoint.get("key") == self._endpoint_key:
                return endpoint

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # First check if coordinator is available (handles update failures)
        if not self.coordinator.last_update_success:
            LOGGER.debug(
                "Entity %s unavailable: coordinator update failed", self.entity_id
            )
            return False

        # Check if this specific endpoint exists in the data and has results
        endpoint_data = self._find_endpoint_data()
        if endpoint_data is None:
            LOGGER.debug(
                "Entity %s unavailable: endpoint data not found for key %s",
                self.entity_id,
                self._endpoint_key,
            )
            return False

        # Check if endpoint has results
        results = endpoint_data.get("results", [])
        if len(results) == 0:
            LOGGER.debug(
                "Entity %s unavailable: no results for endpoint %s",
                self.entity_id,
                self._endpoint_key,
            )
            return False

        LOGGER.debug("Entity %s is available", self.entity_id)
        return True

    @property
    def is_on(self) -> bool:
        """Return true if there is a problem (failure detected)."""
        endpoint_data = self._find_endpoint_data()
        if endpoint_data is None:
            return True  # No data = problem

        # Get the most recent result
        results = endpoint_data.get("results", [])
        if results:
            # Return True if there's a problem (NOT successful)
            return not results[-1].get("success", False)

        return True  # No results = problem

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        endpoint_data = self._find_endpoint_data()
        if endpoint_data is None:
            return {}

        results = endpoint_data.get("results", [])
        if results:
            latest_result = results[-1]
            return {
                "endpoint_group": self._endpoint_group,
                "endpoint_name": self._endpoint_name,
                "hostname": latest_result.get("hostname"),
                "status_code": latest_result.get("status"),
                "duration_ms": latest_result.get("duration", 0)
                / 1_000_000,  # Convert nanoseconds to milliseconds
                "timestamp": latest_result.get("timestamp"),
            }

        return {}
