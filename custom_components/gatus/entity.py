"""GatusEntity class."""

from __future__ import annotations

from urllib.parse import urlparse

from awesomeversion import AwesomeVersion
from awesomeversion.exceptions import AwesomeVersionException

from homeassistant.const import CONF_URL
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, LOGGER
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

        # Retrieve the integration version for device registry display
        try:
            integration_version = (
                coordinator.config_entry.runtime_data.integration.version
            )
        except AttributeError:
            integration_version = None

        sw_version = self._normalize_sw_version(integration_version)

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
            sw_version=sw_version,
        )

    @staticmethod
    def _normalize_sw_version(integration_version: object | None) -> str | None:
        """Return a safe software version string for device registry."""
        if integration_version is None:
            return None

        version = str(integration_version).strip()
        if not version:
            return None

        try:
            AwesomeVersion(version)
        except AwesomeVersionException:
            LOGGER.debug(
                "Skipping invalid integration version for sw_version: %s", version
            )
            return None

        return version
