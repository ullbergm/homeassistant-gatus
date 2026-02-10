"""GatusEntity class."""

from __future__ import annotations

from urllib.parse import urlparse

from homeassistant.const import CONF_URL
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import GatusDataUpdateCoordinator


class GatusEntity(CoordinatorEntity[GatusDataUpdateCoordinator]):
    """GatusEntity class."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: GatusDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        # Get the Gatus URL for the device name
        gatus_url = coordinator.config_entry.data.get(CONF_URL, "Gatus")
        # Extract just the hostname from the URL for a cleaner name
        try:
            parsed = urlparse(gatus_url)
            device_name = parsed.netloc or gatus_url
        except (ValueError, AttributeError):
            device_name = gatus_url

        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    coordinator.config_entry.entry_id,
                ),
            },
            name=f"Gatus ({device_name})",
            manufacturer="Gatus",
            model="Health Monitor",
            configuration_url=gatus_url,
        )
