## PUK Rumia Trash Pickup (Home Assistant)

Simple custom Home Assistant integration for tracking local waste pickup dates from the SISMS API.

### Repository layout

This repository uses a flat layout for HACS, configured with `content_in_root: true` in `hacs.json`.

### Features

- Configurable `unitId` through the Home Assistant config flow.
- Shared `DataUpdateCoordinator` refresh every 6 hours.
- One `SensorEntity` per waste bin type returned by the API.
- Each sensor uses `SensorDeviceClass.DATE`.
- Incoming ISO 8601 strings are parsed into native Python `date` objects.
- Persistent Home Assistant notification is raised whenever API update fails.

### Installation (HACS)

1. Add this repository as a custom HACS integration repository.
2. Install the integration.
3. Restart Home Assistant.
4. Add integration `PUK Rumia Trash Pickup` from Settings -> Devices & Services.
5. Enter your `unitId`.

### How to find unitId

1. Open `https://eko.rumia.eu/p/harmonogram-wywozu`.
2. Select your address.
3. Open browser Developer Tools.
4. Go to the Network tab.
5. Refresh the page.
6. Find a request to `gateway.sisms.pl` and copy the `unitId` query parameter value.

### Sensors

- The integration creates one date sensor per bin returned by the bins API.
- Sensor value is the next upcoming pickup date for that bin.
- Extra attributes include `bin_id`, `waste_type`, and `color`.

### API endpoints used

- `https://gateway.sisms.pl/akun/api/owners/44/bins/list?unitId=<UNIT_ID>`
- `https://gateway.sisms.pl/akun/api/owners/44/timetable/get?unitId=<UNIT_ID>`

### Local tests

Tests are intentionally minimal and cover:

- Date and payload parsing logic.
- Basic config flow entry creation behavior.
- Basic sensor state mapping from coordinator data.

HTTP request execution is intentionally not tested.

Run tests:

```bash
uv run pytest tests
```

Run dependency sync:

```bash
uv sync
```
