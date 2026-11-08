# Tests and validation

## Test environment

| CI job | Python | Home Assistant | Test harness |
| --- | --- | --- | --- |
| Minimum Home Assistant compatibility | 3.13 | 2026.1.0 | 0.13.305 |
| Tests and coverage | 3.14 | 2026.10.4 | 0.13.375 |

The same suite runs in both jobs. The recent job uses the versions pinned in
`requirements_test.txt` and measures branch coverage. Bluetooth sockets and
earphones are simulated; the minimum job does not verify a physical Bluetooth setup.

## Run checks

With Python 3.14, from the repository root:

```bash
python -m pip install -r requirements_test.txt
python -m pytest -q --cov=custom_components.redmi_buds --cov=mma --cov-report=term-missing
python -m ruff check .
python -m ruff format --check .
```

The standalone protocol, client and discovery tests also support Python 3.12+:

```bash
python3 -m unittest tests.test_protocol tests.test_client tests.test_discovery -v
```

## Coverage

- Frame encoding, parsing, fragmentation, concatenation and invalid data.
- Product checks, responses, notifications and timeouts.
- Connection cleanup and cancellation of active operations.
- Battery, charging, firmware and settings decoding.
- Gesture writes, opposite-side preservation and full readback.
- Rejected readback after an accepted write, lost write acknowledgements,
  connection errors, single write attempts and socket cleanup.
- Setup, paired-device selection, duplicate handling and manual fallback.
- Refresh options, scheduling, availability and timestamps.
- Entity states, translations and diagnostic privacy.
- Removal of legacy long-press sensors, including renamed or disabled entries,
  while preserving configuration selects and other devices.

JSON and YAML files and relative documentation links are checked during
packaging. The workflow includes Hassfest and HACS validation; neither has
been executed in this environment. HACS validation is skipped for private
repositories. A scheduled, non-blocking job checks the latest Home Assistant
test harness separately from the pinned test environment.

## Hardware validation

| Feature | Status |
| --- | --- |
| Connection and complete read | Confirmed on Redmi Buds 6 Play |
| Batteries, serial number and settings | Compared with Xiaomi Earbuds |
| Battery reporting resolution | Values observed in 10-percentage-point steps in Home Assistant and Xiaomi Earbuds; full-discharge encoding remains unverified |
| Charging | State transitions and closed-case behavior need further checks |
| Low latency | ON/OFF writes confirmed; persistence needs further checks |
| Audio profiles | Five profiles read; Balanced sound write confirmed |
| Single, double and triple taps | Writes confirmed; all combinations and opposite-side preservation need hardware checks |
| Press and hold | Read confirmed; direct writes need hardware validation |
| Photo action | Single/hold coupling observed; full rules are not established |
| Firmware | Known signature 20222022 maps to 2.0.2.2; other signatures remain raw |
| Phone coexistence | Bluetooth contention is possible; audio recovery and long-term stability need further checks |

Automated tests do not establish physical gesture behavior or phone audio
coexistence. See the [user guide](../DOCS.md) for setup and troubleshooting.
