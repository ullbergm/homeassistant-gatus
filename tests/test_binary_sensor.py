"""Tests for the Gatus binary sensor platform."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.gatus.binary_sensor import GatusEndpointBinarySensor

from .conftest import MOCK_ENDPOINT_DATA, MOCK_URL


def _make_coordinator(data: list | None = None, success: bool = True) -> MagicMock:
    """Build a minimal mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = success
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.data = {"url": MOCK_URL}
    # runtime_data.integration is accessed in entity.py for sw_version
    coordinator.config_entry.runtime_data.integration.version = "1.0.0"
    return coordinator


def _make_sensor(
    coordinator: MagicMock,
    key: str = "external_google",
    name: str = "google",
    group: str = "external",
) -> GatusEndpointBinarySensor:
    """Instantiate a sensor with a minimal coordinator mock."""
    return GatusEndpointBinarySensor(
        coordinator=coordinator,
        endpoint_key=key,
        endpoint_name=name,
        endpoint_group=group,
    )


class TestGatusEndpointBinarySensorIsOn:
    """Tests for the is_on property."""

    def test_is_on_false_when_success_true(self) -> None:
        """Sensor reports 'off' (no problem) when latest result is successful."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA)
        sensor = _make_sensor(coordinator)
        assert sensor.is_on is False

    def test_is_on_true_when_success_false(self) -> None:
        """Sensor reports 'on' (problem) when latest result is failing."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA)
        sensor = _make_sensor(coordinator, key="media_plex", name="plex", group="media")
        assert sensor.is_on is True

    def test_is_on_true_when_no_data(self) -> None:
        """Sensor reports 'on' when coordinator has no data."""
        coordinator = _make_coordinator(data=None)
        sensor = _make_sensor(coordinator)
        assert sensor.is_on is True

    def test_is_on_true_when_endpoint_not_found(self) -> None:
        """Sensor reports 'on' when its key is missing from coordinator data."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA)
        sensor = _make_sensor(coordinator, key="nonexistent_key")
        assert sensor.is_on is True

    def test_is_on_true_when_no_results(self) -> None:
        """Sensor reports 'on' when the endpoint exists but has no results."""
        data = [
            {"key": "empty_endpoint", "name": "empty", "group": "test", "results": []}
        ]
        coordinator = _make_coordinator(data=data)
        sensor = _make_sensor(
            coordinator, key="empty_endpoint", name="empty", group="test"
        )
        assert sensor.is_on is True


class TestGatusEndpointBinarySensorAvailable:
    """Tests for the available property."""

    def test_available_when_coordinator_success_and_data_present(self) -> None:
        """Sensor is available when coordinator succeeds and endpoint has results."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA, success=True)
        sensor = _make_sensor(coordinator)
        assert sensor.available is True

    def test_unavailable_when_coordinator_failed(self) -> None:
        """Sensor is unavailable when last_update_success is False."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA, success=False)
        sensor = _make_sensor(coordinator)
        assert sensor.available is False

    def test_unavailable_when_endpoint_missing(self) -> None:
        """Sensor is unavailable when its key is not in coordinator data."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA, success=True)
        sensor = _make_sensor(coordinator, key="gone_endpoint")
        assert sensor.available is False

    def test_unavailable_when_no_results(self) -> None:
        """Sensor is unavailable when the endpoint has an empty results list."""
        data = [{"key": "no_results", "name": "x", "group": "y", "results": []}]
        coordinator = _make_coordinator(data=data, success=True)
        sensor = _make_sensor(coordinator, key="no_results", name="x", group="y")
        assert sensor.available is False


class TestGatusEndpointBinarySensorAttributes:
    """Tests for extra_state_attributes."""

    def test_attributes_populated_from_latest_result(self) -> None:
        """Attributes reflect the latest result in coordinator data."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA)
        sensor = _make_sensor(coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["endpoint_group"] == "external"
        assert attrs["endpoint_name"] == "google"
        assert attrs["hostname"] == "google.com"
        assert attrs["status_code"] == 200
        assert attrs["duration_ms"] == pytest.approx(50.0)
        assert attrs["timestamp"] == "2026-01-01T00:00:00Z"

    def test_empty_attributes_when_no_data(self) -> None:
        """Attributes are empty when coordinator data is absent."""
        coordinator = _make_coordinator(data=None)
        sensor = _make_sensor(coordinator)
        assert sensor.extra_state_attributes == {}

    def test_empty_attributes_when_no_results(self) -> None:
        """Attributes are empty when the endpoint has no results."""
        data = [{"key": "k", "name": "n", "group": "g", "results": []}]
        coordinator = _make_coordinator(data=data)
        sensor = _make_sensor(coordinator, key="k", name="n", group="g")
        assert sensor.extra_state_attributes == {}


class TestGatusEndpointBinarySensorUniqueId:
    """Tests for unique_id generation."""

    def test_unique_id_combines_entry_id_and_key(self) -> None:
        """Unique ID is entry_id + endpoint key."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA)
        sensor = _make_sensor(coordinator, key="my_endpoint")
        assert sensor.unique_id == "test_entry_id_my_endpoint"

    def test_name_combines_group_and_name(self) -> None:
        """Entity name is '{group} {name}'."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA)
        sensor = _make_sensor(coordinator, name="plex", group="media")
        assert sensor.name == "media plex"


class TestGatusEntityDeviceInfo:
    """Tests for base entity device info metadata."""

    def test_sw_version_is_stringified(self) -> None:
        """Integration version objects are normalized to a string."""

        class VersionObject:
            def __str__(self) -> str:
                return "1.2.3"

        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA)
        coordinator.config_entry.runtime_data.integration.version = VersionObject()

        sensor = _make_sensor(coordinator)

        assert sensor.device_info["sw_version"] == "1.2.3"

    def test_invalid_sw_version_is_omitted(self) -> None:
        """Invalid integration versions are not exposed as sw_version."""
        coordinator = _make_coordinator(data=MOCK_ENDPOINT_DATA)
        coordinator.config_entry.runtime_data.integration.version = "main"

        sensor = _make_sensor(coordinator)

        assert sensor.device_info.get("sw_version") is None
