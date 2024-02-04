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


async def async_setup_dependencies(hass, entry):
    """Instantiate client and refresh session"""
    client = OhmeApiClient(entry.data['email'], entry.data['password'])
    hass.data[DOMAIN][DATA_CLIENT] = client

    hass.data[DOMAIN][DATA_OPTIONS] = entry.options

    await client.async_create_session()
    await client.async_update_device_info()


async def async_update_listener(hass, entry):
    """Handle options flow credentials update."""
    # Re-instantiate the API client
    await async_setup_dependencies(hass, entry)

    # Refresh all coordinators for good measure
    for coordinator in hass.data[DOMAIN][DATA_COORDINATORS]:
        await coordinator.async_refresh()


async def async_setup_entry(hass, entry):
    """This is called from the config flow."""
    hass.data.setdefault(DOMAIN, {})

    await async_setup_dependencies(hass, entry)

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

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, ENTITY_TYPES)


async def async_migrate_entry(hass: core.HomeAssistant, config_entry) -> bool:
    """Migrate old entry."""
    # Version number has gone backwards
    if CONFIG_VERSION < config_entry.version:
        _LOGGER.error("Backwards migration not possible. Please update the integration.")
        return False
    
    # Version number has gone up
    if config_entry.version < CONFIG_VERSION:
        _LOGGER.debug("Migrating from version %s", config_entry.version)
        new_data = dict(config_entry.data)

        # 1 -> 2: Add serial to config
        if CONFIG_VERSION >= 2:
            client = OhmeApiClient(new_data['email'], new_data['password'])
            await client.async_create_session()
            
            chargers = await client.async_get_chargers()
            new_data['serial'] = chargers[0]

        config_entry.version = CONFIG_VERSION
        hass.config_entries.async_update_entry(config_entry, data=new_data)

        _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True
