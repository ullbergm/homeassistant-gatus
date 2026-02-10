"""
Custom integration to integrate Gatus with Home Assistant.

For more details about this integration, please refer to
https://github.com/ullbergm/homeassistant-gatus
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.const import CONF_URL, Platform
from homeassistant.loader import async_get_loaded_integration

from .api import GatusApiClient
from .const import DOMAIN, LOGGER
from .coordinator import GatusDataUpdateCoordinator
from .data import GatusData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import GatusConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: GatusConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = GatusDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(minutes=1),
    )
    # Create connector with threaded resolver to avoid aiodns issues with Python 3.13
    connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
    session = aiohttp.ClientSession(connector=connector)
    entry.runtime_data = GatusData(
        client=GatusApiClient(
            url=entry.data[CONF_URL],
            session=session,
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: GatusConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    # Close the aiohttp session
    await entry.runtime_data.client.session.close()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: GatusConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
