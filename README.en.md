# Redmi Buds 6 Play for Home Assistant

![Redmi Buds 6 Play](custom_components/redmi_buds/brand/icon.png)

Custom integration to monitor batteries and configure **Redmi Buds 6 Play**
from Home Assistant. Direct Bluetooth connection, UI setup, and English and
French translations.

[Français](README.md) · [User guide (French)](DOCS.md)

## Features

- Battery levels and charging status for both earphones and the case.
- Low latency control and five audio profiles.
- Single, double, triple, and press-and-hold gesture settings for each earphone.
- Manual or periodic refresh and last successful read timestamp.
- Firmware version, model reference, and serial number.

Gesture settings configure the earphones’ actions. They do not produce
physical tap events for Home Assistant automations.

## Requirements

- Home Assistant on Linux with a local Bluetooth classic adapter accessible to Core.
- Redmi Buds 6 Play already paired with that adapter.

ESPHome BLE Bluetooth proxies cannot carry this connection. Only Redmi Buds 6
Play is supported. See [VALIDATION.md](docs/VALIDATION.md) for the test environment.

## Installation

1. Download and extract the project.
2. Copy `custom_components/redmi_buds` to `/config/custom_components/redmi_buds`.
3. Restart Home Assistant.
4. Open the case, wake the earphones, and temporarily disconnect the phone.
5. Go to **Settings → Devices & services → Add integration** and search for
   **Redmi Buds 6 Play**.
6. Select the earphones from the paired devices list.
7. Press **Refresh** on the device page.

Manual Bluetooth address entry is available if the earphones are missing from
the list. The integration verifies the model when connecting. Pairing and
troubleshooting instructions are available in the [French user guide](DOCS.md).

## Refreshing

Refreshing is **manual by default**. In the integration options, choose `0`
for manual mode or an interval of **5–1440 minutes**. Values represent the
last successful read.

A Home Assistant connection may interfere with phone audio. Choose a refresh
interval that suits your usage. After restarting in manual mode, press
**Refresh** to populate the values.

## Updating

Replace `/config/custom_components/redmi_buds` and restart Home Assistant.
Keep the existing integration entry; no new setup is required.

## Documentation

- [Usage and troubleshooting (French)](DOCS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Tests and validation limits](docs/VALIDATION.md)
- [Changelog](CHANGELOG.md)

Code licensed under [MIT](LICENSE). Third-party resource attributions are in
[NOTICE.md](NOTICE.md). This project is independent of Xiaomi.
