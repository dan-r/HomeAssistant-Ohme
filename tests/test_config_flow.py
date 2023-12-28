"""Tests for the config flow."""
from unittest import mock
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_PATH
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ohme import config_flow
from custom_components.ohme.const import DOMAIN

@pytest.mark.asyncio
async def test_step_account(hass):
    """Test the initialization of the form in the first step of the config flow."""
    # result = await hass.config_entries.flow.async_step_user(
    #     None
    # )

    assert expected == result
