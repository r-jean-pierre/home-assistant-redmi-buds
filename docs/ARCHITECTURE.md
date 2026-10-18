# Architecture

## Components

| Module | Responsibility |
| --- | --- |
| `mma/` | Protocol codec, data models, BlueZ discovery and RFCOMM client |
| `config_flow.py` | Device selection, manual setup, model verification and options |
| `coordinator.py` | Shared reads and writes, scheduling and executor calls |
| `entity.py` | Device identity and availability |
| `sensor.py` | Batteries, read-only gestures, timestamps and device information |
| `binary_sensor.py` | Charging status |
| `switch.py` | Low latency |
| `select.py` | Audio balance and gesture settings |
| `button.py` | Manual refresh |
| `diagnostics.py` | Diagnostic export |

## Transactions

The synchronous transport uses the Python standard library and runs in Home
Assistant’s executor. A thread lock protects client transactions, and an
asyncio lock serializes coordinator operations. Each transaction owns one
socket, closed on completion or error. Unloading closes the active socket
and waits for its operation to finish.

Connection timeout is 15 seconds, response timeout is 5 seconds and the
exchange session has a 30-second deadline. Writes are not retried automatically.
Gesture writes read the current configuration to preserve the other earphone,
then reread all settings to reflect changes involving more than one gesture.

## Frame parsing

The parser uses frame lengths, with a maximum body size of 1024 bytes. It
handles fragmented headers, partial frames and concatenated frames, and
resynchronizes after invalid lengths or terminators. Header and terminator
bytes inside a payload remain part of that payload.

Responses must match the pending opcode and sequence and have a successful
status. Notifications requesting a reply are acknowledged with response flags
`00`. Unsupported incoming requests receive status `FF`. Notifications do not
produce physical gesture events in Home Assistant.

## Paired device selection

`mma/bluez.py` reads BlueZ managed objects through
`bluetooth_adapters.dbus.get_dbus_managed_objects`, provided by Home Assistant’s
Bluetooth dependency. The read has a five-second timeout. Candidates must be
paired, unblocked devices with a valid public Bluetooth address. Aliases are
used for display, and addresses present on several controllers are deduplicated.

Names determine sorting and preselection. Product verification uses a VID/PID
read after setup submission. Already configured devices are excluded. Listing
candidates does not initiate pairing or a radio scan.

## Diagnostics

Diagnostic exports use an explicit field list. Bluetooth addresses, serial
numbers, free-form device names, complete frames and arbitrary exception
messages are excluded. Raw battery and firmware fields remain available
for troubleshooting.
