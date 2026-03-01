"""Constants for gatus."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "gatus"
ATTRIBUTION = "Data provided by Gatus"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 60  # seconds
