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
from custom_components.gatus.models import GatusEndpoint

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
    coordinator.data = []
    return coordinator


class TestGatusDataUpdateCoordinator:
    """Tests for GatusDataUpdateCoordinator._async_update_data."""

    async def test_successful_update_returns_endpoint_dict(self) -> None:
        """Coordinator parses raw dicts and returns a dict-keyed GatusEndpoint index."""
        client = MagicMock()
        client.async_get_data = AsyncMock(return_value=MOCK_ENDPOINT_DATA)

        coordinator = _make_coordinator(client)
        result = await coordinator._async_update_data()

        assert isinstance(result, dict)
        assert len(result) == len(MOCK_ENDPOINT_DATA)
        assert all(isinstance(ep, GatusEndpoint) for ep in result.values())
        assert set(result.keys()) == {"external_google", "media_plex"}

    async def test_parsed_endpoint_matches_raw_data(self) -> None:
        """Parsed GatusEndpoint values match the source raw dict."""
        client = MagicMock()
        client.async_get_data = AsyncMock(return_value=MOCK_ENDPOINT_DATA)

        coordinator = _make_coordinator(client)
        result = await coordinator._async_update_data()

        first = result["external_google"]
        assert first.key == "external_google"
        assert first.name == "google"
        assert first.group == "external"
        assert len(first.results) == 1
        assert first.results[0].success is True
        assert first.results[0].hostname == "google.com"
        assert first.results[0].status_code == 200
        assert first.results[0].duration_ms == pytest.approx(50.0)

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

    async def test_unexpected_data_format_is_returned_as_is(self) -> None:
        """Non-list responses are returned as-is (coordinator logs a warning)."""
        client = MagicMock()
        client.async_get_data = AsyncMock(return_value={"unexpected": "dict"})

        coordinator = _make_coordinator(client)
        result = await coordinator._async_update_data()
        assert result == {"unexpected": "dict"}
