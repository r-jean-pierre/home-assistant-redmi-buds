# Contributing

Bug reports and pull requests are welcome. Keep changes focused on Redmi Buds
6 Play and include steps to reproduce a problem. Use private reporting for
vulnerabilities as described in [SECURITY.md](SECURITY.md).

## Development

Use Python 3.14 and install the test dependencies:

```bash
python -m pip install -r requirements_test.txt
python -m pytest -q
```

Run lint and formatting checks:

```bash
python -m ruff check .
python -m ruff format --check .
```

Measure coverage:

```bash
python -m pytest --cov=custom_components.redmi_buds --cov=mma --cov-report=term-missing
```

Bluetooth is simulated in automated tests. Describe hardware checks separately,
including the earphone firmware, adapter and Home Assistant version. Use
synthetic addresses and serial numbers in fixtures.

## Changes

- Keep Bluetooth I/O in the executor and serialize reads and writes.
- Preserve entity identifiers and the opposite earphone’s gesture settings.
- Add tests for behavior changes and update documentation where needed.
- Keep English and French translation keys consistent.
- Use English for documentation, comments and issue reports when possible.
- Do not include personal device identifiers or credentials.

## Continuous integration

Pushes and pull requests run tests with coverage, Ruff and Hassfest. HACS
validation also runs for public repositories. A weekly, non-blocking job checks
compatibility with the latest Home Assistant test harness.

## Releases

Use Semantic Versioning. The release tag, such as `v0.1.0`, must match the
version in `custom_components/redmi_buds/manifest.json`. Update the changelog
before tagging a release. A publication-ready archive is not itself a release.
