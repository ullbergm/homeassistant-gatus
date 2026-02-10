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

if TYPE_CHECKING:
    from .data import GatusConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class GatusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Gatus API."""

    config_entry: GatusConfigEntry

    async def _async_update_data(self) -> Any:
        """
        Update data via library.

        Fetches endpoint statuses from Gatus API.
        Returns a list of endpoints with their status information.
        """
        try:
            data = await self.config_entry.runtime_data.client.async_get_data()
            if data and isinstance(data, list):
                LOGGER.debug("Successfully fetched %d endpoints from Gatus", len(data))
            else:
                LOGGER.warning(
                    "Gatus API returned unexpected data format: %s", type(data)
                )
        except GatusApiClientAuthenticationError as exception:
            LOGGER.error("Authentication failed for Gatus API: %s", exception)
            raise ConfigEntryAuthFailed(exception) from exception
        except GatusApiClientError as exception:
            LOGGER.error("Error fetching data from Gatus API: %s", exception)
            raise UpdateFailed(exception) from exception
        else:
            return data
