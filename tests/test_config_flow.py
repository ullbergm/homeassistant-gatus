"""Tests for the Gatus config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

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

        with (
            patch("custom_components.gatus.config_flow.aiohttp.TCPConnector"),
            patch(
                "custom_components.gatus.config_flow.aiohttp.ClientSession"
            ) as mock_session_cls,
            patch(
                "custom_components.gatus.config_flow.GatusApiClient",
                return_value=mock_client,
            ),
        ):
            mock_session = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session_cls.return_value = mock_session

            flow = GatusFlowHandler()
            # Should not raise
            await flow._test_credentials(url=MOCK_URL)
            mock_client.async_get_data.assert_called_once()

    async def test_test_credentials_propagates_auth_error(self) -> None:
        """_test_credentials propagates GatusApiClientAuthenticationError."""
        mock_client = MagicMock()
        mock_client.async_get_data = AsyncMock(
            side_effect=GatusApiClientAuthenticationError("bad creds")
        )

        with (
            patch("custom_components.gatus.config_flow.aiohttp.TCPConnector"),
            patch(
                "custom_components.gatus.config_flow.aiohttp.ClientSession"
            ) as mock_session_cls,
            patch(
                "custom_components.gatus.config_flow.GatusApiClient",
                return_value=mock_client,
            ),
        ):
            mock_session = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session_cls.return_value = mock_session

            flow = GatusFlowHandler()
            with pytest.raises(GatusApiClientAuthenticationError):
                await flow._test_credentials(url=MOCK_URL)

    async def test_test_credentials_propagates_communication_error(self) -> None:
        """_test_credentials propagates GatusApiClientCommunicationError."""
        mock_client = MagicMock()
        mock_client.async_get_data = AsyncMock(
            side_effect=GatusApiClientCommunicationError("timeout")
        )

        with (
            patch("custom_components.gatus.config_flow.aiohttp.TCPConnector"),
            patch(
                "custom_components.gatus.config_flow.aiohttp.ClientSession"
            ) as mock_session_cls,
            patch(
                "custom_components.gatus.config_flow.GatusApiClient",
                return_value=mock_client,
            ),
        ):
            mock_session = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session_cls.return_value = mock_session

            flow = GatusFlowHandler()
            with pytest.raises(GatusApiClientCommunicationError):
                await flow._test_credentials(url=MOCK_URL)


class TestGatusOptionsFlowHandler:
    """Tests for GatusOptionsFlowHandler."""

    async def test_init_creates_entry_with_user_input(self) -> None:
        """Options flow creates an entry when user provides valid input."""
        mock_entry = MagicMock()
        mock_entry.options = {}

        flow = GatusOptionsFlowHandler()
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        with patch.object(
            type(flow),
            "config_entry",
            new_callable=PropertyMock,
            return_value=mock_entry,
        ):
            user_input = {CONF_SCAN_INTERVAL: 120}
            await flow.async_step_init(user_input=user_input)
            flow.async_create_entry.assert_called_once_with(data=user_input)

    async def test_init_shows_form_when_no_input(self) -> None:
        """Options flow shows form when no user input is provided."""
        mock_entry = MagicMock()
        mock_entry.options = {CONF_SCAN_INTERVAL: 60}

        flow = GatusOptionsFlowHandler()
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        with patch.object(
            type(flow),
            "config_entry",
            new_callable=PropertyMock,
            return_value=mock_entry,
        ):
            await flow.async_step_init(user_input=None)
            flow.async_show_form.assert_called_once()
            call_kwargs = flow.async_show_form.call_args.kwargs
            assert call_kwargs["step_id"] == "init"

    def test_default_scan_interval_constant(self) -> None:
        """DEFAULT_SCAN_INTERVAL is 60 seconds."""
        assert DEFAULT_SCAN_INTERVAL == 60
