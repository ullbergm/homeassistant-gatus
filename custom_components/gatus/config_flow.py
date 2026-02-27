"""Adds config flow for Gatus."""

from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.helpers import selector
from slugify import slugify

from .api import (
    GatusApiClient,
    GatusApiClientAuthenticationError,
    GatusApiClientCommunicationError,
    GatusApiClientError,
)
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER

if TYPE_CHECKING:
    from .data import GatusConfigEntry


class GatusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Gatus."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: GatusConfigEntry,  # noqa: ARG004
    ) -> GatusOptionsFlowHandler:
        """Return the options flow handler."""
        return GatusOptionsFlowHandler()

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip()
            if not url.startswith(("http://", "https://")):
                _errors["base"] = "invalid_url"
            else:
                user_input = {**user_input, CONF_URL: url}
            if not _errors:
                try:
                    await self._test_credentials(
                        url=url,
                    )
                except GatusApiClientAuthenticationError as exception:
                    LOGGER.warning(exception)
                    _errors["base"] = "auth"
                except GatusApiClientCommunicationError as exception:
                    LOGGER.error(exception)
                    _errors["base"] = "connection"
                except GatusApiClientError as exception:
                    LOGGER.exception(exception)
                    _errors["base"] = "unknown"
                else:
                    # Slugified URL is stable as long as the user doesn't change
                    # the Gatus server URL, which would be a reconfiguration anyway.
                    await self.async_set_unique_id(slugify(url))
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=url,
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, url: str) -> None:
        """Validate credentials."""
        # Create connector with threaded resolver to avoid aiodns issues
        # with Python 3.13
        connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
        session = aiohttp.ClientSession(connector=connector)
        try:
            client = GatusApiClient(
                url=url,
                session=session,
            )
            await client.async_get_data()
        finally:
            await session.close()


class GatusOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Gatus options."""

    async def async_step_init(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the options flow."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=int(current_interval),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=10,
                            max=3600,
                            step=10,
                            unit_of_measurement="seconds",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
