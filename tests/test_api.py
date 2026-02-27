"""Tests for the Gatus API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.gatus.api import (
    GatusApiClient,
    GatusApiClientAuthenticationError,
    GatusApiClientCommunicationError,
    GatusApiClientError,
    _verify_response_or_raise,
)


@pytest.fixture
def mock_session() -> MagicMock:
    """Return a mock aiohttp.ClientSession."""
    return MagicMock(spec=aiohttp.ClientSession)


def _make_mock_response(status: int, payload: object = None) -> MagicMock:
    """Build a mock aiohttp response."""
    response = MagicMock()
    response.status = status
    response.json = AsyncMock(return_value=payload or [])
    response.raise_for_status = MagicMock()
    return response


class TestVerifyResponseOrRaise:
    """Tests for _verify_response_or_raise."""

    def test_401_raises_auth_error(self) -> None:
        """Test that 401 raises GatusApiClientAuthenticationError."""
        response = MagicMock()
        response.status = 401
        with pytest.raises(GatusApiClientAuthenticationError):
            _verify_response_or_raise(response)

    def test_403_raises_auth_error(self) -> None:
        """Test that 403 raises GatusApiClientAuthenticationError."""
        response = MagicMock()
        response.status = 403
        with pytest.raises(GatusApiClientAuthenticationError):
            _verify_response_or_raise(response)

    def test_200_calls_raise_for_status(self) -> None:
        """Test that a 200 response calls raise_for_status."""
        response = MagicMock()
        response.status = 200
        _verify_response_or_raise(response)
        response.raise_for_status.assert_called_once()

    def test_500_calls_raise_for_status(self) -> None:
        """Test that a 500 response calls raise_for_status (propagates error)."""
        response = MagicMock()
        response.status = 500
        response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=()
        )
        with pytest.raises(aiohttp.ClientResponseError):
            _verify_response_or_raise(response)


class TestGatusApiClient:
    """Tests for GatusApiClient."""

    async def test_async_get_data_success(self, mock_session: MagicMock) -> None:
        """Test successful endpoint status retrieval."""
        payload = [{"key": "external_google", "name": "google"}]
        mock_session.request = AsyncMock(return_value=_make_mock_response(200, payload))

        client = GatusApiClient(url="http://localhost:8080", session=mock_session)
        result = await client.async_get_data()
        assert result == payload
        mock_session.request.assert_called_once_with(
            method="get",
            url="http://localhost:8080/api/v1/endpoints/statuses",
            headers=None,
            json=None,
        )

    async def test_url_trailing_slash_stripped(self, mock_session: MagicMock) -> None:
        """Test that a trailing slash in the URL is stripped."""
        mock_session.request = AsyncMock(return_value=_make_mock_response(200, []))

        client = GatusApiClient(url="http://localhost:8080/", session=mock_session)
        await client.async_get_data()
        _, kwargs = mock_session.request.call_args
        assert kwargs["url"] == "http://localhost:8080/api/v1/endpoints/statuses"

    async def test_authentication_error(self, mock_session: MagicMock) -> None:
        """Test that 401 response raises GatusApiClientAuthenticationError."""
        mock_session.request = AsyncMock(return_value=_make_mock_response(401))

        client = GatusApiClient(url="http://localhost:8080", session=mock_session)
        with pytest.raises(GatusApiClientAuthenticationError):
            await client.async_get_data()

    async def test_timeout_raises_communication_error(
        self, mock_session: MagicMock
    ) -> None:
        """Test that a timeout raises GatusApiClientCommunicationError."""
        mock_session.request = AsyncMock(side_effect=TimeoutError)

        client = GatusApiClient(url="http://localhost:8080", session=mock_session)
        with pytest.raises(GatusApiClientCommunicationError, match="Timeout"):
            await client.async_get_data()

    async def test_connection_error_raises_communication_error(
        self, mock_session: MagicMock
    ) -> None:
        """Test that a connection error raises GatusApiClientCommunicationError."""
        mock_session.request = AsyncMock(
            side_effect=aiohttp.ClientError("connection refused")
        )

        client = GatusApiClient(url="http://localhost:8080", session=mock_session)
        with pytest.raises(GatusApiClientCommunicationError, match="Error fetching"):
            await client.async_get_data()

    async def test_unexpected_exception_raises_api_error(
        self, mock_session: MagicMock
    ) -> None:
        """Test that an unexpected exception raises GatusApiClientError."""
        mock_session.request = AsyncMock(side_effect=ValueError("unexpected"))

        client = GatusApiClient(url="http://localhost:8080", session=mock_session)
        with pytest.raises(GatusApiClientError, match="Something really wrong"):
            await client.async_get_data()
