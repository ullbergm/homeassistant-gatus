"""Shared fixtures for Gatus integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

MOCK_URL = "http://gatus.example.com"

MOCK_ENDPOINT_DATA = [
    {
        "key": "external_google",
        "name": "google",
        "group": "external",
        "results": [
            {
                "success": True,
                "hostname": "google.com",
                "status": 200,
                "duration": 50_000_000,  # 50 ms in nanoseconds
                "timestamp": "2026-01-01T00:00:00Z",
            }
        ],
    },
    {
        "key": "media_plex",
        "name": "plex",
        "group": "media",
        "results": [
            {
                "success": False,
                "hostname": "plex.example.com",
                "status": 503,
                "duration": 100_000_000,  # 100 ms in nanoseconds
                "timestamp": "2026-01-01T00:01:00Z",
            }
        ],
    },
]


@pytest.fixture
def mock_endpoint_data() -> list[dict]:
    """Return mock Gatus endpoint data."""
    return MOCK_ENDPOINT_DATA.copy()


@pytest.fixture
def mock_api_client(mock_endpoint_data: list[dict]) -> MagicMock:
    """Return a mock GatusApiClient."""
    client = MagicMock()
    client.async_get_data = AsyncMock(return_value=mock_endpoint_data)
    return client
