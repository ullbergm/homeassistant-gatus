"""DataUpdateCoordinator for gatus_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    GatusApiClientAuthenticationError,
    GatusApiClientError,
)
from .const import LOGGER
from .models import GatusEndpoint

if TYPE_CHECKING:
    from .data import GatusConfigEntry

type GatusCoordinatorData = dict[str, GatusEndpoint]


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class GatusDataUpdateCoordinator(DataUpdateCoordinator[GatusCoordinatorData]):
    """Class to manage fetching data from the Gatus API."""

    config_entry: GatusConfigEntry

    async def _async_update_data(self) -> Any:
        """
        Update data via library.

        Fetches endpoint statuses from Gatus API.
        Returns a parsed list of GatusEndpoint objects.
        """
        try:
            raw = await self.config_entry.runtime_data.client.async_get_data()
            if raw and isinstance(raw, list):
                endpoints = {
                    ep.key: ep
                    for item in raw
                    if (ep := GatusEndpoint.from_dict(item)).key
                }
                LOGGER.debug(
                    "Successfully fetched %d endpoints from Gatus", len(endpoints)
                )
            else:
                LOGGER.warning(
                    "Gatus API returned unexpected data format: %s", type(raw)
                )
                return raw
        except GatusApiClientAuthenticationError as exception:
            LOGGER.error("Authentication failed for Gatus API: %s", exception)
            raise ConfigEntryAuthFailed(exception) from exception
        except GatusApiClientError as exception:
            LOGGER.error("Error fetching data from Gatus API: %s", exception)
            raise UpdateFailed(exception) from exception
        else:
            return endpoints  # dict[str, GatusEndpoint]
