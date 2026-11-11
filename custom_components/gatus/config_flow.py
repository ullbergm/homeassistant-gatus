"""Adds config flow for Gatus."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import slugify

from .api import (
    GatusApiClient,
    GatusApiClientAuthenticationError,
    GatusApiClientCommunicationError,
    GatusApiClientError,
)
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER

if TYPE_CHECKING:
    from .data import GatusConfigEntry


_URL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT,
            ),
        ),
    },
)


class GatusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Gatus."""

    VERSION = 2

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
        _errors: dict[str, str] = {}
        if user_input is not None:
            url, _errors = await self._async_validate_url(user_input[CONF_URL])
            if not _errors:
                # Slugified URL is stable as long as the user doesn't change
                # the Gatus server URL, which would be a reconfiguration anyway.
                await self.async_set_unique_id(slugify(url))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=url,
                    data={**user_input, CONF_URL: url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_URL_SCHEMA,
            errors=_errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Let the user point an existing entry at a new Gatus URL."""
        entry = self._get_reconfigure_entry()
        _errors: dict[str, str] = {}
        if user_input is not None:
            url, _errors = await self._async_validate_url(user_input[CONF_URL])
            if not _errors:
                unique_id = slugify(url)
                if any(
                    other.unique_id == unique_id and other.entry_id != entry.entry_id
                    for other in self._async_current_entries()
                ):
                    return self.async_abort(reason="already_configured")
                # Entities are keyed on the entry ID, so they (and any user
                # customisations) survive the URL change. The entry's update
                # listener reloads it, so async_update_reload_and_abort (which
                # would schedule a second reload) is deliberately not used.
                self.hass.config_entries.async_update_entry(
                    entry,
                    unique_id=unique_id,
                    title=url,
                    data={**entry.data, CONF_URL: url},
                )
                return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _URL_SCHEMA,
                user_input or {CONF_URL: entry.data.get(CONF_URL, "")},
            ),
            errors=_errors,
        )

    async def _async_validate_url(self, raw_url: str) -> tuple[str, dict[str, str]]:
        """Normalise the URL and check that Gatus answers on it."""
        # Drop trailing slashes so "http://host" and "http://host/" map to
        # the same unique_id and cannot be configured twice.
        url = raw_url.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            return url, {"base": "invalid_url"}
        try:
            await self._test_credentials(url=url)
        except GatusApiClientAuthenticationError as exception:
            LOGGER.warning(exception)
            return url, {"base": "auth"}
        except GatusApiClientCommunicationError as exception:
            LOGGER.error(exception)
            return url, {"base": "connection"}
        except GatusApiClientError as exception:
            LOGGER.exception(exception)
            return url, {"base": "unknown"}
        return url, {}

    async def _test_credentials(self, url: str) -> None:
        """Validate credentials."""
        session = async_get_clientsession(self.hass)
        client = GatusApiClient(url=url, session=session)
        await client.async_get_data()


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
