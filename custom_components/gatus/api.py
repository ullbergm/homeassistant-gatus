"""Gatus API Client."""

from __future__ import annotations

import asyncio
import socket
from typing import Any

import aiohttp


class GatusApiClientError(Exception):
    """Exception to indicate a general API error."""


class GatusApiClientCommunicationError(
    GatusApiClientError,
):
    """Exception to indicate a communication error."""


class GatusApiClientAuthenticationError(
    GatusApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise GatusApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class GatusApiClient:
    """Gatus API Client."""

    def __init__(
        self,
        url: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the Gatus API Client."""
        self._url = url
        self.session = session

    async def async_get_data(self) -> Any:
        """Get endpoint statuses from the Gatus API."""
        return await self._api_wrapper(
            method="get",
            url=f"{self._url.rstrip('/')}/api/v1/endpoints/statuses",
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with asyncio.timeout(10):
                response = await self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except GatusApiClientError:
            # Already the right exception type — let it propagate as-is.
            raise
        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise GatusApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise GatusApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise GatusApiClientError(
                msg,
            ) from exception
