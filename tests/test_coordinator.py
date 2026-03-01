"""Tests for the Gatus DataUpdateCoordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.gatus.api import (
    GatusApiClientAuthenticationError,
    GatusApiClientError,
)
from custom_components.gatus.coordinator import GatusDataUpdateCoordinator

from .conftest import MOCK_ENDPOINT_DATA


def _make_coordinator(client: MagicMock) -> GatusDataUpdateCoordinator:
    """Build a coordinator with a fake hass and injected client mock."""
    hass = MagicMock()
    hass.loop = MagicMock()

    coordinator = GatusDataUpdateCoordinator.__new__(GatusDataUpdateCoordinator)
    # Manually initialise the parts we need without a real HA event loop
    coordinator.logger = MagicMock()
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.runtime_data.client = client
    coordinator._listeners = {}
    coordinator.last_update_success = True
    coordinator.last_exception = None
    coordinator.data = None
    return coordinator


class TestGatusDataUpdateCoordinator:
    """Tests for GatusDataUpdateCoordinator._async_update_data."""

    async def test_successful_update_returns_data(self) -> None:
        """Coordinator returns endpoint list on success."""
        client = MagicMock()
        client.async_get_data = AsyncMock(return_value=MOCK_ENDPOINT_DATA)

        coordinator = _make_coordinator(client)
        result = await coordinator._async_update_data()
        assert result == MOCK_ENDPOINT_DATA

    async def test_auth_error_raises_config_entry_auth_failed(self) -> None:
        """Authentication error is re-raised as ConfigEntryAuthFailed."""
        client = MagicMock()
        client.async_get_data = AsyncMock(
            side_effect=GatusApiClientAuthenticationError("bad creds")
        )

        coordinator = _make_coordinator(client)
        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    async def test_api_error_raises_update_failed(self) -> None:
        """Generic API error is re-raised as UpdateFailed."""
        client = MagicMock()
        client.async_get_data = AsyncMock(
            side_effect=GatusApiClientError("connection failed")
        )

        coordinator = _make_coordinator(client)
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_unexpected_data_format_is_returned(self) -> None:
        """Non-list responses are returned as-is (coordinator logs a warning)."""
        client = MagicMock()
        client.async_get_data = AsyncMock(return_value={"unexpected": "dict"})

        coordinator = _make_coordinator(client)
        result = await coordinator._async_update_data()
        assert result == {"unexpected": "dict"}
