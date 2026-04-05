"""Tests for the Gatus config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from homeassistant.const import CONF_URL

from custom_components.gatus import async_migrate_entry
from custom_components.gatus.api import (
    GatusApiClientAuthenticationError,
    GatusApiClientCommunicationError,
)
from custom_components.gatus.config_flow import (
    GatusFlowHandler,
    GatusOptionsFlowHandler,
)
from custom_components.gatus.const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

from .conftest import MOCK_ENDPOINT_DATA, MOCK_URL


class TestGatusFlowHandlerTestCredentials:
    """Tests for GatusFlowHandler._test_credentials."""

    async def test_test_credentials_success(self) -> None:
        """_test_credentials succeeds when the API returns data."""
        mock_client = MagicMock()
        mock_client.async_get_data = AsyncMock(return_value=MOCK_ENDPOINT_DATA)
        mock_session = MagicMock()

        with (
            patch(
                "custom_components.gatus.config_flow.async_get_clientsession",
                return_value=mock_session,
            ),
            patch(
                "custom_components.gatus.config_flow.GatusApiClient",
                return_value=mock_client,
            ),
        ):
            flow = GatusFlowHandler()
            flow.hass = MagicMock()
            # Should not raise
            await flow._test_credentials(url=MOCK_URL)
            mock_client.async_get_data.assert_called_once()

    async def test_test_credentials_propagates_auth_error(self) -> None:
        """_test_credentials propagates GatusApiClientAuthenticationError."""
        mock_client = MagicMock()
        mock_client.async_get_data = AsyncMock(
            side_effect=GatusApiClientAuthenticationError("bad creds")
        )
        mock_session = MagicMock()

        with (
            patch(
                "custom_components.gatus.config_flow.async_get_clientsession",
                return_value=mock_session,
            ),
            patch(
                "custom_components.gatus.config_flow.GatusApiClient",
                return_value=mock_client,
            ),
        ):
            flow = GatusFlowHandler()
            flow.hass = MagicMock()
            with pytest.raises(GatusApiClientAuthenticationError):
                await flow._test_credentials(url=MOCK_URL)

    async def test_test_credentials_propagates_communication_error(self) -> None:
        """_test_credentials propagates GatusApiClientCommunicationError."""
        mock_client = MagicMock()
        mock_client.async_get_data = AsyncMock(
            side_effect=GatusApiClientCommunicationError("timeout")
        )
        mock_session = MagicMock()

        with (
            patch(
                "custom_components.gatus.config_flow.async_get_clientsession",
                return_value=mock_session,
            ),
            patch(
                "custom_components.gatus.config_flow.GatusApiClient",
                return_value=mock_client,
            ),
        ):
            flow = GatusFlowHandler()
            flow.hass = MagicMock()
            with pytest.raises(GatusApiClientCommunicationError):
                await flow._test_credentials(url=MOCK_URL)


class TestGatusOptionsFlowHandler:
    """Tests for GatusOptionsFlowHandler."""

    async def test_init_creates_entry_with_user_input(self) -> None:
        """Options flow creates an entry when user provides valid input."""
        mock_entry = MagicMock()
        mock_entry.options = {}

        flow = GatusOptionsFlowHandler()

        with (
            patch.object(
                type(flow),
                "config_entry",
                new_callable=PropertyMock,
                return_value=mock_entry,
            ),
            patch.object(
                flow,
                "async_create_entry",
                return_value={"type": "create_entry"},
            ) as mock_create_entry,
        ):
            user_input = {CONF_SCAN_INTERVAL: 120}
            await flow.async_step_init(user_input=user_input)
            mock_create_entry.assert_called_once_with(data=user_input)

    async def test_init_shows_form_when_no_input(self) -> None:
        """Options flow shows form when no user input is provided."""
        mock_entry = MagicMock()
        mock_entry.options = {CONF_SCAN_INTERVAL: 60}

        flow = GatusOptionsFlowHandler()

        with (
            patch.object(
                type(flow),
                "config_entry",
                new_callable=PropertyMock,
                return_value=mock_entry,
            ),
            patch.object(
                flow,
                "async_show_form",
                return_value={"type": "form"},
            ) as mock_show_form,
        ):
            await flow.async_step_init(user_input=None)
            mock_show_form.assert_called_once()
            call_kwargs = mock_show_form.call_args.kwargs
            assert call_kwargs["step_id"] == "init"

    def test_default_scan_interval_constant(self) -> None:
        """DEFAULT_SCAN_INTERVAL is 60 seconds."""
        assert DEFAULT_SCAN_INTERVAL == 60


class TestGatusFlowHandlerVersion:
    """Tests for GatusFlowHandler version."""

    def test_config_flow_version_is_2(self) -> None:
        """Config flow VERSION must be 2 after slugify migration."""
        assert GatusFlowHandler.VERSION == 2


class TestAsyncMigrateEntry:
    """Tests for async_migrate_entry."""

    async def test_v1_to_v2_rewrites_unique_id_with_underscores(self) -> None:
        """v1→v2 migration replaces hyphenated unique_id with underscore form."""
        old_unique_id = "http-gatus-example-com"
        url = MOCK_URL  # "http://gatus.example.com"

        mock_entry = MagicMock()
        mock_entry.version = 1
        mock_entry.unique_id = old_unique_id
        mock_entry.data = {CONF_URL: url}

        captured: dict = {}

        def _fake_update(_entry, *, unique_id=None, version=None, **__):
            captured["unique_id"] = unique_id
            captured["version"] = version

        hass = MagicMock()
        hass.config_entries.async_update_entry.side_effect = _fake_update

        result = await async_migrate_entry(hass, mock_entry)

        assert result is True
        assert captured["unique_id"] == "http_gatus_example_com"
        assert captured["version"] == 2

    async def test_unknown_version_returns_false(self) -> None:
        """Migration fails gracefully for unrecognised entry versions."""
        mock_entry = MagicMock()
        mock_entry.version = 99
        mock_entry.data = {CONF_URL: MOCK_URL}

        hass = MagicMock()

        result = await async_migrate_entry(hass, mock_entry)

        assert result is False
        hass.config_entries.async_update_entry.assert_not_called()
