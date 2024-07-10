import logging
from homeassistant import core
from .const import *
from .utils import get_option
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
    
    # Reload this instance
    await hass.config_entries.async_reload(entry.entry_id)


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

    coordinators_skipped = []

    # Skip statistics coordinator if we don't need it
    if not get_option(hass, "enable_accumulative_energy"):
        coordinators_skipped.append(OhmeStatisticsCoordinator)

    for coordinator in coordinators:
        # If we should skip this coordinator
        skip = False
        for skipped in coordinators_skipped:
            if isinstance(coordinator, skipped):
                skip = True
                break
        
        if skip:
            _LOGGER.debug(f"Skipping initial load of {coordinator.__class__.__name__}")
            continue

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

    # Setup entities
    await hass.config_entries.async_forward_entry_setups(entry, ENTITY_TYPES)

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
        new_data = config_entry.data

        config_entry.version = CONFIG_VERSION
        hass.config_entries.async_update_entry(config_entry, data=new_data)

        _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True
