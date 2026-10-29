# Changelog

## 0.1.2 — 2026-10-29

- Remove the duplicate read-only long-press sensors. View and change long-press
  actions through the configuration selects.
- Remove the retired sensor entries automatically when the integration loads.
  Dashboards and automations using those sensors must use the corresponding
  select entities instead.

## 0.1.1 — 2026-10-28

- Report failed readback after an accepted write as an unconfirmed write,
  including rejected read requests. Preserve unconfirmed-write errors when
  the write acknowledgement is lost.
- Document observed battery reporting in 10-percentage-point steps.

## 0.1.0 — 2026-10-19

- UI setup with paired-device selection and manual address entry.
- Battery levels and charging status for both earphones and the case.
- Low latency, audio balance and individual gesture settings.
- Manual or periodic refresh with the last successful read timestamp.
- Firmware version, model reference and serial number.
- English and French translations, diagnostics and automated tests.
