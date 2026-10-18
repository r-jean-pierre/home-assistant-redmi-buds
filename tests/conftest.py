from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockModule, mock_integration

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def local_bluetooth_backend(hass):
    # Native Bluetooth's hardware manager is outside this integration's tests.
    mock_integration(hass, MockModule("bluetooth"))
    with patch(
        "custom_components.redmi_buds.config_flow.async_list_paired_devices",
        AsyncMock(return_value=[]),
    ):
        yield
