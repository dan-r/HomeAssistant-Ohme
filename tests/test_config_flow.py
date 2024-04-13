"""Tests for the config flow."""
from unittest import mock
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ohme import config_flow
from homeassistant.helpers import config_entry_flow

async def test_step_account(hass):
    """Test the initialization of the form in the first step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )
    
    expected =  {
            'type': 'form',
            'flow_id': mock.ANY,
            'handler': 'ohme',
            'step_id': 'user',
            'data_schema': config_flow.USER_SCHEMA,
            'errors': {},
            'description_placeholders': None,
            'last_step': None,
            'preview': None
    }

    assert expected == result

async def test_options_flow(hass):
    """Test the options flow."""
    entry = MockConfigEntry(domain=config_flow.DOMAIN)
    entry.add_to_hass(hass)

    flow = config_flow.OhmeOptionsFlow(entry)
    result = await config_entry_flow.async_init(
        hass, flow, context={"source": "test"}, data={}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert result["data_schema"] is not None

    result = await config_entry_flow.async_configure(
        hass,
        flow,
        result["step_id"],
        {
            "email": "test@example.com",
            "password": "password123",
            "never_session_specific": True,
            "enable_accumulative_energy": False,
        },
    )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        "never_session_specific": True,
        "enable_accumulative_energy": False,
    }