"""Tests for endpoint tracking and the response time sensor."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.gatus.entity import async_track_endpoints
from custom_components.gatus.models import GatusEndpoint
from custom_components.gatus.sensor import GatusEndpointResponseTimeSensor

from .conftest import MOCK_ENDPOINT_DATA, MOCK_URL


def _endpoints(*keys: str) -> dict[str, GatusEndpoint]:
    all_endpoints = {d["key"]: GatusEndpoint.from_dict(d) for d in MOCK_ENDPOINT_DATA}
    return {key: all_endpoints[key] for key in keys}


def _make_entry(data: dict[str, GatusEndpoint]) -> MagicMock:
    entry = MagicMock()
    coordinator = entry.runtime_data.coordinator
    coordinator.data = data
    coordinator.last_update_success = True
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.data = {"url": MOCK_URL}
    return entry


def _factory(_coordinator, endpoint: GatusEndpoint) -> MagicMock:
    entity = MagicMock()
    entity.key = endpoint.key
    return entity


def _listener(entry: MagicMock):
    return entry.runtime_data.coordinator.async_add_listener.call_args.args[0]


class TestAsyncTrackEndpoints:
    """Tests for async_track_endpoints."""

    def test_adds_initial_endpoints_and_registers_listener(self) -> None:
        entry = _make_entry(_endpoints("external_google", "media_plex"))
        add_entities = MagicMock()

        async_track_endpoints(entry, add_entities, _factory)

        added = add_entities.call_args.args[0]
        assert [e.key for e in added] == ["external_google", "media_plex"]
        entry.async_on_unload.assert_called_once()

    def test_adds_only_new_endpoints_on_update(self) -> None:
        entry = _make_entry(_endpoints("external_google"))
        add_entities = MagicMock()
        async_track_endpoints(entry, add_entities, _factory)

        entry.runtime_data.coordinator.data = _endpoints(
            "external_google", "media_plex"
        )
        _listener(entry)()

        assert add_entities.call_count == 2
        assert [e.key for e in add_entities.call_args.args[0]] == ["media_plex"]

    def test_removes_entity_when_endpoint_disappears(self) -> None:
        entry = _make_entry(_endpoints("external_google", "media_plex"))
        add_entities = MagicMock()
        async_track_endpoints(entry, add_entities, _factory)
        plex = add_entities.call_args.args[0][1]

        entry.runtime_data.coordinator.data = _endpoints("external_google")
        _listener(entry)()

        plex.async_remove.assert_called_once()
        plex.hass.async_create_task.assert_called_once()

    def test_endpoint_is_re_added_after_returning(self) -> None:
        entry = _make_entry(_endpoints("external_google", "media_plex"))
        add_entities = MagicMock()
        async_track_endpoints(entry, add_entities, _factory)

        entry.runtime_data.coordinator.data = _endpoints("external_google")
        _listener(entry)()
        entry.runtime_data.coordinator.data = _endpoints(
            "external_google", "media_plex"
        )
        _listener(entry)()

        assert [e.key for e in add_entities.call_args.args[0]] == ["media_plex"]

    def test_failed_update_does_not_remove_entities(self) -> None:
        entry = _make_entry(_endpoints("external_google"))
        add_entities = MagicMock()
        async_track_endpoints(entry, add_entities, _factory)
        google = add_entities.call_args.args[0][0]

        entry.runtime_data.coordinator.last_update_success = False
        entry.runtime_data.coordinator.data = {}
        _listener(entry)()

        google.async_remove.assert_not_called()


class TestGatusEndpointResponseTimeSensor:
    """Tests for the response time sensor."""

    def _sensor(
        self, data: dict[str, GatusEndpoint], group: str = "external"
    ) -> GatusEndpointResponseTimeSensor:
        return GatusEndpointResponseTimeSensor(
            coordinator=_make_entry(data).runtime_data.coordinator,
            endpoint_key="external_google",
            endpoint_name="google",
            endpoint_group=group,
        )

    def test_native_value_is_latest_duration_in_ms(self) -> None:
        assert self._sensor(_endpoints("external_google")).native_value == 50.0

    def test_native_value_none_when_endpoint_missing(self) -> None:
        assert self._sensor({}).native_value is None

    def test_identity(self) -> None:
        sensor = self._sensor(_endpoints("external_google"))
        assert sensor.unique_id == "test_entry_id_external_google_response_time"
        assert sensor.name == "external google response time"
        assert sensor.entity_registry_enabled_default is False

    def test_name_omits_empty_group(self) -> None:
        sensor = self._sensor(_endpoints("external_google"), group="")
        assert sensor.name == "google response time"
