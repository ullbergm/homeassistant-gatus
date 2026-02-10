"""Adds config flow for Gatus."""

from __future__ import annotations

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
from .const import DOMAIN, LOGGER


class GatusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Gatus."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    url=user_input[CONF_URL],
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
                await self.async_set_unique_id(
                    ## Do NOT use this in production code
                    ## The unique_id should never be something that can change
                    ## https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
                    unique_id=slugify(user_input[CONF_URL])
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_URL],
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
