"""Custom types for gatus_integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import GatusApiClient
    from .coordinator import GatusDataUpdateCoordinator


type GatusConfigEntry = ConfigEntry[GatusData]


@dataclass
class GatusData:
    """Data for the Gatus integration."""

    client: GatusApiClient
    coordinator: GatusDataUpdateCoordinator
    integration: Integration
