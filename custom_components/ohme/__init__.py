from homeassistant import core
from .const import *
from .api_client import OhmeApiClient
from .coordinator import OhmeUpdateCoordinator, OhmeStatisticsUpdateCoordinator


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Ohme EV Charger component."""
    return True


async def async_setup_dependencies(hass, config):
    """Instantiate client and refresh session"""
    client = OhmeApiClient(config['email'], config['password'])
    hass.data[DOMAIN][DATA_CLIENT] = client

    await client.async_refresh_session()
    await client.async_update_device_info()


async def async_setup_entry(hass, entry):
    """This is called from the config flow."""
    hass.data.setdefault(DOMAIN, {})
    config = dict(entry.data)

    if entry.options:
        config.update(entry.options)

    if "email" not in config:
        return False

    await async_setup_dependencies(hass, config)

    hass.data[DOMAIN][DATA_COORDINATOR] = OhmeUpdateCoordinator(hass=hass)
    await hass.data[DOMAIN][DATA_COORDINATOR].async_config_entry_first_refresh()

    hass.data[DOMAIN][DATA_STATISTICS_COORDINATOR] = OhmeStatisticsUpdateCoordinator(
        hass=hass)
    await hass.data[DOMAIN][DATA_STATISTICS_COORDINATOR].async_config_entry_first_refresh()

    # Create tasks for each entity type
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )

    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, ['binary_sensor', 'sensor', 'switch'])
