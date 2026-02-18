# Gatus Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![hacs][hacsbadge]][hacs]

A Home Assistant custom integration for [Gatus](https://github.com/TwiN/gatus) - a health check and monitoring tool.

## Features

This integration connects to your Gatus instance and creates binary sensors for each monitored endpoint using the **Problem** device class. This means:
- **Off (OK)**: The endpoint is healthy and passing checks
- **On (Problem)**: The endpoint is failing or unreachable

### Binary Sensors

One sensor is created for each endpoint monitored by Gatus:

**Device Class**: `problem`
- **Off**: Service is healthy (check passed)
- **On**: Service has a problem (check failed)

**Attributes Available**:
- `endpoint_group`: The group name from Gatus (e.g., "media", "external")
- `endpoint_name`: The endpoint name from Gatus (e.g., "plex", "google")
- `hostname`: The hostname being monitored
- `status_code`: HTTP status code from the health check (e.g., 200, 404)
- `duration_ms`: Response time in milliseconds
- `timestamp`: ISO timestamp of the last health check

### Usage in Automations

Since these are **problem** sensors, they work by waiting for the to turn 'on' for alerting:

```yaml
# Example: Alert when a service has a problem
alias: ESP Connect down
description: Alert when ESP Connect service is unreachable
triggers:
  - trigger: state
    entity_id:
      - >-
        binary_sensor.home_automation_espconnect
    to:
      - "on"
conditions: []
actions:
  - action: notify.notify
    metadata: {}
    data:
      title: ESP Connect is down!
      message: >-
        Status code: {{
        state_attr('binary_sensor.home_automation_espconnect',
        'status_code') }}
mode: single
```

## Installation


## Installation instruction

### HACS

The easiest way to install this integration is with [HACS][hacs]. First, install [HACS][hacs-download] if you don't have it yet. In Home Assistant, go to `HACS -> Integrations`, click on `+ Explore & Download Repositories`, search for `Gatus`, and click download. After download, restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ullbergm&repository=homeassistant-gatus&category=integration)

Once the integration is installed, you can add it to the Home Assistant by going to `Configuration -> Devices & Services`, clicking `+ Add Integration` and searching for `Gatus` or, using My Home Assistant service, you can click on:

[![Add Gatus][add-integration-badge]][add-integration]

### Manual installation

1. Copy the `custom_components/gatus` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

### Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Gatus Integration"
4. Enter your Gatus URL (e.g., `https://gatus.example.com`)
5. The integration will automatically discover all endpoints from your Gatus instance

## Example Configuration

**Gatus URL**: `https://gatus.apps.openshift.ullberg.family`

This will create binary sensors like:
- `binary_sensor.adsb_dump978` - Shows "Problem" if ADSB dump978 is down
- `binary_sensor.external_google` - Shows "Problem" if Google is unreachable
- `binary_sensor.media_plex` - Shows "Problem" if Plex is down
- etc.

All sensors will show "OK" when services are healthy and "Problem" when they fail health checks.

## Update Frequency

The integration polls Gatus every minute to update the status of all endpoints.

## Development

This integration was built using the Home Assistant integration blueprint.

### Development Setup

1. Open this repository in Visual Studio Code devcontainer
2. Run `./scripts/develop` to start Home Assistant for testing

## License

See [LICENSE](LICENSE) file for details.

## Notice

Gatus and other names are trademarks of their respective owners.

[add-integration]: https://my.home-assistant.io/redirect/config_flow_start?domain=gatus
[add-integration-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[hacs]: https://hacs.xyz
[hacs-download]: https://hacs.xyz/docs/setup/download
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-blue.svg?style=flat
[ha-logs]: https://my.home-assistant.io/redirect/logs
[ha-logs-badge]: https://my.home-assistant.io/badges/logs.svg
[ha-service]: https://my.home-assistant.io/redirect/developer_call_service/?service=logger.set_level
[ha-service-badge]: https://my.home-assistant.io/badges/developer_call_service.svg
[releases-shield]: https://img.shields.io/github/release/ullbergm/homeassistant-gatus.svg?style=flat
[releases]: https://github.com/ullbergm/homeassistant-gatus/releases
