"""Image platform for Gatus."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.image import (
    ImageDeviceClass,
    ImageEntity,
    BImageEntityDescription,
)

from .const import DOMAIN
from .coordinator import GatusDataUpdateCoordinator
from .entity import GatusEntity
from homeassistant.const import CONF_HOST
from homeassistant.components.image import ImageEntity, ImageEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

PARALLEL_UPDATES = 1

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    ) -> None:
    """Set up the Gatus platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        GatusImage(
            coordinator=coordinator,
            entity_description=ImageEntityDescription(
                key=endpoint["key"],
                name=endpoint["name"] + " 24h Uptime",
                icon="mdi:network-outline",
                # device_class=ImageClass.CONNECTIVITY,
            )
        )
        for endpoint in hass.data[DOMAIN][entry.entry_id].endpoints
    )


class GatusImage(GatusEntity, ImageEntity):
    """Gatus image class."""

    def __init__(
        self,
        coordinator: GatusDataUpdateCoordinator,
        entity_description: ImageEntityDescription,
    ) -> None:
        """Initialize the image class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_image_url = (
                    "https://"
                    + coordinator.config_entry.data[CONF_HOST]
                    + "/api/v1/endpoints/"
                    + x["key"]
                    + f"/uptimes/24h/badge.svg"
                )

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        # return self.coordinator.data.get("title", "") == "foo"
        for x in self.coordinator.endpoints:
            if self.entity_description.key == x["key"]:
                return x["results"][0]["success"]

        return {}
    

    # async def _async_load_image_from_url(self, url: str) -> Image | None:
    #     """Load an image by url."""
    #     if response := await self._fetch_url(url):
    #         return Image(
    #             content=response.content,
    #             content_type="image/svg",  # Actually returns binary/octet-stream
    #         )
    #     return None

    # @callback
    # def _handle_coordinator_update(self) -> None:
    #     """Handle updated data from the coordinator."""
    #     if (
    #         self.data["last_alarm_pic"]
    #         and self.data["last_alarm_pic"] != self._attr_image_url
    #     ):
    #         _LOGGER.debug("Image url changed to %s", self.data["last_alarm_pic"])

    #         self._attr_image_url = self.data["last_alarm_pic"]
    #         self._cached_image = None
    #         self._attr_image_last_updated = dt_util.parse_datetime(
    #             str(self.data["last_alarm_time"])
    #         )

    #     super()._handle_coordinator_update()
