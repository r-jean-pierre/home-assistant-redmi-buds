# Security policy

## Supported versions

Security fixes target the latest published release. Upgrade older installations
before checking whether a problem still occurs. Before the first release,
reports apply to the `main` branch.

## Reporting a vulnerability

Report vulnerabilities privately. Do not open a public issue or pull request
with exploit details.

Use **Security → Advisories → Report a vulnerability** on GitHub:

[Report a vulnerability](https://github.com/r-jean-pierre/home-assistant-redmi-buds/security/advisories/new)

If private reporting is unavailable, arrange a private contact with the
maintainer before sending technical details. Do not post an exploit in a
public issue to request contact.

Include:

- Integration and Home Assistant versions.
- Installation type and Bluetooth adapter.
- A description of the vulnerability and its impact.
- Prerequisites and steps to reproduce it.
- A minimal proof of concept, if available.

Remove passwords, tokens, Bluetooth addresses and serial numbers from logs
and screenshots. Do not send a full Home Assistant backup.

## Handling reports

The maintainer reviews reports and may request additional information.
Confirmed vulnerabilities are addressed with coordinated disclosure. Response
and fix times depend on severity and maintainer availability. Contributor
credit is provided with the reporter’s agreement.

## Scope

This policy covers this integration and its configuration files. Report issues
in Home Assistant, BlueZ or earphone firmware to their respective maintainers
or vendors. Use regular repository issues for connection failures, feature
requests and other problems without a security impact.
