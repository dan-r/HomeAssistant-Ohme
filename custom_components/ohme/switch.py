from __future__ import annotations
import logging
import asyncio

from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import generate_entity_id

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity
)
from homeassistant.components.switch import SwitchEntity
from homeassistant.util.dt import (utcnow)

from .const import DOMAIN, DATA_CLIENT, DATA_COORDINATORS, COORDINATOR_CHARGESESSIONS, COORDINATOR_ACCOUNTINFO
from .coordinator import OhmeChargeSessionsCoordinator, OhmeAccountInfoCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities
):
    """Setup switches and configure coordinator."""
    coordinators = hass.data[DOMAIN][DATA_COORDINATORS]

    coordinator = coordinators[COORDINATOR_CHARGESESSIONS]
    accountinfo_coordinator = coordinators[COORDINATOR_ACCOUNTINFO]
    client = hass.data[DOMAIN][DATA_CLIENT]

    switches = [OhmePauseChargeSwitch(coordinator, hass, client),
                OhmeMaxChargeSwitch(coordinator, hass, client)]

    if client.is_capable("buttonsLockable"):
        switches.append(
            OhmeConfigurationSwitch(
                accountinfo_coordinator, hass, client, "Lock Buttons", "lock", "buttonsLocked")
        )
    if client.is_capable("pluginsRequireApprovalMode"):
        switches.append(
            OhmeConfigurationSwitch(accountinfo_coordinator, hass, client,
                                    "Require Approval", "check-decagram", "pluginsRequireApproval")
        )
    if client.is_capable("stealth"):
        switches.append(
            OhmeConfigurationSwitch(accountinfo_coordinator, hass, client,
                                    "Sleep When Inactive", "power-sleep", "stealthEnabled")
        )

    async_add_entities(switches, update_before_add=True)


class OhmePauseChargeSwitch(CoordinatorEntity[OhmeChargeSessionsCoordinator], SwitchEntity):
    """Switch for pausing a charge."""
    _attr_name = "Pause Charge"

    def __init__(self, coordinator, hass: HomeAssistant, client):
        super().__init__(coordinator=coordinator)

        self._client = client

        self._state = False
        self._last_updated = None
        self._attributes = {}

        self.entity_id = generate_entity_id(
            "switch.{}", "ohme_pause_charge", hass=hass)

        self._attr_device_info = client.get_device_info()

    @property
    def unique_id(self):
        """The unique ID of the switch."""
        return self._client.get_unique_id("pause_charge")

    @property
    def icon(self):
        """Icon of the switch."""
        return "mdi:pause"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Determine if charge is paused.
           We handle this differently to the sensors as the state of this switch
           is evaluated only when new data is fetched to stop the switch flicking back then forth."""
        if self.coordinator.data is None:
            self._attr_is_on = False
        else:
            self._attr_is_on = bool(self.coordinator.data["mode"] == "STOPPED")

        self._last_updated = utcnow()

        self.async_write_ha_state()

    async def async_turn_on(self):
        """Turn on the switch."""
        await self._client.async_pause_charge()

        await asyncio.sleep(1)
        await self.coordinator.async_refresh()

    async def async_turn_off(self):
        """Turn off the switch."""
        await self._client.async_resume_charge()

        await asyncio.sleep(1)
        await self.coordinator.async_refresh()


class OhmeMaxChargeSwitch(CoordinatorEntity[OhmeChargeSessionsCoordinator], SwitchEntity):
    """Switch for pausing a charge."""
    _attr_name = "Max Charge"

    def __init__(self, coordinator, hass: HomeAssistant, client):
        super().__init__(coordinator=coordinator)

        self._client = client

        self._state = False
        self._last_updated = None
        self._attributes = {}

        self.entity_id = generate_entity_id(
            "switch.{}", "ohme_max_charge", hass=hass)

        self._attr_device_info = client.get_device_info()

    @property
    def unique_id(self):
        """The unique ID of the switch."""
        return self._client.get_unique_id("max_charge")

    @property
    def icon(self):
        """Icon of the switch."""
        return "mdi:battery-arrow-up"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Determine if we are max charging."""
        if self.coordinator.data is None:
            self._attr_is_on = False
        else:
            self._attr_is_on = bool(
                self.coordinator.data["mode"] == "MAX_CHARGE")

        self._last_updated = utcnow()

        self.async_write_ha_state()

    async def async_turn_on(self):
        """Turn on the switch."""
        await self._client.async_max_charge()

        # Not very graceful but wait here to avoid the mode coming back as 'CALCULATING'
        # It would be nice to simply ignore this state in future and try again after x seconds.
        await asyncio.sleep(1)
        await self.coordinator.async_refresh()

    async def async_turn_off(self):
        """Turn off the switch."""
        await self._client.async_stop_max_charge()

        await asyncio.sleep(1)
        await self.coordinator.async_refresh()


class OhmeConfigurationSwitch(CoordinatorEntity[OhmeAccountInfoCoordinator], SwitchEntity):
    """Switch for changing configuration options."""

    def __init__(self, coordinator, hass: HomeAssistant, client, name, icon, config_key):
        super().__init__(coordinator=coordinator)

        self._client = client

        self._state = False
        self._last_updated = None
        self._attributes = {}

        self._icon = icon
        self._attr_name = name
        self._config_key = config_key
        self.entity_id = generate_entity_id(
            "switch.{}", "ohme_" + name.lower().replace(' ', '_'), hass=hass)

        self._attr_device_info = client.get_device_info()

    @property
    def unique_id(self):
        """The unique ID of the switch."""
        return self._client.get_unique_id(self._config_key)

    @property
    def icon(self):
        """Icon of the switch."""
        return f"mdi:{self._icon}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Determine configuration value."""
        if self.coordinator.data is None:
            self._attr_is_on = None
        else:
            settings = self.coordinator.data["chargeDevices"][0]["optionalSettings"]
            self._attr_is_on = bool(settings[self._config_key])

        self._last_updated = utcnow()

        self.async_write_ha_state()

    async def async_turn_on(self):
        """Turn on the switch."""
        await self._client.async_set_configuration_value({self._config_key: True})

        await asyncio.sleep(1)
        await self.coordinator.async_refresh()

    async def async_turn_off(self):
        """Turn off the switch."""
        await self._client.async_set_configuration_value({self._config_key: False})

        await asyncio.sleep(1)
        await self.coordinator.async_refresh()
