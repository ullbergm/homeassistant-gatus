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
    from .models import GatusEndpoint


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: GatusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    coordinator = entry.runtime_data.coordinator
    known_endpoint_keys: set[str] = set()

    def _add_new_endpoints() -> None:
        """Add entities for any endpoints not yet registered."""
        if not coordinator.data or not isinstance(coordinator.data, list):
            return

        new_sensors: list[GatusEndpointBinarySensor] = []
        for endpoint in coordinator.data:
            if endpoint.key and endpoint.key not in known_endpoint_keys:
                known_endpoint_keys.add(endpoint.key)
                new_sensors.append(
                    GatusEndpointBinarySensor(
                        coordinator=coordinator,
                        endpoint_key=endpoint.key,
                        endpoint_name=endpoint.name,
                        endpoint_group=endpoint.group,
                    )
                )

        if new_sensors:
            async_add_entities(new_sensors)

    # Add initial entities and register a listener for future coordinator updates
    # so that endpoints added to Gatus after setup are picked up automatically.
    _add_new_endpoints()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_endpoints))


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

    def _find_endpoint(self) -> GatusEndpoint | None:
        """Find this endpoint's typed data in the coordinator data."""
        if not self.coordinator.data or not isinstance(self.coordinator.data, list):
            return None

        for endpoint in self.coordinator.data:
            if endpoint.key == self._endpoint_key:
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

        # Check if this specific endpoint exists in the data and has a latest result
        endpoint = self._find_endpoint()
        if endpoint is None:
            LOGGER.debug(
                "Entity %s unavailable: endpoint data not found for key %s",
                self.entity_id,
                self._endpoint_key,
            )
            return False

        if endpoint.latest_result is None:
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
        endpoint = self._find_endpoint()
        if endpoint is None:
            return True  # No data = problem

        latest = endpoint.latest_result
        if latest is None:
            return True  # No results = problem

        return not latest.success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        endpoint = self._find_endpoint()
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
