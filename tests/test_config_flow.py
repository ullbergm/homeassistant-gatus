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

    async def test_migration_logs_old_and_new_unique_id(self) -> None:
        """The log line reports the pre-migration unique_id, not the new one."""
        mock_entry = MagicMock()
        mock_entry.version = 1
        mock_entry.unique_id = "http-gatus-example-com"
        mock_entry.data = {CONF_URL: MOCK_URL}

        def _fake_update(entry, *, unique_id=None, **__):
            entry.unique_id = unique_id

        hass = MagicMock()
        hass.config_entries.async_update_entry.side_effect = _fake_update

        with patch("custom_components.gatus.LOGGER") as mock_logger:
            await async_migrate_entry(hass, mock_entry)

        assert mock_logger.info.call_args.args[1:] == (
            "http-gatus-example-com",
            "http_gatus_example_com",
        )

    async def test_unknown_version_returns_false(self) -> None:
        """Migration fails gracefully for unrecognised entry versions."""
        mock_entry = MagicMock()
        mock_entry.version = 99
        mock_entry.data = {CONF_URL: MOCK_URL}

        hass = MagicMock()

        result = await async_migrate_entry(hass, mock_entry)

        assert result is False
        hass.config_entries.async_update_entry.assert_not_called()


class TestGatusFlowHandlerUserStep:
    """Tests for GatusFlowHandler.async_step_user."""

    async def _run(self, url: str) -> dict[str, MagicMock]:
        flow = GatusFlowHandler()
        mocks: dict[str, MagicMock] = {
            "async_set_unique_id": AsyncMock(),
            "_abort_if_unique_id_configured": MagicMock(),
            "_test_credentials": AsyncMock(),
            "async_create_entry": MagicMock(return_value={"type": "create_entry"}),
            "async_show_form": MagicMock(return_value={"type": "form"}),
        }
        with patch.multiple(flow, **mocks):
            await flow.async_step_user({CONF_URL: url})
        return mocks

    async def test_trailing_slash_is_normalised(self) -> None:
        """A trailing slash does not produce a different unique_id or entry."""
        mocks = await self._run(f"  {MOCK_URL}/ ")

        mocks["async_set_unique_id"].assert_awaited_once_with("http_gatus_example_com")
        mocks["async_create_entry"].assert_called_once_with(
            title=MOCK_URL, data={CONF_URL: MOCK_URL}
        )

    async def test_url_without_scheme_is_rejected(self) -> None:
        """URLs without http(s) scheme show the invalid_url error."""
        mocks = await self._run("gatus.example.com")

        mocks["async_create_entry"].assert_not_called()
        kwargs = mocks["async_show_form"].call_args.kwargs
        assert kwargs["errors"] == {"base": "invalid_url"}
        # The rejected value is offered back instead of an empty field.
        marker = next(iter(kwargs["data_schema"].schema))
        assert marker.description == {"suggested_value": "gatus.example.com"}


class TestGatusFlowHandlerReconfigureStep:
    """Tests for GatusFlowHandler.async_step_reconfigure."""

    async def _run(
        self, user_input: dict | None, other_unique_id: str | None = None
    ) -> dict[str, MagicMock]:
        entry = MagicMock()
        entry.entry_id = "entry_1"
        entry.unique_id = "http_gatus_example_com"
        entry.data = {CONF_URL: MOCK_URL}
        entries = [entry]
        if other_unique_id:
            other = MagicMock()
            other.entry_id = "entry_2"
            other.unique_id = other_unique_id
            entries.append(other)

        flow = GatusFlowHandler()
        flow.hass = MagicMock()
        mocks: dict[str, MagicMock] = {
            "_get_reconfigure_entry": MagicMock(return_value=entry),
            "_async_current_entries": MagicMock(return_value=entries),
            "_test_credentials": AsyncMock(),
            "async_abort": MagicMock(return_value={"type": "abort"}),
            "async_show_form": MagicMock(return_value={"type": "form"}),
        }
        with patch.multiple(flow, **mocks):
            await flow.async_step_reconfigure(user_input)
        mocks["entry"] = entry
        mocks["update_entry"] = flow.hass.config_entries.async_update_entry
        return mocks

    async def test_shows_form_prefilled_with_current_url(self) -> None:
        mocks = await self._run(None)

        kwargs = mocks["async_show_form"].call_args.kwargs
        assert kwargs["step_id"] == "reconfigure"
        marker = next(iter(kwargs["data_schema"].schema))
        assert marker.description == {"suggested_value": MOCK_URL}

    async def test_updates_url_unique_id_and_title(self) -> None:
        mocks = await self._run({CONF_URL: "https://new.example.com/"})

        mocks["_test_credentials"].assert_awaited_once_with(
            url="https://new.example.com"
        )
        mocks["update_entry"].assert_called_once_with(
            mocks["entry"],
            unique_id="https_new_example_com",
            title="https://new.example.com",
            data={CONF_URL: "https://new.example.com"},
        )
        mocks["async_abort"].assert_called_once_with(reason="reconfigure_successful")

    async def test_unchanged_url_is_accepted(self) -> None:
        mocks = await self._run({CONF_URL: MOCK_URL})

        mocks["update_entry"].assert_called_once()
        mocks["async_abort"].assert_called_once_with(reason="reconfigure_successful")

    async def test_url_of_another_entry_aborts(self) -> None:
        mocks = await self._run(
            {CONF_URL: "https://new.example.com"},
            other_unique_id="https_new_example_com",
        )

        mocks["async_abort"].assert_called_once_with(reason="already_configured")
        mocks["update_entry"].assert_not_called()

    async def test_connection_error_shows_form_again(self) -> None:
        flow = GatusFlowHandler()
        flow.hass = MagicMock()
        entry = MagicMock()
        entry.data = {CONF_URL: MOCK_URL}
        mocks: dict[str, MagicMock] = {
            "_get_reconfigure_entry": MagicMock(return_value=entry),
            "_test_credentials": AsyncMock(
                side_effect=GatusApiClientCommunicationError("down")
            ),
            "async_show_form": MagicMock(return_value={"type": "form"}),
        }
        with patch.multiple(flow, **mocks):
            await flow.async_step_reconfigure({CONF_URL: "https://new.example.com"})

        flow.hass.config_entries.async_update_entry.assert_not_called()
        assert mocks["async_show_form"].call_args.kwargs["errors"] == {
            "base": "connection"
        }
