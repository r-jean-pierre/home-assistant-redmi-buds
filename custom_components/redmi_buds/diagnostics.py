"""Export an allowlist, never serial numbers, MACs, names or raw packets."""

from homeassistant.core import HomeAssistant

from . import BudsConfigEntry
from .const import CONF_CHANNEL, CONF_INTERVAL, DEFAULT_CHANNEL


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BudsConfigEntry
) -> dict:
    coordinator = entry.runtime_data
    snapshot = coordinator.data
    return {
        "address": "**REDACTED**",
        "serial_number": "**REDACTED**",
        "channel": entry.data.get(CONF_CHANNEL, DEFAULT_CHANNEL),
        "poll_interval_minutes": entry.options.get(CONF_INTERVAL, 0),
        "last_update_success": coordinator.last_update_success,
        "last_success": coordinator.last_success.isoformat()
        if coordinator.last_success
        else None,
        "last_error_type": type(coordinator.last_exception).__name__
        if coordinator.last_exception
        else None,
        "device": None
        if snapshot is None
        else {
            "vid": f"{snapshot.info.vid:04x}",
            "pid": f"{snapshot.info.pid:04x}",
            "firmware_raw": snapshot.info.firmware_raw,
            "firmware_version": snapshot.info.firmware_version,
            "firmware_version_source": "observed_signature_mapping"
            if snapshot.info.firmware_version
            else "unknown",
            "model_id": snapshot.info.model_id,
            "model_id_source": "vid_pid_mapping",
            "battery_raw": [cell.raw for cell in snapshot.info.batteries]
            if snapshot.info.batteries
            else None,
            "low_latency": snapshot.latency,
            "equalizer_code": snapshot.equalizer,
            "gestures": {
                str(key): list(value) for key, value in snapshot.gestures.items()
            },
        },
    }
