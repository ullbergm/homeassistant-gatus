"""DataUpdateCoordinator for gatus_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

    async def _async_update_data(self) -> GatusCoordinatorData:
        """
        Fetch endpoint statuses from the Gatus API.

        Returns the endpoints indexed by their Gatus key.
        """
        try:
            raw = await self.config_entry.runtime_data.client.async_get_data()
        except GatusApiClientAuthenticationError as exception:
            # The integration has no credentials to re-enter, so this is not a
            # ConfigEntryAuthFailed (which would start a reauth flow).
            msg = (
                "Gatus rejected the request (401/403); this integration only "
                f"supports instances that do not require authentication: {exception}"
            )
            raise UpdateFailed(msg) from exception
        except GatusApiClientError as exception:
            raise UpdateFailed(exception) from exception

        if not isinstance(raw, list):
            msg = f"Gatus API returned unexpected data format: {type(raw).__name__}"
            raise UpdateFailed(msg)

        endpoints = {
            endpoint.key: endpoint
            for item in raw
            if isinstance(item, dict)
            and (endpoint := GatusEndpoint.from_dict(item)).key
        }
        LOGGER.debug("Successfully fetched %d endpoints from Gatus", len(endpoints))
        return endpoints
