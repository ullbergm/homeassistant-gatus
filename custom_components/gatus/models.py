"""Typed data models for the Gatus integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GatusResult:
    """A single health-check result returned by the Gatus API."""

    success: bool
    hostname: str | None
    status_code: int | None
    duration_ns: int  # nanoseconds as returned by the API
    timestamp: str | None

    @property
    def duration_ms(self) -> float:
        """Return duration in milliseconds (converted from nanoseconds)."""
        return self.duration_ns / 1_000_000

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GatusResult:
        """Construct a GatusResult from a raw API response dict."""
        return cls(
            success=data.get("success", False),
            hostname=data.get("hostname"),
            status_code=data.get("status"),
            duration_ns=data.get("duration", 0),
            timestamp=data.get("timestamp"),
        )


@dataclass
class GatusEndpoint:
    """A monitored endpoint as returned by the Gatus API."""

    key: str
    name: str
    group: str
    results: list[GatusResult] = field(default_factory=list)

    @property
    def latest_result(self) -> GatusResult | None:
        """Return the most recent health-check result, or None if no results yet."""
        return self.results[-1] if self.results else None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GatusEndpoint:
        """Construct a GatusEndpoint from a raw API response dict."""
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            group=data.get("group", ""),
            results=[
                GatusResult.from_dict(r) for r in data.get("results", [])
            ],
        )
