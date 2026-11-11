"""GatusEntity class."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from homeassistant.const import CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, LOGGER
from .coordinator import GatusDataUpdateCoordinator

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import GatusConfigEntry
    from .models import GatusEndpoint


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
            entry_type=DeviceEntryType.SERVICE,
            # Earlier releases stored the integration's own version here, which
            # is not the Gatus version. Passing None clears that stale value.
            sw_version=None,
        )


class GatusEndpointEntity(GatusEntity):
    """Base class for entities that represent a single Gatus endpoint."""

    def __init__(
        self,
        coordinator: GatusDataUpdateCoordinator,
        endpoint_key: str,
        endpoint_name: str,
        endpoint_group: str,
    ) -> None:
        """Initialize the endpoint entity."""
        super().__init__(coordinator)
        self._endpoint_key = endpoint_key
        self._endpoint_name = endpoint_name
        self._endpoint_group = endpoint_group

    @property
    def _endpoint_label(self) -> str:
        """Return "<group> <name>", omitting the group for ungrouped endpoints."""
        return " ".join(
            part for part in (self._endpoint_group, self._endpoint_name) if part
        )

    def _get_endpoint(self) -> GatusEndpoint | None:
        """Return this endpoint's data from the coordinator index (O(1) lookup)."""
        if not self.coordinator.data or not isinstance(self.coordinator.data, dict):
            return None
        return self.coordinator.data.get(self._endpoint_key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        endpoint = self._get_endpoint()
        return endpoint is not None and endpoint.latest_result is not None


@callback
def async_track_endpoints(
    entry: GatusConfigEntry,
    async_add_entities: AddEntitiesCallback,
    entity_factory: Callable[
        [GatusDataUpdateCoordinator, GatusEndpoint], GatusEndpointEntity
    ],
) -> None:
    """
    Keep a platform's entities in sync with the endpoints Gatus reports.

    Endpoints that appear are added. Endpoints that disappear have their live
    entity removed, but the entity registry entry is kept on purpose: Gatus
    with in-memory storage reports no endpoints right after a restart, and
    deleting registry entries would throw away user customisations. The
    orphaned entry can be deleted from the UI, and is reused if the endpoint
    comes back.
    """
    coordinator = entry.runtime_data.coordinator
    entities: dict[str, GatusEndpointEntity] = {}

    @callback
    def _sync_endpoints() -> None:
        data = coordinator.data
        if not coordinator.last_update_success or not isinstance(data, dict):
            return

        new_entities: list[GatusEndpointEntity] = []
        for key, endpoint in data.items():
            if key not in entities:
                entities[key] = entity_factory(coordinator, endpoint)
                new_entities.append(entities[key])
        if new_entities:
            async_add_entities(new_entities)

        for key in entities.keys() - data.keys():
            entity = entities.pop(key)
            LOGGER.debug("Endpoint %s no longer reported by Gatus; removing", key)
            if entity.hass is not None:
                entity.hass.async_create_task(entity.async_remove())

    _sync_endpoints()
    entry.async_on_unload(coordinator.async_add_listener(_sync_endpoints))
