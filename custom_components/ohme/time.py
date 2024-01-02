from __future__ import annotations
import asyncio
import logging
from homeassistant.components.time import TimeEntity
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.core import callback, HomeAssistant
from .const import DOMAIN, DATA_CLIENT, DATA_COORDINATORS, COORDINATOR_CHARGESESSIONS, COORDINATOR_SCHEDULES
from datetime import time as dt_time

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities
):
    """Setup switches and configure coordinator."""
    coordinators = hass.data[DOMAIN][DATA_COORDINATORS]

    client = hass.data[DOMAIN][DATA_CLIENT]

    numbers = [TargetTime(coordinators[COORDINATOR_CHARGESESSIONS],
                          coordinators[COORDINATOR_SCHEDULES], hass, client)]

    async_add_entities(numbers, update_before_add=True)


class TargetTime(TimeEntity):
    """Target time sensor."""
    _attr_name = "Target Time"

    def __init__(self, coordinator, coordinator_schedules, hass: HomeAssistant, client):
        self.coordinator = coordinator
        self.coordinator_schedules = coordinator_schedules

        self._client = client

        self._state = None
        self._last_updated = None
        self._attributes = {}

        self.entity_id = generate_entity_id(
            "number.{}", "ohme_target_time", hass=hass)

        self._attr_device_info = client.get_device_info()

    @property
    def unique_id(self):
        """The unique ID of the switch."""
        return self._client.get_unique_id("target_time")

    async def async_set_value(self, value: dt_time) -> None:
        """Update the current value."""
        # If disconnected, update top rule. If not, apply rule to current session
        if self.coordinator.data and self.coordinator.data['mode'] == "DISCONNECTED":
            await self._client.async_update_schedule(target_time=(int(value.hour), int(value.minute)))
            await asyncio.sleep(1)
            await self.coordinator_schedules.async_refresh()
        else:
            await self._client.async_apply_charge_rule(target_time=(int(value.hour), int(value.minute)))
            await asyncio.sleep(1)
            await self.coordinator.async_refresh()

        

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:alarm-check"

    @property
    def native_value(self):
        """Get value from data returned from API by coordinator"""
        # If we are not pending approval or disconnected, return in progress charge rule
        target = None
        if self.coordinator.data and self.coordinator.data['appliedRule'] and self.coordinator.data['mode'] != "PENDING_APPROVAL" and self.coordinator.data['mode'] != "DISCONNECTED":
            target = self.coordinator.data['appliedRule']['targetTime']
        elif self.coordinator_schedules.data:
            target = self.coordinator_schedules.data['targetTime']
        
        if target:
            self._state = dt_time(
                hour=target // 3600,
                minute=(target % 3600) // 60,
                second=0
            )
        return self._state
