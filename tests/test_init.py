"""Tests for integration setup and diagnostics."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_URL, Platform

from custom_components.gatus import PLATFORMS, async_setup_entry
from custom_components.gatus.const import CONF_SCAN_INTERVAL
from custom_components.gatus.diagnostics import async_get_config_entry_diagnostics

from .conftest import MOCK_ENDPOINTS_DICT, MOCK_URL


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    async def test_setup_wires_coordinator_with_shared_session(self) -> None:
        hass = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        entry = MagicMock()
        entry.data = {CONF_URL: MOCK_URL}
        entry.options = {CONF_SCAN_INTERVAL: 120}

        with (
            patch(
                "custom_components.gatus.GatusDataUpdateCoordinator"
            ) as coordinator_cls,
            patch("custom_components.gatus.async_get_clientsession") as get_session,
            patch("custom_components.gatus.async_get_loaded_integration"),
        ):
            coordinator_cls.return_value.async_config_entry_first_refresh = AsyncMock()
            assert await async_setup_entry(hass, entry) is True

        kwargs = coordinator_cls.call_args.kwargs
        # The entry is passed explicitly rather than via the ContextVar fallback.
        assert kwargs["config_entry"] is entry
        assert kwargs["update_interval"] == timedelta(seconds=120)
        # The shared HA session is reused, so reloads do not create new sessions.
        get_session.assert_called_once_with(hass)
        assert entry.runtime_data.client._session is get_session.return_value
        hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
            entry, PLATFORMS
        )

    def test_platforms(self) -> None:
        assert PLATFORMS == [Platform.BINARY_SENSOR, Platform.SENSOR]


class TestDiagnostics:
    """Tests for config entry diagnostics."""

    async def test_diagnostics_redacts_url_and_summarises_endpoints(self) -> None:
        entry = MagicMock()
        entry.as_dict.return_value = {"data": {CONF_URL: MOCK_URL}, "title": "x"}
        coordinator = entry.runtime_data.coordinator
        coordinator.data = MOCK_ENDPOINTS_DICT
        coordinator.last_update_success = True
        coordinator.last_exception = None

        result = await async_get_config_entry_diagnostics(MagicMock(), entry)

        assert result["config_entry"]["data"][CONF_URL] == "**REDACTED**"
        assert result["coordinator"] == {
            "last_update_success": True,
            "last_exception": None,
            "endpoint_count": 2,
        }
        plex = next(e for e in result["endpoints"] if e["key"] == "media_plex")
        assert plex["success"] is False
        assert plex["status_code"] == 503
        assert plex["duration_ms"] == 100.0
        assert plex["result_count"] == 1
