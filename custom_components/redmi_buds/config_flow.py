"""Choose a paired classic Bluetooth device, with a manual fallback."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_ADDRESS,
    CONF_CHANNEL,
    CONF_INTERVAL,
    DEFAULT_CHANNEL,
    DOMAIN,
    NAME,
)
from .mma import BudsClient, BudsError
from .mma.bluez import DiscoveryUnavailable, PairedDevice, async_list_paired_devices
from .mma.protocol import IncompatibleDevice, UnsupportedTransport


def normalize_address(value: str) -> str:
    address = value.strip().replace("-", ":").upper()
    if not re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", address):
        raise ValueError("Invalid Bluetooth MAC address")
    return address


def schema(address: str = "", channel: int = DEFAULT_CHANNEL) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_ADDRESS, default=address): str,
            vol.Required(CONF_CHANNEL, default=channel): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=30)
            ),
        }
    )


class BudsConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._paired_devices: dict[str, PairedDevice] | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BudsOptionsFlow()

    async def _validate(self, data: dict) -> str | None:
        client = BudsClient(data[CONF_ADDRESS], data[CONF_CHANNEL])
        try:
            await self.hass.async_add_executor_job(client.probe)
        except IncompatibleDevice:
            return "unsupported_device"
        except UnsupportedTransport:
            return "unsupported_transport"
        except BudsError:
            return "cannot_connect"
        finally:
            await self.hass.async_add_executor_job(client.close)
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # Handle address submissions from the manual setup form.
        if user_input is not None and CONF_ADDRESS in user_input:
            return await self.async_step_manual(user_input)
        if self._paired_devices is None:
            try:
                paired = await async_list_paired_devices()
            except DiscoveryUnavailable:
                return await self.async_step_manual(
                    discovery_error="cannot_list_devices"
                )
            configured = {entry.unique_id for entry in self._async_current_entries()}
            self._paired_devices = {
                item.address: item for item in paired if item.address not in configured
            }
        if not self._paired_devices:
            return await self.async_step_manual()

        errors = {}
        if user_input is not None:
            if user_input.get("manual_entry"):
                return await self.async_step_manual()
            if (address := user_input.get("device")) in self._paired_devices:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                data = {CONF_ADDRESS: address, CONF_CHANNEL: DEFAULT_CHANNEL}
                if error := await self._validate(data):
                    errors["base"] = error
                else:
                    return self.async_create_entry(title=NAME, data=data)
            else:
                errors["device"] = "select_device"

        devices = self._paired_devices
        likely = [item.address for item in devices.values() if item.likely_model]
        default = (
            likely[0]
            if len(likely) == 1
            else next(iter(devices))
            if len(devices) == 1
            else None
        )
        marker = (
            vol.Optional("device", default=default)
            if default
            else vol.Optional("device")
        )
        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    marker: vol.In(
                        {
                            item.address: f"{item.name} (…:{item.address[-5:]})"
                            for item in devices.values()
                        }
                    ),
                    vol.Optional("manual_entry", default=False): bool,
                }
            ),
        )

    async def async_step_manual(
        self,
        user_input: dict[str, Any] | None = None,
        *,
        discovery_error: str | None = None,
    ) -> ConfigFlowResult:
        errors = {}
        if discovery_error:
            errors["base"] = discovery_error
        if user_input is not None:
            try:
                data = {
                    CONF_ADDRESS: normalize_address(user_input[CONF_ADDRESS]),
                    CONF_CHANNEL: user_input[CONF_CHANNEL],
                }
            except ValueError:
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(data[CONF_ADDRESS])
                self._abort_if_unique_id_configured()
                if error := await self._validate(data):
                    errors["base"] = error
                else:
                    return self.async_create_entry(title=NAME, data=data)
        return self.async_show_form(
            step_id="manual", data_schema=schema(), errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            try:
                address = normalize_address(user_input[CONF_ADDRESS])
            except ValueError:
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                # Changing the address requires a separate config entry.
                if address != entry.data[CONF_ADDRESS]:
                    errors[CONF_ADDRESS] = "different_device"
                else:
                    data = {
                        CONF_ADDRESS: address,
                        CONF_CHANNEL: user_input[CONF_CHANNEL],
                    }
                    if error := await self._validate(data):
                        errors["base"] = error
                    else:
                        return self.async_update_reload_and_abort(
                            entry, data_updates=data
                        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema(
                entry.data[CONF_ADDRESS], entry.data.get(CONF_CHANNEL, DEFAULT_CHANNEL)
            ),
            errors=errors,
        )


class BudsOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            minutes = user_input[CONF_INTERVAL]
            if minutes == 0 or (5 <= minutes <= 1440 and minutes == int(minutes)):
                return self.async_create_entry(
                    title="", data={CONF_INTERVAL: int(minutes)}
                )
            errors[CONF_INTERVAL] = "invalid_interval"
        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INTERVAL,
                        default=self.config_entry.options.get(CONF_INTERVAL, 0),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=1440,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="min",
                        )
                    ),
                }
            ),
        )
