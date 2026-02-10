# Gatus Integration for Home Assistant

A Home Assistant custom integration for [Gatus](https://github.com/TwiN/gatus) - a health check and monitoring tool.

## Features

This integration connects to your Gatus instance and creates binary sensors for each monitored endpoint. Each sensor shows whether the endpoint is up (on) or down (off) based on the latest health check results from Gatus.

### What gets created

- **Binary Sensors**: One sensor for each endpoint monitored by Gatus
  - **State**: On (up) or Off (down) based on the latest health check
  - **Attributes**:
    - Endpoint group
    - Endpoint name
    - Hostname
    - HTTP status code
    - Response duration (in milliseconds)
    - Last check timestamp

## Installation

### Manual Installation

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
- `binary_sensor.adsb_dump978` - ADSB dump978 endpoint
- `binary_sensor.external_google` - External Google endpoint
- `binary_sensor.media_plex` - Media Plex endpoint
- etc.

## Update Frequency

The integration polls Gatus every minute to update the status of all endpoints.

## Development

This integration was built using the Home Assistant integration blueprint.

### Development Setup

1. Open this repository in Visual Studio Code devcontainer
2. Run `./scripts/develop` to start Home Assistant for testing

## License

See [LICENSE](LICENSE) file for details.
