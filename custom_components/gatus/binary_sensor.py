"""Binary sensor platform for Gatus."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import DOMAIN
from .coordinator import GatusDataUpdateCoordinator
from .entity import GatusEntity

PARALLEL_UPDATES = 1

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    ) -> None:
    """Set up the Gatus platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        GatusBinarySensor(
            coordinator=coordinator,
            entity_description=BinarySensorEntityDescription(
                key=endpoint["key"],
                name=endpoint["name"] + " Healthy",
                icon="mdi:network-outline",
                device_class=BinarySensorDeviceClass.CONNECTIVITY,
            )
        )
        for endpoint in hass.data[DOMAIN][entry.entry_id].endpoints
    )


class GatusBinarySensor(GatusEntity, BinarySensorEntity):
    """Gatus binary_sensor class."""

    def __init__(
        self,
        coordinator: GatusDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        # return self.coordinator.data.get("title", "") == "foo"
        for x in self.coordinator.endpoints:
            if self.entity_description.key == x["key"]:
                return x["results"][0]["success"]

    @property
    def extra_state_attributes(self) -> dict[str, str | int | datetime]:
        """Return the state attributes of the sensor."""
        for x in self.coordinator.endpoints:
            if self.entity_description.key == x["key"]:
                attrs: dict[str, str | int | datetime] = {}
                attrs["response time"] = x["results"][0]["duration"] / 1000000
                attrs["timestamp"] = x["results"][0]["timestamp"]
                attrs["status"] = x["results"][0]["status"]
                attrs["group"] = x["group"]
                self._attr_name = x["name"] + " healthy"
                return attrs

        return {}