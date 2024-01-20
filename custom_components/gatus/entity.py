"""GatusEntity class."""
from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME, VERSION
from .coordinator import GatusDataUpdateCoordinator


class GatusEntity(CoordinatorEntity):
    """GatusEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: GatusDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = "binary_sensor.gatus_" + coordinator.config_entry.data[CONF_HOST]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=coordinator.config_entry.data[CONF_HOST],
            model=VERSION,
            manufacturer=NAME,
            configuration_url="https://" + coordinator.config_entry.data[CONF_HOST],
        )
