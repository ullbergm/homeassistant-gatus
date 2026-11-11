# Gatus Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![hacs][hacsbadge]](https://hacs.xyz)

A Home Assistant custom integration for [Gatus](https://github.com/TwiN/gatus) - a health check and monitoring tool.

## Features

This integration connects to your Gatus instance and creates entities for each monitored endpoint, grouped under one device per Gatus server.

### Binary sensors

One binary sensor is created for each endpoint, using the **Problem** device class:

- **Off (OK)**: the endpoint is healthy and passing checks
- **On (Problem)**: the endpoint is failing its checks

Attributes:

- `endpoint_group`: the group name from Gatus (e.g. "media", "external")
- `endpoint_name`: the endpoint name from Gatus (e.g. "plex", "google")
- `hostname`: the hostname being monitored
- `status_code`: HTTP status code from the health check (e.g. 200, 404)
- `duration_ms`: response time in milliseconds
- `timestamp`: ISO timestamp of the last health check

`duration_ms` and `timestamp` change on every check, so they are not stored by the recorder. Use the response time sensor below if you want history.

### Response time sensors

Each endpoint also has a response time sensor (milliseconds) with long-term statistics. These are **disabled by default**; enable the ones you want under **Settings** → **Devices & Services** → **Gatus** → *entities*.

### Entity IDs

Entity IDs are built from the device name and the endpoint, so for a server at `https://gatus.example.com` you get IDs such as:

- `binary_sensor.gatus_gatus_example_com_external_google`
- `binary_sensor.gatus_gatus_example_com_media_plex`
- `sensor.gatus_gatus_example_com_media_plex_response_time`

Check the entity list for the exact IDs in your installation; you can rename them freely.

### Endpoints added or removed in Gatus

New endpoints are picked up automatically on the next poll. When an endpoint disappears from Gatus its entities stop being provided; they are not deleted automatically (so a Gatus restart never loses your customisations), but you can delete them from the entity list.

### Usage in automations

Since these are **problem** sensors, alert when one turns `on`:

```yaml
# Example: Alert when a service has a problem
alias: Plex down
description: Alert when the Plex health check fails
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.gatus_gatus_example_com_media_plex
    to:
      - "on"
conditions: []
actions:
  - action: notify.notify
    data:
      title: Plex is down!
      message: >-
        Status code: {{
        state_attr('binary_sensor.gatus_gatus_example_com_media_plex',
        'status_code') }}
mode: single
```

## Requirements

- Home Assistant 2025.2 or newer
- A Gatus instance whose API is reachable **without authentication**. Instances behind basic auth, OIDC or an authenticating proxy are not supported.

## Installation

### HACS

This repository is not in the HACS default store, so add it as a custom repository:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ullbergm&repository=homeassistant-gatus&category=integration)

Or manually: open **HACS**, choose **Custom repositories** from the menu, add `https://github.com/ullbergm/homeassistant-gatus` with type **Integration**, then download **Gatus** and restart Home Assistant.

### Manual installation

1. Download `gatus.zip` from the [latest release][releases] and extract it to `custom_components/gatus` in your Home Assistant configuration directory
2. Restart Home Assistant

## Configuration

[![Add Gatus][add-integration-badge]][add-integration]

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Gatus"
4. Enter your Gatus URL (e.g. `https://gatus.example.com`)
5. The integration discovers all endpoints from your Gatus instance

### Changing the URL

If your Gatus server moves, open the integration, choose **Reconfigure** from the menu and enter the new URL. Your entities and their customisations are kept.

### Polling interval

Gatus is polled every 60 seconds by default. To change this, open the integration and choose **Configure**; the interval can be set between 10 and 3600 seconds.

## Development

This integration was built using the Home Assistant integration blueprint.

1. Open this repository in a Visual Studio Code devcontainer
2. Run `./scripts/develop` to start Home Assistant for testing
3. Run `pytest` and `./scripts/lint` before opening a pull request

## License

See [LICENSE](LICENSE) file for details.

## Notice

Gatus and other names are trademarks of their respective owners.

[add-integration]: https://my.home-assistant.io/redirect/config_flow_start?domain=gatus
[add-integration-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-blue.svg?style=flat
[releases-shield]: https://img.shields.io/github/release/ullbergm/homeassistant-gatus.svg?style=flat
[releases]: https://github.com/ullbergm/homeassistant-gatus/releases
