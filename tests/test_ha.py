"""Home Assistant integration tests with a simulated Bluetooth backend."""

import asyncio
import json
import threading
from dataclasses import replace
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import probatio
import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.redmi_buds.mma.bluez import DiscoveryUnavailable, PairedDevice
from custom_components.redmi_buds.mma.client import BudsClient
from custom_components.redmi_buds.mma.protocol import (
    ConnectionError,
    IncompatibleDevice,
)

from .support import ADDRESS, FakeSocket

DOMAIN = "redmi_buds"


@pytest.fixture
def snapshot():
    return BudsClient(ADDRESS, socket_factory=FakeSocket).read()


@pytest.fixture
def client(snapshot):
    client = MagicMock()
    client.read.return_value = snapshot
    client.probe.return_value = snapshot.info
    client.set_config.return_value = snapshot
    client.set_gesture.return_value = snapshot
    return client


async def setup(hass, client, options=None):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ADDRESS,
        title="Redmi Buds 6 Play",
        data={"address": ADDRESS, "channel": 6},
        options=options or {},
    )
    entry.add_to_hass(hass)
    with patch("custom_components.redmi_buds.BudsClient", return_value=client):
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def eid(hass, platform, key):
    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{ADDRESS}_{key}")


async def test_setup_manual_refresh_entities_and_unload(hass, client):
    entry = await setup(hass, client)
    client.read.assert_not_called()
    assert hass.states.get(eid(hass, "sensor", "battery_left")).state == "unavailable"
    assert hass.states.get(eid(hass, "button", "refresh")).state != "unavailable"
    await hass.services.async_call(
        "button", "press", {"entity_id": eid(hass, "button", "refresh")}, blocking=True
    )
    assert hass.states.get(eid(hass, "sensor", "battery_left")).state == "100"
    assert hass.states.get(eid(hass, "binary_sensor", "charging_case")).state == "off"
    assert hass.states.get(eid(hass, "switch", "low_latency")).state == "on"
    assert hass.states.get(eid(hass, "select", "equalizer")).state == "bass"
    assert (
        hass.states.get(eid(hass, "sensor", "gesture_long_right")).state == "take_photo"
    )
    assert await hass.config_entries.async_unload(entry.entry_id)
    client.close.assert_called_once()


async def test_offline_refresh_preserves_timestamp_marks_states_unavailable(
    hass, client
):
    entry = await setup(hass, client)
    coordinator = entry.runtime_data
    await coordinator.async_refresh()
    timestamp = hass.states.get(eid(hass, "sensor", "last_read")).state
    client.read.side_effect = ConnectionError("offline")
    await coordinator.async_refresh()
    assert hass.states.get(eid(hass, "sensor", "battery_left")).state == "unavailable"
    assert hass.states.get(eid(hass, "sensor", "last_read")).state == timestamp
    assert hass.states.get(eid(hass, "button", "refresh")).state != "unavailable"


async def test_all_tap_menus_and_new_actions_through_ha_services(hass, client):
    entry = await setup(hass, client)
    await entry.runtime_data.async_refresh()
    expected = {
        "none",
        "play_pause",
        "volume_up",
        "volume_down",
        "previous_track",
        "next_track",
        "take_photo",
    }
    for gesture in ("single", "double", "triple"):
        for side in ("left", "right"):
            state = hass.states.get(eid(hass, "select", f"gesture_{gesture}_{side}"))
            assert set(state.attributes["options"]) == expected

    def write_gesture(gesture, side, action):
        return BudsClient(ADDRESS, socket_factory=FakeSocket).set_gesture(
            gesture, side, action
        )

    client.set_gesture.side_effect = write_gesture
    for key, option in (
        ("gesture_single_left", "previous_track"),
        ("gesture_double_right", "none"),
        ("gesture_triple_left", "take_photo"),
    ):
        entity_id = eid(hass, "select", key)
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": entity_id, "option": option},
            blocking=True,
        )
        assert hass.states.get(entity_id).state == option


async def test_writes_publish_full_readback_and_mismatch(hass, client, snapshot):
    entry = await setup(hass, client)
    await entry.runtime_data.async_refresh()
    client.set_config.return_value = replace(snapshot, latency=False, equalizer=0)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": eid(hass, "switch", "low_latency")},
        blocking=True,
    )
    client.set_config.assert_called_with(0x2F, 0)
    assert hass.states.get(eid(hass, "select", "equalizer")).state == "balanced"
    with pytest.raises(HomeAssistantError, match="readback differs"):
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": eid(hass, "select", "equalizer"), "option": "voice"},
            blocking=True,
        )


async def test_long_press_controls_and_coupled_readback(hass, client, snapshot):
    gestures = {**snapshot.gestures, 4: (5, 4), 3: (0, 8)}
    client.read.return_value = replace(snapshot, gestures=gestures)
    entry = await setup(hass, client)
    await entry.runtime_data.async_refresh()
    for side in ("left", "right"):
        state = hass.states.get(eid(hass, "select", f"gesture_long_{side}"))
        assert state.attributes["options"] == ["none", "voice_assistant", "take_photo"]

    def write_long(gesture, side, action):
        sock = FakeSocket()
        sock.config[2] = bytes.fromhex("04 05 04 01 02 03 02 05 04 03 00 08")
        return BudsClient(ADDRESS, socket_factory=lambda: sock).set_gesture(
            gesture, side, action
        )

    client.set_gesture.side_effect = write_long
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": eid(hass, "select", "gesture_long_right"),
            "option": "take_photo",
        },
        blocking=True,
    )
    client.set_gesture.assert_called_once_with(3, 1, 9)
    assert (
        hass.states.get(eid(hass, "select", "gesture_long_right")).state == "take_photo"
    )
    assert (
        hass.states.get(eid(hass, "select", "gesture_single_right")).state
        == "take_photo"
    )
    # Diagnostic sensors and configuration selects share the same state.
    assert (
        hass.states.get(eid(hass, "sensor", "gesture_long_right")).state == "take_photo"
    )


async def test_io_does_not_block_event_loop_and_unload_interrupts(
    hass, client, snapshot
):
    started, release = threading.Event(), threading.Event()

    def blocking_read():
        started.set()
        if not release.wait(5):
            raise ConnectionError("test timed out")
        raise ConnectionError("stopped")

    # Use a regular function so the test harness runs it in the executor.
    client.read = blocking_read
    client.close = release.set
    entry = await setup(hass, client)
    task = asyncio.create_task(entry.runtime_data.async_refresh())
    # The event loop must remain responsive while the read is blocked.
    assert await hass.async_add_executor_job(started.wait, 2)
    assert not task.done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    await task
    assert release.is_set()


async def test_diagnostics_redacts_identifiers_and_preserves_raw_batteries(
    hass, client
):
    from custom_components.redmi_buds.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    entry = await setup(hass, client)
    await entry.runtime_data.async_refresh()
    result = await async_get_config_entry_diagnostics(hass, entry)
    serialized = json.dumps(result)
    assert ADDRESS not in serialized
    assert "TEST-SERIAL" not in serialized
    assert result["device"]["battery_raw"] == [228, 228, 100]


async def test_flow_validation_and_duplicate(hass, client):
    with patch(
        "custom_components.redmi_buds.config_flow.BudsClient", return_value=client
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] == "form"
        with patch("custom_components.redmi_buds.async_setup_entry", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"address": "aa-bb-cc-dd-ee-01", "channel": 6}
            )
            await hass.async_block_till_done()
        assert result["type"] == "create_entry"
        assert result["data"] == {"address": ADDRESS, "channel": 6}
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"address": ADDRESS, "channel": 6},
        )
        assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    "address,error", [("bad", "invalid_address"), (ADDRESS, "unsupported_device")]
)
async def test_flow_errors(hass, client, address, error):
    client.probe.side_effect = IncompatibleDevice("unsupported")
    with patch(
        "custom_components.redmi_buds.config_flow.BudsClient", return_value=client
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"address": address, "channel": 6},
        )
    assert error in result["errors"].values()


async def test_options_enable_periodic_refresh_and_reject_short_interval(hass, client):
    entry = await setup(hass, client)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"poll_interval_minutes": 1}
    )
    assert result["type"] == "form"
    assert result["errors"] == {"poll_interval_minutes": "invalid_interval"}
    with patch("custom_components.redmi_buds.BudsClient", return_value=client):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"poll_interval_minutes": 5}
        )
        await hass.async_block_till_done()
    assert result["type"] == "create_entry"
    assert entry.options["poll_interval_minutes"] == 5
    client.read.assert_called_once()


async def test_refresh_options_serialize_to_a_visible_number_input(hass, client):
    entry = await setup(hass, client)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    # Check the form schema as serialized for the frontend.
    fields = probatio.to_field_list(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )
    field = next(item for item in fields if item["name"] == "poll_interval_minutes")
    assert field["default"] == 0
    number = field["selector"]["number"]
    assert number["mode"] == "box"
    assert number["min"] == 0
    assert number["max"] == 1440
    assert number["step"] == 1


async def test_firmware_sensor_and_device_metadata_clear_unknown_version(
    hass, client, snapshot
):
    with patch(
        "custom_components.redmi_buds.sensor.FirmwareSensor._attr_entity_registry_enabled_default",
        True,
    ):
        entry = await setup(hass, client)
    await entry.runtime_data.async_refresh()
    entity_id = eid(hass, "sensor", "firmware_raw")
    state = hass.states.get(entity_id)
    assert state.state == "2.0.2.2"
    assert state.attributes["firmware_raw"] == "20222022"
    registry = dr.async_get(hass)
    device = registry.async_get_device_by_identifier((DOMAIN, ADDRESS), entry.entry_id)
    assert device.model_id == "M2420E1"
    assert device.sw_version == "2.0.2.2"

    client.read.return_value = replace(
        snapshot, info=replace(snapshot.info, firmware_raw="20232023")
    )
    await entry.runtime_data.async_refresh()
    state = hass.states.get(entity_id)
    assert state.state == "20232023"
    assert state.attributes["version_source"] == "raw_unknown_signature"
    assert registry.async_get(device.id).sw_version is None


async def test_periodic_polling_refreshes_without_button(hass, client, freezer):
    await setup(hass, client, {"poll_interval_minutes": 5})
    client.read.assert_called_once()
    freezer.tick(timedelta(minutes=6))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert client.read.call_count == 2


@pytest.mark.parametrize(
    "name,likely", [("Redmi Buds 6 Play", True), ("My headphones", False)]
)
async def test_pick_paired_device_without_entering_mac(hass, client, name, likely):
    with (
        patch(
            "custom_components.redmi_buds.config_flow.async_list_paired_devices",
            AsyncMock(return_value=[PairedDevice(ADDRESS, name, likely)]),
        ),
        patch(
            "custom_components.redmi_buds.config_flow.BudsClient", return_value=client
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["step_id"] == "user"
        # One candidate is preselected, no address or channel to type.
        assert result["data_schema"]({}) == {"device": ADDRESS, "manual_entry": False}
        client.probe.assert_not_called()
        with patch("custom_components.redmi_buds.async_setup_entry", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {}
            )
            await hass.async_block_till_done()
        assert result["type"] == "create_entry"
        assert result["data"] == {"address": ADDRESS, "channel": 6}
        client.probe.assert_called_once()


async def test_paired_name_is_not_accepted_without_product_validation(hass, client):
    client.probe.side_effect = IncompatibleDevice("unsupported product")
    with (
        patch(
            "custom_components.redmi_buds.config_flow.async_list_paired_devices",
            AsyncMock(return_value=[PairedDevice(ADDRESS, "Redmi Buds 6 Play", True)]),
        ),
        patch(
            "custom_components.redmi_buds.config_flow.BudsClient", return_value=client
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": ADDRESS}
        )
        assert result["errors"] == {"base": "unsupported_device"}
        assert result["type"] == "form"


@pytest.mark.parametrize("unavailable", [False, True])
async def test_paired_listing_empty_or_unavailable_falls_back_to_manual(
    hass, client, unavailable
):
    listing = (
        AsyncMock(side_effect=DiscoveryUnavailable("unavailable"))
        if unavailable
        else AsyncMock(return_value=[])
    )
    with (
        patch(
            "custom_components.redmi_buds.config_flow.async_list_paired_devices",
            listing,
        ),
        patch(
            "custom_components.redmi_buds.config_flow.BudsClient", return_value=client
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["step_id"] == "manual"
        if unavailable:
            assert result["errors"] == {"base": "cannot_list_devices"}
        with patch("custom_components.redmi_buds.async_setup_entry", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"address": ADDRESS, "channel": 6}
            )
            await hass.async_block_till_done()
        assert result["type"] == "create_entry"


async def test_manual_fallback_can_be_chosen_from_device_list(hass):
    with patch(
        "custom_components.redmi_buds.config_flow.async_list_paired_devices",
        AsyncMock(return_value=[PairedDevice(ADDRESS, "Redmi Buds 6 Play", True)]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"manual_entry": True}
        )
        assert result["step_id"] == "manual"


@pytest.mark.parametrize("fails", [False, True])
async def test_bluez_reader_uses_managed_objects_and_handles_failure(fails):
    from custom_components.redmi_buds.mma.bluez import async_list_paired_devices

    props = {"Paired": True, "Address": ADDRESS, "Name": "Redmi Buds 6 Play"}
    getter = (
        AsyncMock(side_effect=TimeoutError)
        if fails
        else AsyncMock(
            return_value={"/org/bluez/hci0/dev_1": {"org.bluez.Device1": props}}
        )
    )
    with patch("bluetooth_adapters.dbus.get_dbus_managed_objects", getter):
        if fails:
            with pytest.raises(DiscoveryUnavailable):
                await async_list_paired_devices()
        else:
            assert (await async_list_paired_devices())[0].address == ADDRESS
    getter.assert_awaited_once()
