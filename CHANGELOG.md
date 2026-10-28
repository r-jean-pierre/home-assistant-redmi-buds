# Changelog

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
