# Usage and troubleshooting

## Pair the earphones

Pair the earphones with Home Assistant’s local Bluetooth controller before
adding the integration. Pairing them with a phone alone is not sufficient.
Keep an existing Home Assistant pairing.

If your installation provides `bluetoothctl`, run it from a terminal with
access to that controller:

```bash
bluetoothctl
```

Open the case and put the earphones into pairing mode according to their
manual. In the interactive prompt, scan for the device and replace the example
address below with its Bluetooth address:

```text
power on
agent on
default-agent
scan on
pair AA:BB:CC:DD:EE:01
trust AA:BB:CC:DD:EE:01
scan off
quit
```

## Add the integration

Go to **Settings → Devices & services → Add integration → Redmi Buds 6 Play**.
Choose the earphones from the paired devices list. Reopen the form after a
new pairing to refresh the list.

Manual address entry is available if the list is empty or unavailable.
The default RFCOMM channel is **6**. The integration checks the product
identifier when connecting; a matching Bluetooth name alone is not sufficient.

## Read measurements

Press **Refresh** on the device page to read batteries, charging status and
settings. Battery levels are percentages; charging entities are on/off indicators.
Their icons distinguish charging, not charging and unknown states.

Values reflect the last read. A failed read makes measurements unavailable
while retaining **Last successful read**. Wake the earphones and refresh again.
Manual mode does not restore measurements after a Home Assistant restart.

**Firmware version** and **Serial number** sensors are disabled by default.
Enable them in the device’s entity list if needed. Unrecognized firmware
signatures are displayed as raw bytes.

## Automatic refresh

Open the integration options from **Settings → Devices & services**.

| Interval | Behavior |
| --- | --- |
| `0` | Manual refresh |
| `5`–`1440` | Refresh interval in minutes |

Enabling an interval starts a read. In manual mode, use **Refresh** after
startup. Reads can interfere with the phone’s Bluetooth connection.

## Gesture settings

Use the selects in the device’s **Configuration** section.

| Gesture | Left | Right |
| --- | --- | --- |
| Single | Tap left earphone once | Tap right earphone once |
| Double | Double tap left earphone | Double tap right earphone |
| Triple | Triple tap left earphone | Triple tap right earphone |
| Hold | Press and hold left earphone | Press and hold right earphone |

Single, double and triple taps offer **None**, **Play/Pause**, **Volume up**,
**Volume down**, **Previous song**, **Next song** and **Take photo**.
Press and hold offers **None**, **Voice assistant** and **Take photo**.
The long-press sensors under **Diagnostic** are read-only; use the
configuration selects to change their values.

After a change, the integration reads all settings again. Some actions,
particularly **Take photo**, may also affect another gesture. According to
Xiaomi Earbuds, the photo feature requires a compatible Xiaomi HyperOS phone
and is unavailable with dual connection.

If a write returns an error, **refresh before trying again**. The setting
may have changed even if its confirmation was not received.

## Audio settings

**Audio balance** offers Balanced sound, Enhance Voice, Enhance Bass,
Enhance Treble and Boost Volume. **Low latency** turns low latency on or off.
The integration displays the settings read back from the earphones.

## Connection problems

- Check that Home Assistant can access a local Bluetooth classic adapter.
- Open the case, wake the earphones and move them closer to the adapter.
- Temporarily disconnect the phone and close other earphone clients.
- Check pairing with Home Assistant’s controller, then refresh.

If the phone cannot resume audio, disconnect the earphones from Home
Assistant’s controller using a terminal with access to it:

```bash
bluetoothctl disconnect AA:BB:CC:DD:EE:01
```

Replace the example address. This disconnects the device’s profiles on that
controller without removing the pairing. The integration does not run this
command automatically. Use manual refresh if polling disrupts audio.

## Report a problem

Use the repository’s bug report form. Include Home Assistant and integration
versions, installation type, Bluetooth adapter, the error message and steps
to reproduce the problem. Integration diagnostics omit Bluetooth addresses and
serial numbers. Review other logs and screenshots before sharing them.
For vulnerabilities, follow [SECURITY.md](SECURITY.md).
