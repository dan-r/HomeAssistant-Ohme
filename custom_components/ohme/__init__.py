import logging
from homeassistant import core
from .const import *
from .api_client import OhmeApiClient
from .coordinator import OhmeChargeSessionsCoordinator, OhmeStatisticsCoordinator, OhmeAccountInfoCoordinator, OhmeAdvancedSettingsCoordinator, OhmeChargeSchedulesCoordinator
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Ohme EV Charger component."""
    return True


async def async_setup_dependencies(hass, config):
    """Instantiate client and refresh session"""
    client = OhmeApiClient(config['email'], config['password'])
    hass.data[DOMAIN][DATA_CLIENT] = client

    await client.async_create_session()
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

    coordinators = [
        OhmeChargeSessionsCoordinator(hass=hass),   # COORDINATOR_CHARGESESSIONS
        OhmeAccountInfoCoordinator(hass=hass),      # COORDINATOR_ACCOUNTINFO
        OhmeStatisticsCoordinator(hass=hass),       # COORDINATOR_STATISTICS
        OhmeAdvancedSettingsCoordinator(hass=hass), # COORDINATOR_ADVANCED
        OhmeChargeSchedulesCoordinator(hass=hass)   # COORDINATOR_SCHEDULES
    ]

    # We can function without these so setup can continue
    coordinators_optional = [
        OhmeStatisticsCoordinator,
        OhmeAdvancedSettingsCoordinator
    ]

    for coordinator in coordinators:
        # Catch failures if this is an 'optional' coordinator
        try:
            await coordinator.async_config_entry_first_refresh()
        except ConfigEntryNotReady as ex:
            allow_failure = False
            for optional in coordinators_optional:
                allow_failure = True if isinstance(coordinator, optional) else allow_failure

            if allow_failure:
                _LOGGER.error(f"{coordinator.__class__.__name__} failed to setup. This coordinator is optional so the integration will still function, but please raise an issue if this persists.")
            else:
                raise ex

    hass.data[DOMAIN][DATA_COORDINATORS] = coordinators

    # Create tasks for each entity type
    for entity_type in ENTITY_TYPES:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, entity_type)
        )

    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, ENTITY_TYPES)
