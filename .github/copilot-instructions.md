# Copilot Instructions

## Project Overview

This is a **Home Assistant custom integration** (HACS-compatible) for [Gatus](https://github.com/TwiN/gatus), a developer-oriented health check and monitoring tool. The integration polls a Gatus instance's API and exposes each monitored endpoint as a **binary sensor** with the `problem` device class in Home Assistant.

- **Repository**: `ullbergm/homeassistant-gatus`
- **Domain**: `gatus`
- **IoT class**: `local_polling` (polls every 60 seconds)
- **Platforms**: `binary_sensor`

## Architecture

### Integration Code (`custom_components/gatus/`)

| File | Purpose |
|---|---|
| `__init__.py` | Entry setup/unload; creates the coordinator, API client, and aiohttp session |
| `api.py` | `GatusApiClient` — wraps the Gatus REST API (`/api/v1/endpoints/statuses`) |
| `binary_sensor.py` | `GatusEndpointBinarySensor` — one entity per Gatus endpoint; device class `problem` (on = failing) |
| `config_flow.py` | `GatusFlowHandler` — UI config flow; accepts a single URL, tests connectivity, sets unique ID from slugified URL |
| `coordinator.py` | `GatusDataUpdateCoordinator` — standard HA `DataUpdateCoordinator`; fetches all endpoint statuses |
| `const.py` | Constants: `DOMAIN`, `LOGGER`, `ATTRIBUTION` |
| `data.py` | `GatusData` dataclass and `GatusConfigEntry` type alias for runtime data |
| `entity.py` | `GatusEntity` base class — sets device info, attribution, and `has_entity_name = True` |
| `manifest.json` | Integration manifest (domain, version, requirements, codeowners) |
| `translations/en.json` | UI strings for the config flow |

### Key Data Flow

1. User adds integration via UI → `config_flow.py` validates the Gatus URL
2. `__init__.py` creates an `aiohttp.ClientSession` (with `ThreadedResolver` for Python 3.13 compatibility), `GatusApiClient`, and `GatusDataUpdateCoordinator`
3. Coordinator calls `GET {url}/api/v1/endpoints/statuses` every 60 seconds
4. `binary_sensor.py` creates one `GatusEndpointBinarySensor` per endpoint in the response
5. Each sensor's `is_on` checks the latest result's `success` field (on = problem/failure)
6. Extra attributes: `endpoint_group`, `endpoint_name`, `hostname`, `status_code`, `duration_ms`, `timestamp`

### Supporting Files

| File | Purpose |
|---|---|
| `config/configuration.yaml` | Local dev HA config (debug logging for `custom_components.gatus`) |
| `scripts/setup` | Install Python dependencies (`requirements.txt`) |
| `scripts/develop` | Start a local HA instance with the integration loaded via `PYTHONPATH` |
| `scripts/lint` | Run `ruff format` + `ruff check --fix` locally |
| `hacs.json` | HACS metadata (name, minimum HA/HACS versions) |
| `requirements.txt` | Runtime deps: `pip`, `ruff`, `homeassistant` |
| `requirements_dev.txt` | Dev deps: adds `pre-commit`, `pylint`, `mypy` |

## Conventions

### Home Assistant Integration Patterns

- Follow the [HA developer docs](https://developers.home-assistant.io/) for all integration patterns
- Use `ConfigEntry.runtime_data` (typed via `GatusConfigEntry`) to store the API client, coordinator, and integration reference
- Use `DataUpdateCoordinator` for polling — never poll directly from entities
- All entities must inherit from `GatusEntity` (which inherits `CoordinatorEntity`)
- Use `has_entity_name = True` and set `_attr_name` for entity naming
- Handle `ConfigEntryAuthFailed` for auth errors and `UpdateFailed` for transient failures in the coordinator
- Close aiohttp sessions in `async_unload_entry`

### Python Style

- Format and lint with **Ruff** (enforced in CI and via `scripts/lint`)
- Use `from __future__ import annotations` in all files
- Use `TYPE_CHECKING` guards for imports only needed at type-check time
- Follow Home Assistant naming conventions: `async_setup_entry`, `async_unload_entry`, etc.

### Conventional Commits (strict)

PR titles **must** follow [Conventional Commits](https://www.conventionalcommits.org/) format, enforced by the `conventional-commits.yml` workflow using `amannn/action-semantic-pull-request`:

- Subject must start with a **lowercase** letter (regex: `^(?![A-Z]).+$`)
- No trailing period
- Scope is optional: `feat(api): add endpoint` or `feat: add endpoint`
- Breaking changes use `!` suffix: `feat!: redesign config`

Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

### Version Bumping

Versions are calculated by git-cliff from `.github/cliff.toml` — not from labels or manual input:

- `feat` → **minor** bump (`features_always_bump_minor = true`)
- `feat!` / `fix!` / any `!` → **major** bump (`breaking_always_bump_major = true`)
- Everything else → **patch** bump
- First version defaults to `v0.1.0`; tags are always `v`-prefixed
- The version in `manifest.json` should be kept in sync with releases

### Labels

Labels are defined in `.github/labels.yml` and auto-synced on push to `main`. When adding new labels, edit `labels.yml` — don't create them manually in GitHub.

## Key Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| `build.yml` | Push to `main`, PRs, daily schedule, manual | Runs pre-commit hooks, HACS validation (`hacs/action`), and hassfest (`home-assistant/actions/hassfest`) |
| `lint.yml` | Push to `main` or PR to `main` | Ruff check + format verification (Python 3.14) |
| `draft-release.yml` | Push to `main` | Generates changelog via git-cliff, deletes old drafts, creates a new draft release |
| `conventional-commits.yml` | PR open/edit/sync | Validates PR title format |
| `scorecard.yml` | Push to `main`, weekly, manual | OpenSSF Scorecard security analysis (public repos only) |
| `lighthouse.yml` | PR to `main` (docs/ changed), manual | Lighthouse audit on the docs site |
| `auto-assign.yml` | PR or issue opened | Auto-assigns author |
| `codeowners.yml` | Push to `main` (CODEOWNERS changed) + Monday cron | Validates CODEOWNERS syntax |
| `sync-labels.yml` | Push to `main` (labels.yml changed) | Syncs labels from `.github/labels.yml` |
| `stale.yml` | Daily cron (09:00 UTC) | Marks issues stale after 30d, PRs after 14d; closes after 7d more |
| `lock.yml` | Daily cron (09:00 UTC) | Locks closed issues after 30d, closed PRs after 7d |

### Stale Exemptions

Issues with labels `pinned`, `security`, `help wanted`, or `good first issue` are exempt. PRs with `pinned`, `security`, or `dependencies` are exempt.

## Development

### Local Setup

```bash
scripts/setup    # Install Python dependencies
scripts/develop  # Start HA with the integration loaded (debug mode)
scripts/lint     # Auto-format and fix lint issues
```

The `scripts/develop` script sets `PYTHONPATH` so `custom_components/gatus` is picked up without symlinks. HA config lives in `config/configuration.yaml` with debug logging enabled for the integration.

### Adding a New Platform

1. Create `custom_components/gatus/<platform>.py` (e.g., `sensor.py`)
2. Add the platform to `PLATFORMS` in `__init__.py`
3. Implement `async_setup_entry` to create entities from `coordinator.data`
4. Have entities inherit from `GatusEntity`
5. Add any new translation keys to `translations/en.json`

### Adding New Entity Attributes or Sensors

- The Gatus API response is a list of endpoint objects; each has `key`, `name`, `group`, and `results[]`
- Each result has `success`, `hostname`, `status`, `duration` (nanoseconds), `timestamp`, and other fields
- Entities look up their data via `_endpoint_key` in `coordinator.data`

### Modifying CI/CD

- **Adding a workflow**: Place in `.github/workflows/`, use minimal `permissions`, and prefer pinned action versions (`@v4` not `@main`)
- **Changing changelog format**: Edit `.github/cliff.toml` — the `commit_parsers` array maps commit prefixes to changelog sections with emoji headers
- **Editing labels**: Only edit `.github/labels.yml` — the sync workflow handles the rest